"""Transcript scraper for extracting transcripts from tubetranscript.com"""

from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.utils.browser_manager import BrowserManager
from src.data.models import VideoData
from src.exceptions.custom_exceptions import TranscriptScrapingError
from src.utils.config import TRANSCRIPT_SERVICE_URL, DEFAULT_RETRY_ATTEMPTS, DEFAULT_RETRY_DELAY


class TranscriptScraper:
    """Scraper for extracting transcripts from tubetranscript.com"""
    
    def __init__(self, browser: BrowserManager):
        """Initialize transcript scraper"""
        self.browser = browser
    
    def get_transcript(self, video_url: str, retry_attempts: int = DEFAULT_RETRY_ATTEMPTS, 
                      retry_delay: int = DEFAULT_RETRY_DELAY, progress_callback=None) -> Optional[str]:
        """Get transcript for a video URL"""
        for attempt in range(retry_attempts):
            try:
                if progress_callback and attempt > 0:
                    progress_callback(f"Retrying transcript extraction (attempt {attempt + 1}/{retry_attempts})...")
                
                # Open new tab for transcript service
                self.browser.open_new_tab(TRANSCRIPT_SERVICE_URL)
                # Wait for page to load and input field to appear
                try:
                    WebDriverWait(self.browser.driver, self.browser.page_load_timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[placeholder*='YouTube'], input[placeholder*='youtube.com'], input[name*='url'], input[id*='url'], #url"))
                    )
                except:
                    self.browser.wait_for_page_load()
                
                # Find the input field for YouTube URL
                input_selectors = [
                    "input[type='text']",
                    "input[placeholder*='YouTube']",
                    "input[placeholder*='youtube.com']",
                    "input[name*='url']",
                    "input[id*='url']",
                    "#url",
                    "input.form-control",
                    "input[class*='input']",
                ]
                
                input_element = None
                for selector in input_selectors:
                    try:
                        elements = self.browser.find_elements(By.CSS_SELECTOR, selector)
                        for elem in elements:
                            # Check if it's visible and likely the right input
                            if elem.is_displayed() and elem.is_enabled():
                                placeholder = elem.get_attribute('placeholder') or ''
                                if 'youtube' in placeholder.lower() or 'url' in placeholder.lower() or not placeholder:
                                    input_element = elem
                                    break
                        if input_element:
                            break
                    except:
                        continue
                
                if not input_element:
                    raise TranscriptScrapingError("Could not find URL input field")
                
                # Enter video URL
                input_element.clear()
                input_element.send_keys(video_url)
                # Wait briefly for input to be processed
                try:
                    WebDriverWait(self.browser.driver, 1).until(
                        lambda d: input_element.get_attribute('value') == video_url
                    )
                except:
                    pass  # Continue even if value not set immediately
                
                # Find and click the generate button
                button_selectors = [
                    "button:contains('Generate')",
                    "button:contains('Transcribe')",
                    "button[type='submit']",
                    "input[type='submit']",
                    "button.btn-primary",
                    "button[class*='generate']",
                    "button[class*='submit']",
                ]
                
                button_clicked = False
                for selector in button_selectors:
                    try:
                        # Try CSS selector first
                        if 'contains' not in selector:
                            buttons = self.browser.find_elements(By.CSS_SELECTOR, selector)
                            for btn in buttons:
                                if btn.is_displayed() and btn.is_enabled():
                                    btn_text = btn.text.lower()
                                    if 'generate' in btn_text or 'transcribe' in btn_text or 'submit' in btn_text:
                                        self.browser.execute_script("arguments[0].click();", btn)
                                        button_clicked = True
                                        break
                        if button_clicked:
                            break
                    except:
                        continue
                
                # If CSS selectors didn't work, try XPath
                if not button_clicked:
                    try:
                        buttons = self.browser.find_elements(By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'generate')]")
                        if not buttons:
                            buttons = self.browser.find_elements(By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'transcribe')]")
                        if buttons:
                            for btn in buttons:
                                if btn.is_displayed() and btn.is_enabled():
                                    self.browser.execute_script("arguments[0].click();", btn)
                                    button_clicked = True
                                    break
                    except:
                        pass
                
                if not button_clicked:
                    raise TranscriptScrapingError("Could not find generate/transcribe button")
                
                # Wait for transcript to be generated - wait for page to process
                try:
                    # Wait for page to start processing (any change in DOM)
                    WebDriverWait(self.browser.driver, 5).until(
                        lambda d: d.execute_script('return document.readyState') == 'complete'
                    )
                except:
                    pass
                
                # Look for transcript text
                transcript_selectors = [
                    "#transcript",
                    ".transcript",
                    "[class*='transcript']",
                    "[id*='transcript']",
                    "div[class*='result']",
                    "div[class*='output']",
                    "pre",
                    "textarea",
                ]
                
                transcript_text = None
                max_wait_time = self.browser.page_load_timeout  # Use browser timeout setting
                wait_interval = 2
                
                # Wait for transcript to appear with intelligent polling
                try:
                    WebDriverWait(self.browser.driver, max_wait_time).until(
                        lambda d: any(
                            elem.text.strip() and len(elem.text.strip()) > 50
                            and not any(error_word in elem.text.strip().lower() for error_word in ['error', 'not found', 'unavailable', 'failed'])
                            for selector in transcript_selectors
                            for elem in d.find_elements(By.CSS_SELECTOR, selector)
                            if elem.is_displayed()
                        )
                    )
                    # Now extract the transcript
                    for selector in transcript_selectors:
                        try:
                            elements = self.browser.find_elements(By.CSS_SELECTOR, selector)
                            for elem in elements:
                                if elem.is_displayed():
                                    text = elem.text.strip()
                                    if text and len(text) > 50:
                                        if not any(error_word in text.lower() for error_word in ['error', 'not found', 'unavailable', 'failed']):
                                            transcript_text = text
                                            break
                            if transcript_text:
                                break
                        except:
                            continue
                except TimeoutException:
                    # Transcript didn't appear within timeout
                    pass
                
                # Close the transcript tab
                self.browser.close_current_tab()
                
                if transcript_text:
                    return transcript_text
                else:
                    raise TranscriptScrapingError("Transcript not found or empty")
                
            except Exception as e:
                # Close tab if still open
                try:
                    if len(self.browser.driver.window_handles) > 1:
                        self.browser.close_current_tab()
                except:
                    pass
                
                if attempt < retry_attempts - 1:
                    # Wait before retry - ensure page is ready
                    try:
                        self.browser.wait_for_page_load(timeout=retry_delay)
                    except:
                        pass  # Continue even if page load check fails
                    continue
                else:
                    if progress_callback:
                        progress_callback(f"Failed to get transcript after {retry_attempts} attempts: {str(e)}")
                    return None
        
        return None
    
    def add_transcripts_to_videos(self, videos: list[VideoData], retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
                                  progress_callback=None) -> list[VideoData]:
        """Add transcripts to a list of videos"""
        for i, video in enumerate(videos, 1):
            if progress_callback:
                progress_callback(f"Getting transcript for video {i}/{len(videos)}: {video.video_title or video.video_url}")
            
            try:
                transcript = self.get_transcript(
                    video.video_url,
                    retry_attempts=retry_attempts,
                    progress_callback=progress_callback
                )
                video.transcript = transcript if transcript else "Transcript not available"
            except Exception as e:
                video.transcript = f"Error: {str(e)}"
                if progress_callback:
                    progress_callback(f"Error getting transcript: {str(e)}")
            
            # Ensure page is ready before next request
            try:
                self.browser.wait_for_page_load(timeout=2)
            except:
                pass  # Continue even if page load check fails
        
        return videos

