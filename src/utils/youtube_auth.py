"""YouTube authentication manager"""

import pickle
from pathlib import Path
from typing import Optional, Callable
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from src.utils.config import YOUTUBE_BASE_URL
from src.utils.browser_manager import BrowserManager


class YouTubeAuthManager:
    """Manages YouTube authentication and session persistence"""
    
    def __init__(self, browser: BrowserManager):
        """Initialize YouTube authentication manager"""
        self.browser = browser
        self.cookies_file = Path(__file__).parent.parent.parent / "youtube_cookies.pkl"
        self._load_cookies()
    
    def _load_cookies(self):
        """Load saved cookies if they exist"""
        try:
            if self.cookies_file.exists() and self.browser.driver:
                # First navigate to YouTube to set the domain
                self.browser.driver.get(YOUTUBE_BASE_URL)
                self.browser.wait_for_page_load()
                
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
                                self.browser.driver.add_cookie(cookie)
                            else:
                                cookie_copy = cookie.copy()
                                cookie_copy.pop('expiry', None)
                                self.browser.driver.add_cookie(cookie_copy)
                        else:
                            self.browser.driver.add_cookie(cookie)
                    except Exception as e:
                        # Skip invalid cookies
                        continue
                
                # Refresh to apply cookies
                self.browser.driver.refresh()
                self.browser.wait_for_page_load()
        except Exception as e:
            # If loading cookies fails, continue without them
            pass
    
    def _save_cookies(self):
        """Save current cookies to file"""
        try:
            if self.browser.driver:
                cookies = self.browser.driver.get_cookies()
                # Ensure directory exists
                self.cookies_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.cookies_file, 'wb') as f:
                    pickle.dump(cookies, f)
        except Exception as e:
            # If saving fails, continue without saving
            pass
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in to YouTube"""
        try:
            if not self.browser.driver:
                return False
            
            # Navigate to YouTube homepage
            self.browser.navigate(YOUTUBE_BASE_URL)
            
            # Wait for page to load AND for login indicators to appear
            logged_in_indicators = [
                "yt-img-shadow img[alt*='account']",  # Profile picture
                "button[aria-label*='account']",  # Account button
                "button#avatar-btn",  # Avatar button
                "yt-img-shadow#avatar",  # Avatar image
                "button[aria-label*='Google Account']",  # Google account button
            ]
            
            sign_in_selectors = [
                "a[aria-label*='Sign in']",
                "button[aria-label*='Sign in']",
                "yt-button-shape a[href*='accounts.google.com']",
            ]
            
            # Wait for page to load and for either login or sign-in elements to appear
            all_selectors = logged_in_indicators + sign_in_selectors
            self.browser.wait_for_page_load(wait_for_elements=all_selectors)
            
            # Check for login indicators first
            for selector in logged_in_indicators:
                try:
                    elements = self.browser.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and any(elem.is_displayed() for elem in elements):
                        return True
                except:
                    continue
            
            # Check if we can see "Sign in" button (means not logged in)
            for selector in sign_in_selectors:
                try:
                    elements = self.browser.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and any(elem.is_displayed() for elem in elements):
                        return False
                except:
                    continue
            
            # If we can't determine, assume not logged in
            return False
            
        except Exception as e:
            # If check fails, assume not logged in
            return False
    
    def ensure_login(
        self, 
        progress_callback: Optional[Callable[[str], None]] = None,
        show_message_callback: Optional[Callable[[str, str], None]] = None
    ) -> bool:
        """Ensure user is logged in to YouTube, show login page if not"""
        try:
            if progress_callback:
                progress_callback("Checking YouTube login status...")
            
            # Check if already logged in
            if self.is_logged_in():
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
            self.browser.navigate(YOUTUBE_BASE_URL)
            self.browser.wait_for_page_load()
            
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
                        elements = self.browser.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in elements:
                            if elem.is_displayed():
                                self.browser.driver.execute_script("arguments[0].click();", elem)
                                self.browser.wait_for_page_load()
                                break
                    except:
                        continue
            except:
                pass  # If clicking sign in fails, user can navigate manually
            
            # Wait for user to log in manually
            # Use intelligent polling - wait for login status to change
            max_wait_time = 300  # 5 minutes max wait
            
            if progress_callback:
                progress_callback("Waiting for you to log in in the browser window...")
            
            # Wait for login status to change using WebDriverWait
            try:
                def login_status_changed(driver):
                    """Check if user has logged in"""
                    try:
                        # Check for login indicators
                        logged_in_indicators = [
                            "yt-img-shadow img[alt*='account']",
                            "button[aria-label*='account']",
                            "button#avatar-btn",
                            "yt-img-shadow#avatar",
                            "button[aria-label*='Google Account']",
                        ]
                        
                        for selector in logged_in_indicators:
                            try:
                                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                if elements and any(elem.is_displayed() for elem in elements):
                                    return True
                            except:
                                continue
                        
                        # Also check if sign-in button disappeared (means logged in)
                        sign_in_selectors = [
                            "a[aria-label*='Sign in']",
                            "button[aria-label*='Sign in']",
                            "yt-button-shape a[href*='accounts.google.com']",
                        ]
                        
                        sign_in_visible = False
                        for selector in sign_in_selectors:
                            try:
                                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                if elements and any(elem.is_displayed() for elem in elements):
                                    sign_in_visible = True
                                    break
                            except:
                                continue
                        
                        # If sign-in is not visible and we're on YouTube, might be logged in
                        if not sign_in_visible and YOUTUBE_BASE_URL in driver.current_url:
                            # Double check by looking for account elements
                            for selector in logged_in_indicators:
                                try:
                                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                    if elements:
                                        return True
                                except:
                                    continue
                        
                        return False
                    except:
                        return False
                
                # Wait for login status to change
                wait = WebDriverWait(self.browser.driver, max_wait_time)
                wait.until(login_status_changed)
                
                # Login successful
                if progress_callback:
                    progress_callback("Login successful! Saving session...")
                self._save_cookies()
                return True
                
            except TimeoutException:
                # Timeout - user didn't log in
                if progress_callback:
                    progress_callback("Login timeout. Please try again.")
                return False
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error during login check: {str(e)}")
            return False
    
    def save_session(self):
        """Save current session cookies"""
        self._save_cookies()
    
    def cleanup(self):
        """Cleanup - save cookies before closing"""
        self._save_cookies()

