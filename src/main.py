"""Main entry point for YouTube Channel Analyzer"""

import tkinter as tk
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.gui.main_window import MainWindow
from src.utils.browser_manager import BrowserManager
from src.utils.youtube_auth import YouTubeAuthManager
from src.scrapers.youtube_scraper import YouTubeScraper
from src.scrapers.transcript_scraper import TranscriptScraper
from src.data.excel_handler import ExcelHandler
from src.data.models import ScrapingConfig
from src.exceptions.custom_exceptions import ScrapingError, BrowserError


class YouTubeChannelAnalyzer:
    """Main application class"""
    
    def __init__(self, gui_window: MainWindow):
        """Initialize analyzer"""
        self.gui = gui_window
        self.browser = None
        self.auth_manager = None
        self.youtube_scraper = None
        self.transcript_scraper = None
    
    def start_analysis(self, config: ScrapingConfig):
        """Start the analysis process"""
        try:
            # Initialize browser
            self.gui.log("Initializing browser...")
            self.gui.update_progress(5, "Initializing browser...")
            
            if self.gui.should_stop():
                return
            
            self.browser = BrowserManager(headless=False, page_load_timeout=config.page_load_timeout)
            
            # Initialize authentication manager
            self.auth_manager = YouTubeAuthManager(self.browser)
            
            # Check and ensure YouTube login
            self.gui.log("Checking YouTube login status...")
            self.gui.update_progress(8, "Checking YouTube login...")
            
            if self.gui.should_stop():
                return
            
            def show_login_message(title, message):
                """Show login message in GUI thread"""
                from tkinter import messagebox
                messagebox.showinfo(title, message)
            
            if not self.auth_manager.ensure_login(
                progress_callback=self._progress_callback,
                show_message_callback=lambda title, msg: self.gui.root.after(0, lambda t=title, m=msg: show_login_message(t, m))
            ):
                self.gui.log("Login failed or cancelled. Please log in and try again.")
                self.gui.root.after(0, lambda: self._show_error(
                    "Login Required", 
                    "Please log in to YouTube in the browser window and try again."
                ))
                return
            
            self.gui.log("YouTube login verified. Starting analysis...")
            self.gui.update_progress(10, "Login verified. Starting analysis...")
            
            if self.gui.should_stop():
                return
            
            self.youtube_scraper = YouTubeScraper(self.browser)
            self.transcript_scraper = TranscriptScraper(self.browser)
            
            # Scrape YouTube videos
            self.gui.log("Scraping YouTube videos...")
            self.gui.update_progress(10, "Scraping YouTube videos...")
            
            if self.gui.should_stop():
                return
            
            videos = self.youtube_scraper.scrape_videos(
                config,
                progress_callback=self._progress_callback
            )
            
            if not videos:
                self.gui.log("No videos found!")
                return
            
            self.gui.log(f"Found {len(videos)} videos")
            self.gui.update_progress(50, f"Found {len(videos)} videos. Getting transcripts...")
            
            if self.gui.should_stop():
                return
            
            # Get transcripts
            self.gui.log("Getting transcripts...")
            videos = self.transcript_scraper.add_transcripts_to_videos(
                videos,
                retry_attempts=config.retry_attempts,
                progress_callback=self._progress_callback
            )
            
            self.gui.log(f"Transcripts retrieved for {len(videos)} videos")
            self.gui.update_progress(90, "Saving to Excel...")
            
            if self.gui.should_stop():
                return
            
            # Save to Excel
            self.gui.log("Saving data to Excel...")
            excel_handler = ExcelHandler()
            
            # Get output directory (current directory by default)
            output_dir = os.getcwd()
            
            channel_name = videos[0].channel_name if videos else "Unknown_Channel"
            filepath = excel_handler.export_videos(videos, channel_name, output_dir)
            
            self.gui.log(f"Data saved to: {filepath}")
            self.gui.update_progress(100, "Analysis completed!")
            
            # Show success message
            self.gui.root.after(0, lambda: self._show_success_message(filepath))
            
        except BrowserError as e:
            error_msg = str(e)
            self.gui.log(f"Browser error: {error_msg}")
            self.gui.root.after(0, lambda msg=error_msg: self._show_error("Browser Error", msg))
        except ScrapingError as e:
            error_msg = str(e)
            self.gui.log(f"Scraping error: {error_msg}")
            self.gui.root.after(0, lambda msg=error_msg: self._show_error("Scraping Error", msg))
        except Exception as e:
            error_msg = str(e)
            self.gui.log(f"Unexpected error: {error_msg}")
            self.gui.root.after(0, lambda msg=error_msg: self._show_error("Error", msg))
        finally:
            # Cleanup
            if self.auth_manager:
                try:
                    self.auth_manager.cleanup()
                except:
                    pass
            if self.browser:
                try:
                    self.browser.close()
                except:
                    pass
    
    def _progress_callback(self, message: str):
        """Progress callback from scrapers"""
        if not self.gui.should_stop():
            self.gui.log(message)
            # Update progress based on message content
            if "video" in message.lower() and "/" in message:
                try:
                    # Try to extract progress from message like "Processing video 5/10"
                    parts = message.split()
                    for part in parts:
                        if "/" in part and part[0].isdigit():
                            current, total = map(int, part.split("/"))
                            progress = 10 + (current / total) * 40  # 10-50% for video scraping
                            self.gui.update_progress(progress, message)
                            return
                except:
                    pass
    
    def _show_success_message(self, filepath: str):
        """Show success message"""
        from tkinter import messagebox
        messagebox.showinfo(
            "Success",
            f"Analysis completed successfully!\n\nFile saved to:\n{filepath}"
        )
    
    def _show_error(self, title: str, message: str):
        """Show error message"""
        from tkinter import messagebox
        messagebox.showerror(title, message)


def main():
    """Main function"""
    # Create root window
    root = tk.Tk()
    
    # Create analyzer instance
    analyzer = None
    
    def start_callback(config: ScrapingConfig, gui_window: MainWindow):
        """Callback for starting analysis"""
        nonlocal analyzer
        analyzer = YouTubeChannelAnalyzer(gui_window)
        analyzer.start_analysis(config)
    
    # Create and show main window
    app = MainWindow(root, start_callback)
    
    # Run main loop
    root.mainloop()
    
    # Cleanup on exit
    if analyzer and analyzer.browser:
        try:
            analyzer.browser.close()
        except:
            pass


if __name__ == "__main__":
    main()

