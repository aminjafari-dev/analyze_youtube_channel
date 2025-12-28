"""Browser automation manager using Selenium"""

import os
import pickle
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from src.utils.config import (
    BROWSER_HEADLESS,
    BROWSER_TIMEOUT,
    BROWSER_IMPLICIT_WAIT,
    YOUTUBE_BASE_URL
)
from src.exceptions.custom_exceptions import BrowserError


class BrowserManager:
    """Manages browser instances and operations"""
    
    def __init__(self, headless: bool = BROWSER_HEADLESS):
        """Initialize browser manager"""
        self.driver = None
        self.headless = headless
        self.cookies_file = Path(__file__).parent.parent.parent / "youtube_cookies.pkl"
        self._setup_driver()
        self._load_cookies()
    
    def _setup_driver(self):
        """Setup Chrome WebDriver"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Use webdriver-manager to automatically handle ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(BROWSER_IMPLICIT_WAIT)
            self.driver.maximize_window()
        except Exception as e:
            raise BrowserError(f"Failed to initialize browser: {str(e)}")
    
    def navigate(self, url: str):
        """Navigate to a URL"""
        try:
            self.driver.get(url)
            # Wait for page to be ready
            WebDriverWait(self.driver, BROWSER_TIMEOUT).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except Exception as e:
            raise BrowserError(f"Failed to navigate to {url}: {str(e)}")
    
    def wait_for_element(self, by: By, value: str, timeout: int = BROWSER_TIMEOUT):
        """Wait for an element to be present"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            raise BrowserError(f"Element not found: {by}={value}")
    
    def wait_for_clickable(self, by: By, value: str, timeout: int = BROWSER_TIMEOUT):
        """Wait for an element to be clickable"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.element_to_be_clickable((by, value)))
        except TimeoutException:
            raise BrowserError(f"Element not clickable: {by}={value}")
    
    def wait_for_page_load(self, timeout: int = BROWSER_TIMEOUT):
        """Wait for page to be fully loaded"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        except TimeoutException:
            raise BrowserError("Page did not load within timeout")
    
    def wait_for_element_visible(self, by: By, value: str, timeout: int = BROWSER_TIMEOUT):
        """Wait for an element to be visible"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.visibility_of_element_located((by, value)))
        except TimeoutException:
            raise BrowserError(f"Element not visible: {by}={value}")
    
    def find_element(self, by: By, value: str):
        """Find an element"""
        try:
            return self.driver.find_element(by, value)
        except Exception as e:
            raise BrowserError(f"Element not found: {by}={value}, Error: {str(e)}")
    
    def find_elements(self, by: By, value: str):
        """Find multiple elements"""
        try:
            return self.driver.find_elements(by, value)
        except Exception as e:
            raise BrowserError(f"Elements not found: {by}={value}, Error: {str(e)}")
    
    def click_element(self, by: By, value: str):
        """Click an element"""
        try:
            element = self.wait_for_clickable(by, value)
            self.driver.execute_script("arguments[0].click();", element)
            # Wait for any potential page changes after click
            WebDriverWait(self.driver, 2).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except TimeoutException:
            # If page doesn't change, that's okay
            pass
        except Exception as e:
            raise BrowserError(f"Failed to click element: {by}={value}, Error: {str(e)}")
    
    def send_keys(self, by: By, value: str, text: str):
        """Send keys to an element"""
        try:
            element = self.wait_for_element(by, value)
            element.clear()
            element.send_keys(text)
            # Wait briefly for input to be processed (no page load needed)
        except Exception as e:
            raise BrowserError(f"Failed to send keys: {by}={value}, Error: {str(e)}")
    
    def get_text(self, by: By, value: str) -> str:
        """Get text from an element"""
        try:
            element = self.wait_for_element(by, value)
            return element.text
        except Exception as e:
            raise BrowserError(f"Failed to get text: {by}={value}, Error: {str(e)}")
    
    def execute_script(self, script: str):
        """Execute JavaScript"""
        try:
            return self.driver.execute_script(script)
        except Exception as e:
            raise BrowserError(f"Failed to execute script: {str(e)}")
    
    def open_new_tab(self, url: str = None):
        """Open a new tab"""
        try:
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            if url:
                self.navigate(url)
        except Exception as e:
            raise BrowserError(f"Failed to open new tab: {str(e)}")
    
    def close_current_tab(self):
        """Close current tab and switch to previous"""
        try:
            if len(self.driver.window_handles) > 1:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[-1])
        except Exception as e:
            raise BrowserError(f"Failed to close tab: {str(e)}")
    
    def switch_to_tab(self, index: int):
        """Switch to a specific tab by index"""
        try:
            handles = self.driver.window_handles
            if 0 <= index < len(handles):
                self.driver.switch_to.window(handles[index])
        except Exception as e:
            raise BrowserError(f"Failed to switch tab: {str(e)}")
    
    def _load_cookies(self):
        """Load saved cookies if they exist"""
        try:
            if self.cookies_file.exists() and self.driver:
                # First navigate to YouTube to set the domain
                self.driver.get(YOUTUBE_BASE_URL)
                self.wait_for_page_load()
                
                # Load cookies
                with open(self.cookies_file, 'rb') as f:
                    cookies = pickle.load(f)
                
                # Add each cookie
                for cookie in cookies:
                    try:
                        # Remove 'expiry' if it's too large (causes issues)
                        if 'expiry' in cookie:
                            # Check if expiry is a valid integer
                            if isinstance(cookie['expiry'], (int, float)):
                                self.driver.add_cookie(cookie)
                            else:
                                cookie_copy = cookie.copy()
                                cookie_copy.pop('expiry', None)
                                self.driver.add_cookie(cookie_copy)
                        else:
                            self.driver.add_cookie(cookie)
                    except Exception as e:
                        # Skip invalid cookies
                        continue
                
                # Refresh to apply cookies
                self.driver.refresh()
                self.wait_for_page_load()
        except Exception as e:
            # If loading cookies fails, continue without them
            pass
    
    def _save_cookies(self):
        """Save current cookies to file"""
        try:
            if self.driver:
                cookies = self.driver.get_cookies()
                # Ensure directory exists
                self.cookies_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.cookies_file, 'wb') as f:
                    pickle.dump(cookies, f)
        except Exception as e:
            # If saving fails, continue without saving
            pass
    
    def is_logged_in_youtube(self) -> bool:
        """Check if user is logged in to YouTube"""
        try:
            if not self.driver:
                return False
            
            # Navigate to YouTube homepage
            self.navigate(YOUTUBE_BASE_URL)
            self.wait_for_page_load()
            
            # Wait a bit for page to fully render
            import time
            time.sleep(2)
            
            # Check for login indicators
            # If logged in, we should see profile picture or account menu
            logged_in_indicators = [
                "yt-img-shadow img[alt*='account']",  # Profile picture
                "button[aria-label*='account']",  # Account button
                "button#avatar-btn",  # Avatar button
                "yt-img-shadow#avatar",  # Avatar image
                "button[aria-label*='Google Account']",  # Google account button
            ]
            
            for selector in logged_in_indicators:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and any(elem.is_displayed() for elem in elements):
                        return True
                except:
                    continue
            
            # Also check if we can see "Sign in" button (means not logged in)
            sign_in_selectors = [
                "a[aria-label*='Sign in']",
                "button[aria-label*='Sign in']",
                "yt-button-shape a[href*='accounts.google.com']",
            ]
            
            for selector in sign_in_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and any(elem.is_displayed() for elem in elements):
                        return False
                except:
                    continue
            
            # If we can't determine, assume not logged in
            return False
            
        except Exception as e:
            # If check fails, assume not logged in
            return False
    
    def ensure_youtube_login(self, progress_callback=None, show_message_callback=None):
        """Ensure user is logged in to YouTube, show login page if not"""
        try:
            if progress_callback:
                progress_callback("Checking YouTube login status...")
            
            # Check if already logged in
            if self.is_logged_in_youtube():
                if progress_callback:
                    progress_callback("Already logged in to YouTube")
                self._save_cookies()
                return True
            
            # Not logged in, show login page
            if progress_callback:
                progress_callback("Not logged in. Opening login page...")
            
            # Show message to user
            if show_message_callback:
                show_message_callback(
                    "Login Required",
                    "Please log in to YouTube in the browser window.\n\n"
                    "The browser will wait for you to complete the login process.\n"
                    "After logging in, the analysis will continue automatically."
                )
            
            # Navigate to YouTube homepage (better than /signin as it redirects properly)
            self.navigate(YOUTUBE_BASE_URL)
            self.wait_for_page_load()
            
            # Try to click sign in button if visible
            try:
                sign_in_selectors = [
                    "a[aria-label*='Sign in']",
                    "button[aria-label*='Sign in']",
                    "yt-button-shape a[href*='accounts.google.com']",
                    "a[href*='/ServiceLogin']",
                ]
                
                for selector in sign_in_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in elements:
                            if elem.is_displayed():
                                self.driver.execute_script("arguments[0].click();", elem)
                                self.wait_for_page_load()
                                break
                    except:
                        continue
            except:
                pass  # If clicking sign in fails, user can navigate manually
            
            # Wait for user to log in manually
            # Check every 3 seconds if user has logged in
            max_wait_time = 300  # 5 minutes max wait
            check_interval = 3  # Check every 3 seconds
            elapsed_time = 0
            
            if progress_callback:
                progress_callback("Waiting for you to log in in the browser window...")
            
            while elapsed_time < max_wait_time:
                time.sleep(check_interval)
                elapsed_time += check_interval
                
                # Check if logged in now
                if self.is_logged_in_youtube():
                    if progress_callback:
                        progress_callback("Login successful! Saving session...")
                    self._save_cookies()
                    return True
                
                # Update progress message
                if progress_callback and elapsed_time % 15 == 0:  # Every 15 seconds
                    remaining = (max_wait_time - elapsed_time) // 60
                    progress_callback(f"Still waiting for login... ({remaining} minutes remaining)")
            
            # Timeout
            if progress_callback:
                progress_callback("Login timeout. Please try again.")
            return False
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error during login check: {str(e)}")
            return False
    
    def close(self):
        """Close the browser"""
        try:
            if self.driver:
                # Save cookies before closing
                self._save_cookies()
                self.driver.quit()
        except Exception as e:
            raise BrowserError(f"Failed to close browser: {str(e)}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

