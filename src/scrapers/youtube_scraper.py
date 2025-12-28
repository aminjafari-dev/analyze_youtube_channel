"""YouTube scraper for extracting video information from Shorts"""

import re
from typing import List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.utils.browser_manager import BrowserManager
from src.data.models import VideoData, ScrapingConfig
from src.exceptions.custom_exceptions import YouTubeScrapingError
from src.utils.config import YOUTUBE_BASE_URL


class YouTubeScraper:
    """Scraper for YouTube channel Shorts"""
    
    def __init__(self, browser: BrowserManager):
        """Initialize YouTube scraper"""
        self.browser = browser
    
    def get_channel_shorts_url(self, channel_url: str) -> str:
        """Convert channel URL to Shorts section URL"""
        # Normalize channel URL
        channel_url = channel_url.strip()
        
        # If it's already a shorts URL, return it
        if '/shorts' in channel_url:
            return channel_url
        
        # Extract channel identifier
        if '/@' in channel_url:
            # Handle @username format
            match = re.search(r'/@([^/?]+)', channel_url)
            if match:
                username = match.group(1)
                return f"{YOUTUBE_BASE_URL}/@{username}/shorts"
        
        # Handle /channel/ format
        if '/channel/' in channel_url:
            channel_id = channel_url.split('/channel/')[-1].split('/')[0].split('?')[0]
            return f"{YOUTUBE_BASE_URL}/channel/{channel_id}/shorts"
        
        # Handle /c/ format
        if '/c/' in channel_url:
            channel_name = channel_url.split('/c/')[-1].split('/')[0].split('?')[0]
            return f"{YOUTUBE_BASE_URL}/c/{channel_name}/shorts"
        
        # Default: try to append /shorts
        if channel_url.endswith('/'):
            return f"{channel_url}shorts"
        return f"{channel_url}/shorts"
    
    def navigate_to_shorts(self, channel_url: str):
        """Navigate to channel Shorts section"""
        try:
            shorts_url = self.get_channel_shorts_url(channel_url)
            self.browser.navigate(shorts_url)
            # Wait for page to load - check for video elements or channel name
            try:
                WebDriverWait(self.browser.driver, 10).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, "a[href*='/shorts/'], a[href*='/watch?v=']")) > 0
                    or d.find_elements(By.CSS_SELECTOR, "#channel-name, ytd-channel-name")
                )
            except:
                # If specific elements not found, at least wait for page ready
                self.browser.wait_for_page_load()
        except Exception as e:
            raise YouTubeScrapingError(f"Failed to navigate to Shorts: {str(e)}")
    
    def set_sort_mode(self, mode: str = "Popular"):
        """Set the sort mode for videos"""
        try:
            # Wait for the sort button/dropdown to appear
            try:
                WebDriverWait(self.browser.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label*='Sort'], button[aria-label*='Filter'], yt-chip-cloud-chip-renderer, #filter-button"))
                )
            except:
                pass  # Continue even if sort button not found
            
            # Try to find and click the filter/sort button
            # YouTube's UI may vary, so we try multiple selectors
            sort_selectors = [
                "button[aria-label*='Sort']",
                "button[aria-label*='Filter']",
                "yt-chip-cloud-chip-renderer",
                "#filter-button",
            ]
            
            sort_clicked = False
            for selector in sort_selectors:
                try:
                    elements = self.browser.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].is_displayed():
                        self.browser.execute_script("arguments[0].click();", elements[0])
                        sort_clicked = True
                        # Wait for dropdown/menu to appear
                        try:
                            WebDriverWait(self.browser.driver, 3).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "yt-formatted-string, *[aria-label*='Popular']"))
                            )
                        except:
                            pass
                        break
                except:
                    continue
            
            if not sort_clicked:
                # Try scrolling to trigger lazy loading
                self.browser.execute_script("window.scrollTo(0, 500);")
                # Wait for scroll to complete
                WebDriverWait(self.browser.driver, 2).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
            
            # If mode is Popular, try to select it
            if mode == "Popular" and sort_clicked:
                # Look for "Most popular" or similar option
                popular_selectors = [
                    "yt-formatted-string",
                    "*[aria-label*='Popular']",
                ]
                
                for selector in popular_selectors:
                    try:
                        elements = self.browser.find_elements(By.CSS_SELECTOR, selector)
                        for elem in elements:
                            if elem.is_displayed() and ('popular' in elem.text.lower() or 'most viewed' in elem.text.lower()):
                                self.browser.execute_script("arguments[0].click();", elem)
                                # Wait for sort to apply
                                try:
                                    WebDriverWait(self.browser.driver, 3).until(
                                        lambda d: d.execute_script('return document.readyState') == 'complete'
                                    )
                                except:
                                    pass
                                return
                    except:
                        continue
            
        except Exception as e:
            # If sorting fails, continue anyway - videos might already be sorted
            print(f"Warning: Could not set sort mode: {str(e)}")
    
    def extract_video_links(self, count: int = 10) -> List[str]:
        """Extract video links from the Shorts page"""
        try:
            video_links = []
            
            # Scroll to load more videos
            scroll_attempts = 0
            max_scrolls = 5
            
            while len(video_links) < count and scroll_attempts < max_scrolls:
                # Find all video links
                video_elements = self.browser.find_elements(
                    By.CSS_SELECTOR,
                    "a[href*='/shorts/'], a[href*='/watch?v=']"
                )
                
                for elem in video_elements:
                    href = elem.get_attribute('href')
                    if href and ('/shorts/' in href or '/watch?v=' in href):
                        # Clean the URL
                        if '/shorts/' in href:
                            video_id = href.split('/shorts/')[-1].split('?')[0]
                            full_url = f"{YOUTUBE_BASE_URL}/shorts/{video_id}"
                        else:
                            full_url = href.split('&')[0]  # Remove extra parameters
                        
                        if full_url not in video_links:
                            video_links.append(full_url)
                        
                        if len(video_links) >= count:
                            break
                
                # Scroll down to load more
                if len(video_links) < count:
                    self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    # Wait for new content to load after scroll
                    try:
                        WebDriverWait(self.browser.driver, 3).until(
                            lambda d: d.execute_script('return document.readyState') == 'complete'
                        )
                        # Additional wait for lazy-loaded videos
                        WebDriverWait(self.browser.driver, 2).until(
                            lambda d: len(d.find_elements(By.CSS_SELECTOR, "a[href*='/shorts/'], a[href*='/watch?v=']")) > len(video_links)
                        )
                    except:
                        # If no new videos loaded, that's okay - continue
                        pass
                    scroll_attempts += 1
            
            return video_links[:count]
            
        except Exception as e:
            raise YouTubeScrapingError(f"Failed to extract video links: {str(e)}")
    
    def extract_channel_name(self) -> str:
        """Extract channel name from the page"""
        try:
            # Try multiple selectors for channel name
            selectors = [
                "#channel-name a",
                "#text-container a",
                "ytd-channel-name a",
                "yt-formatted-string#text",
            ]
            
            for selector in selectors:
                try:
                    element = self.browser.find_element(By.CSS_SELECTOR, selector)
                    name = element.text.strip()
                    if name:
                        return name
                except:
                    continue
            
            # Fallback: try to get from URL
            current_url = self.browser.driver.current_url
            if '/@' in current_url:
                match = re.search(r'/@([^/?]+)', current_url)
                if match:
                    return match.group(1)
            
            return "Unknown Channel"
            
        except Exception as e:
            return "Unknown Channel"
    
    def extract_video_metadata(self, video_url: str) -> dict:
        """Extract metadata from a video page"""
        metadata = {
            'title': '',
            'views': '',
            'likes': '',
            'comments': '',
            'description': '',
            'upload_date': ''
        }
        
        try:
            # Navigate to video
            self.browser.navigate(video_url)
            # Wait for video page to load - check for title element
            try:
                WebDriverWait(self.browser.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.ytd-watch-metadata yt-formatted-string, h1 yt-formatted-string"))
                )
            except:
                # If title not found, at least wait for page ready
                self.browser.wait_for_page_load()
            
            # Extract title
            try:
                title_elem = self.browser.find_element(By.CSS_SELECTOR, "h1.ytd-watch-metadata yt-formatted-string, h1 yt-formatted-string")
                metadata['title'] = title_elem.text.strip()
            except:
                pass
            
            # Extract views
            try:
                views_elem = self.browser.find_element(By.CSS_SELECTOR, "#info-strings yt-formatted-string, .view-count")
                views_text = views_elem.text.strip()
                metadata['views'] = views_text
            except:
                pass
            
            # Extract likes
            try:
                likes_elem = self.browser.find_element(By.CSS_SELECTOR, "#top-level-buttons-computed button[aria-label*='like']")
                likes_text = likes_elem.get_attribute('aria-label') or likes_elem.text
                metadata['likes'] = likes_text
            except:
                pass
            
            # Extract description
            try:
                desc_elem = self.browser.find_element(By.CSS_SELECTOR, "#description, ytd-video-secondary-info-renderer #description")
                metadata['description'] = desc_elem.text.strip()
            except:
                pass
            
            # Extract upload date
            try:
                date_elem = self.browser.find_element(By.CSS_SELECTOR, "#info-strings yt-formatted-string")
                date_text = date_elem.text.strip()
                metadata['upload_date'] = date_text
            except:
                pass
            
        except Exception as e:
            print(f"Warning: Could not extract full metadata for {video_url}: {str(e)}")
        
        return metadata
    
    def scrape_videos(self, config: ScrapingConfig, progress_callback=None) -> List[VideoData]:
        """Main method to scrape videos from channel Shorts"""
        try:
            # Navigate to Shorts
            if progress_callback:
                progress_callback("Navigating to channel Shorts...")
            self.navigate_to_shorts(config.channel_url)
            
            # Extract channel name
            channel_name = self.extract_channel_name()
            if progress_callback:
                progress_callback(f"Channel found: {channel_name}")
            
            # Set sort mode
            if progress_callback:
                progress_callback(f"Setting sort mode to {config.sort_mode}...")
            self.set_sort_mode(config.sort_mode)
            
            # Extract video links
            if progress_callback:
                progress_callback(f"Extracting {config.video_count} video links...")
            video_links = self.extract_video_links(config.video_count)
            
            if not video_links:
                raise YouTubeScrapingError("No video links found")
            
            if progress_callback:
                progress_callback(f"Found {len(video_links)} videos. Extracting metadata...")
            
            # Extract metadata for each video
            videos_data = []
            for i, video_url in enumerate(video_links, 1):
                if progress_callback:
                    progress_callback(f"Processing video {i}/{len(video_links)}: {video_url}")
                
                try:
                    metadata = self.extract_video_metadata(video_url)
                    
                    video_data = VideoData(
                        channel_name=channel_name,
                        video_title=metadata.get('title', ''),
                        video_url=video_url,
                        upload_date=metadata.get('upload_date', ''),
                        views=metadata.get('views', ''),
                        likes=metadata.get('likes', ''),
                        comments=metadata.get('comments', ''),
                        description=metadata.get('description', '')
                    )
                    
                    videos_data.append(video_data)
                except Exception as e:
                    print(f"Error extracting metadata for {video_url}: {str(e)}")
                    # Create minimal video data
                    video_data = VideoData(
                        channel_name=channel_name,
                        video_title='',
                        video_url=video_url
                    )
                    videos_data.append(video_data)
            
            return videos_data
            
        except Exception as e:
            raise YouTubeScrapingError(f"Failed to scrape videos: {str(e)}")

