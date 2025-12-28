"""Browser automation manager using Selenium"""

import os
import pickle
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
    
    def __init__(self, headless: bool = BROWSER_HEADLESS, page_load_timeout: int = None):
        """Initialize browser manager"""
        self.driver = None
        self.headless = headless
        self.page_load_timeout = page_load_timeout if page_load_timeout is not None else BROWSER_TIMEOUT
        self.cookies_file = Path(__file__).parent.parent.parent / "youtube_cookies.pkl"
        self._setup_driver()
    
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
            WebDriverWait(self.driver, self.page_load_timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except Exception as e:
            raise BrowserError(f"Failed to navigate to {url}: {str(e)}")
    
    def wait_for_element(self, by: By, value: str, timeout: int = None):
        """Wait for an element to be present"""
        if timeout is None:
            timeout = self.page_load_timeout
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            raise BrowserError(f"Element not found: {by}={value}")
    
    def wait_for_clickable(self, by: By, value: str, timeout: int = None):
        """Wait for an element to be clickable"""
        if timeout is None:
            timeout = self.page_load_timeout
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.element_to_be_clickable((by, value)))
        except TimeoutException:
            raise BrowserError(f"Element not clickable: {by}={value}")
    
    def wait_for_page_load(self, timeout: int = None, wait_for_elements: list = None):
        """
        Wait for page to be fully loaded and optionally for specific elements to appear.
        This is the main function for waiting - no time.sleep is used.
        
        Args:
            timeout: Maximum time to wait (uses instance default if None)
            wait_for_elements: Optional list of CSS selectors to wait for
        """
        if timeout is None:
            timeout = self.page_load_timeout
        try:
            wait = WebDriverWait(self.driver, timeout)
            
            # First wait for document ready state
            wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
            
            # If specific elements are requested, wait for at least one to appear
            if wait_for_elements:
                def any_element_present(driver):
                    for selector in wait_for_elements:
                        try:
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            if elements and any(elem.is_displayed() for elem in elements):
                                return True
                        except:
                            continue
                    return False
                
                wait.until(any_element_present)
            
            # Additional check: wait for jQuery (if present) to be ready
            try:
                wait.until(lambda d: d.execute_script('return typeof jQuery === "undefined" || jQuery.active === 0'))
            except:
                pass  # jQuery might not be present, that's okay
            
        except TimeoutException:
            raise BrowserError("Page did not load within timeout")
    
    def wait_for_element_visible(self, by: By, value: str, timeout: int = None):
        """Wait for an element to be visible"""
        if timeout is None:
            timeout = self.page_load_timeout
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
    
    def close(self):
        """Close the browser"""
        try:
            if self.driver:
                self.driver.quit()
        except Exception as e:
            raise BrowserError(f"Failed to close browser: {str(e)}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

