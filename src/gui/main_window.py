"""Main GUI window for YouTube Channel Analyzer"""

import tkinter as tk
from tkinter import messagebox, filedialog
import threading
from typing import Optional, Callable

from src.gui.components import LabeledEntry, LabeledCombobox, StyledButton, ScrollableText
from src.gui.styles import STYLES, COLOR_BACKGROUND
from src.utils.config import WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT
from src.utils.validators import validate_youtube_url, validate_video_count
from src.data.models import ScrapingConfig


class MainWindow:
    """Main application window"""
    
    def __init__(self, root: tk.Tk, start_callback: Callable):
        """Initialize main window"""
        self.root = root
        self.start_callback = start_callback
        self.is_running = False
        self.stop_requested = False
        
        self._setup_window()
        self._create_widgets()
        self._layout_widgets()
    
    def _setup_window(self):
        """Setup window properties"""
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=COLOR_BACKGROUND)
        self.root.resizable(True, True)
        
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        self.main_frame = tk.Frame(self.root, bg=COLOR_BACKGROUND, padx=20, pady=20)
        
        # Title
        title_style = STYLES['label_heading'].copy()
        title_style.pop('font', None)  # Remove font from style to use custom font
        self.title_label = tk.Label(
            self.main_frame,
            text="YouTube Channel Analyzer",
            **title_style,
            font=("Segoe UI", 16, "bold")
        )
        
        # Input section
        input_frame_style = STYLES['label'].copy()
        input_frame_style.pop('font', None)  # Remove font to use custom font
        self.input_frame = tk.LabelFrame(
            self.main_frame,
            text="Configuration",
            **input_frame_style,
            font=STYLES['label_heading']['font'],
            padx=15,
            pady=15
        )
        
        # Channel URL input
        self.channel_url_entry = LabeledEntry(
            self.input_frame,
            "Channel URL:",
            width=60
        )
        # Set placeholder text manually
        self.channel_url_entry.entry.insert(0, "https://www.youtube.com/@channelname")
        self.channel_url_entry.entry.config(fg='gray')
        
        def on_focus_in(event):
            if self.channel_url_entry.entry.get() == "https://www.youtube.com/@channelname":
                self.channel_url_entry.entry.delete(0, tk.END)
                self.channel_url_entry.entry.config(fg='black')
        
        def on_focus_out(event):
            if not self.channel_url_entry.entry.get():
                self.channel_url_entry.entry.insert(0, "https://www.youtube.com/@channelname")
                self.channel_url_entry.entry.config(fg='gray')
        
        self.channel_url_entry.entry.bind('<FocusIn>', on_focus_in)
        self.channel_url_entry.entry.bind('<FocusOut>', on_focus_out)
        
        # Video count selector
        self.video_count_combo = LabeledCombobox(
            self.input_frame,
            "Number of Videos:",
            values=[str(i) for i in range(1, 21)],
            width=10
        )
        self.video_count_combo.set("10")
        
        # Sort mode selector
        self.sort_mode_combo = LabeledCombobox(
            self.input_frame,
            "Sort Mode:",
            values=["Popular", "Recent"],
            width=15
        )
        self.sort_mode_combo.set("Popular")
        
        # Buttons frame
        self.buttons_frame = tk.Frame(self.input_frame, bg=COLOR_BACKGROUND)
        
        # Control buttons
        self.start_button = StyledButton(
            self.buttons_frame,
            "Start Analysis",
            style='primary',
            command=self._on_start_clicked
        )
        
        self.stop_button = StyledButton(
            self.buttons_frame,
            "Stop",
            style='danger',
            command=self._on_stop_clicked
        )
        self.stop_button.disable()
        
        self.clear_button = StyledButton(
            self.buttons_frame,
            "Clear",
            style='secondary',
            command=self._on_clear_clicked
        )
        
        # Progress section
        progress_frame_style = STYLES['label'].copy()
        progress_frame_style.pop('font', None)  # Remove font to use custom font
        self.progress_frame = tk.LabelFrame(
            self.main_frame,
            text="Progress",
            **progress_frame_style,
            font=STYLES['label_heading']['font'],
            padx=15,
            pady=15
        )
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = tk.ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400,
            mode='determinate'
        )
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="Ready",
            **STYLES['label']
        )
        
        # Log section
        log_frame_style = STYLES['label'].copy()
        log_frame_style.pop('font', None)  # Remove font to use custom font
        self.log_frame = tk.LabelFrame(
            self.main_frame,
            text="Status Log",
            **log_frame_style,
            font=STYLES['label_heading']['font'],
            padx=15,
            pady=15
        )
        
        self.log_text = ScrollableText(self.log_frame, height=12, width=80)
    
    def _layout_widgets(self):
        """Layout all widgets"""
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        self.title_label.pack(pady=(0, 20))
        
        # Input section
        self.input_frame.pack(fill=tk.X, pady=(0, 15))
        self.channel_url_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Options in a row
        options_frame = tk.Frame(self.input_frame, bg=COLOR_BACKGROUND)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.video_count_combo.frame.pack(side=tk.LEFT, padx=(0, 20))
        self.sort_mode_combo.frame.pack(side=tk.LEFT)
        
        # Buttons
        self.buttons_frame.pack(fill=tk.X)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        self.clear_button.pack(side=tk.LEFT)
        
        # Progress section
        self.progress_frame.pack(fill=tk.X, pady=(0, 15))
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        self.progress_label.pack(anchor='w')
        
        # Log section
        self.log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def _on_start_clicked(self):
        """Handle start button click"""
        # Validate inputs
        channel_url = self.channel_url_entry.get().strip()
        # Ignore placeholder text
        if not channel_url or channel_url == "https://www.youtube.com/@channelname":
            messagebox.showerror("Error", "Please enter a channel URL")
            return
        
        if not validate_youtube_url(channel_url):
            messagebox.showerror("Error", "Please enter a valid YouTube channel URL")
            return
        
        try:
            video_count = int(self.video_count_combo.get())
            if not validate_video_count(video_count):
                messagebox.showerror("Error", "Video count must be between 1 and 20")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid video count")
            return
        
        sort_mode = self.sort_mode_combo.get()
        
        # Create config
        config = ScrapingConfig(
            channel_url=channel_url,
            video_count=video_count,
            sort_mode=sort_mode
        )
        
        # Disable inputs and start button
        self._set_inputs_enabled(False)
        self.start_button.disable()
        self.stop_button.enable()
        self.is_running = True
        self.stop_requested = False
        
        # Clear log
        self.log_text.clear()
        self.log("Starting analysis...")
        self.log(f"Channel: {channel_url}")
        self.log(f"Videos: {video_count}, Sort: {sort_mode}")
        self.log("-" * 50)
        
        # Update progress
        self.update_progress(0, "Initializing...")
        
        # Start scraping in a separate thread
        thread = threading.Thread(target=self._run_scraping, args=(config,), daemon=True)
        thread.start()
    
    def _on_stop_clicked(self):
        """Handle stop button click"""
        self.stop_requested = True
        self.log("Stop requested...")
    
    def _on_clear_clicked(self):
        """Handle clear button click"""
        if self.is_running:
            if not messagebox.askyesno("Confirm", "Analysis is running. Stop and clear?"):
                return
            self.stop_requested = True
        
        self.channel_url_entry.clear()
        # Restore placeholder
        self.channel_url_entry.entry.insert(0, "https://www.youtube.com/@channelname")
        self.channel_url_entry.entry.config(fg='gray')
        self.video_count_combo.set("10")
        self.sort_mode_combo.set("Popular")
        self.log_text.clear()
        self.update_progress(0, "Ready")
    
    def _run_scraping(self, config: ScrapingConfig):
        """Run scraping in background thread"""
        try:
            self.start_callback(config, self)
        except Exception as e:
            self.log(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self._set_inputs_enabled(True)
            self.start_button.enable()
            self.stop_button.disable()
            self.is_running = False
            self.update_progress(100, "Completed")
    
    def _set_inputs_enabled(self, enabled: bool):
        """Enable or disable input fields"""
        if enabled:
            self.channel_url_entry.enable()
            self.video_count_combo.enable()
            self.sort_mode_combo.enable()
        else:
            self.channel_url_entry.disable()
            self.video_count_combo.disable()
            self.sort_mode_combo.disable()
    
    def log(self, message: str):
        """Add message to log"""
        self.log_text.insert(f"[{self._get_timestamp()}] {message}")
    
    def update_progress(self, value: float, message: str = ""):
        """Update progress bar and label"""
        self.progress_var.set(value)
        if message:
            self.progress_label.config(text=message)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def should_stop(self) -> bool:
        """Check if stop was requested"""
        return self.stop_requested

