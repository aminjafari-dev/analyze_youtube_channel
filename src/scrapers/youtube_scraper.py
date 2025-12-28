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
            video_selectors = [
                "a[href*='/shorts/']",
                "a[href*='/watch?v=']",
                "#channel-name",
                "ytd-channel-name"
            ]
            self.browser.wait_for_page_load(wait_for_elements=video_selectors)
        except Exception as e:
            raise YouTubeScrapingError(f"Failed to navigate to Shorts: {str(e)}")
    
    def set_sort_mode(self, mode: str = "Popular", page_load_timeout: int = 10):
        """Set the sort mode for videos using JavaScript to find and click the chip button
        
        Args:
            mode: Sort mode to select (Popular, Latest, Oldest)
            page_load_timeout: Timeout in seconds to wait for page loading (from GUI settings)
        """
        import time
        
        try:
            # Wait for chip buttons to appear
            try:
                WebDriverWait(self.browser.driver, page_load_timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "yt-chip-cloud-chip-renderer"))
                )
            except:
                pass
            
            # Wait for page to fully load (use half of page_load_timeout)
            wait_time = max(1, page_load_timeout // 3)
            time.sleep(wait_time)
            
            # Use JavaScript to find and click the button with the matching text
            # This directly searches for the div.ytChipShapeChip containing the mode text
            # and then clicks its parent button
            js_click_chip = f"""
            (function() {{
                // Find all chip divs
                var chipDivs = document.querySelectorAll('div.ytChipShapeChip');
                
                for (var i = 0; i < chipDivs.length; i++) {{
                    var div = chipDivs[i];
                    var text = div.textContent || div.innerText;
                    text = text.trim().toLowerCase();
                    
                    if (text === '{mode.lower()}') {{
                        // Found the chip, now find and click the parent button
                        var button = div.closest('button');
                        if (button) {{
                            button.scrollIntoView({{block: 'center'}});
                            button.click();
                            return 'clicked: ' + text;
                        }}
                    }}
                }}
                
                // Try alternative: find yt-chip-cloud-chip-renderer elements
                var renderers = document.querySelectorAll('yt-chip-cloud-chip-renderer');
                for (var j = 0; j < renderers.length; j++) {{
                    var renderer = renderers[j];
                    var text = renderer.textContent || renderer.innerText;
                    text = text.trim().toLowerCase();
                    
                    if (text === '{mode.lower()}') {{
                        var button = renderer.querySelector('button');
                        if (button) {{
                            button.scrollIntoView({{block: 'center'}});
                            button.click();
                            return 'clicked via renderer: ' + text;
                        }}
                    }}
                }}
                
                // Last try: find any button with role="tab" containing the text
                var buttons = document.querySelectorAll('button[role="tab"]');
                for (var k = 0; k < buttons.length; k++) {{
                    var btn = buttons[k];
                    var text = btn.textContent || btn.innerText;
                    text = text.trim().toLowerCase();
                    
                    if (text === '{mode.lower()}') {{
                        btn.scrollIntoView({{block: 'center'}});
                        btn.click();
                        return 'clicked via tab button: ' + text;
                    }}
                }}
                
                return 'not found';
            }})();
            """
            
            result = self.browser.execute_script(js_click_chip)
            print(f"JavaScript chip click result: {result}")
            
            if result and 'clicked' in str(result):
                print(f"Successfully clicked on '{mode}' chip")
                print(f"Waiting for page to reload after sort change (timeout: {page_load_timeout}s)...")
                
                # Calculate wait times based on page_load_timeout
                initial_wait = max(1, page_load_timeout // 5)  # 20% of timeout
                video_wait = max(2, page_load_timeout // 3)    # 33% of timeout
                final_wait = max(1, page_load_timeout // 5)    # 20% of timeout
                
                # Wait for page to reload with new sorted content
                time.sleep(initial_wait)
                
                # Wait for document to be ready
                try:
                    WebDriverWait(self.browser.driver, page_load_timeout).until(
                        lambda d: d.execute_script('return document.readyState') == 'complete'
                    )
                except:
                    pass
                
                # Additional wait for videos to load after sorting
                time.sleep(video_wait)
                
                # Wait for video elements to appear
                try:
                    WebDriverWait(self.browser.driver, page_load_timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/shorts/']"))
                    )
                except:
                    pass
                
                # Final wait to ensure all content is loaded
                time.sleep(final_wait)
                print(f"Sort mode '{mode}' applied and page reloaded")
            else:
                print(f"Warning: Could not find '{mode}' chip button")
                # Debug: print all chip texts found
                debug_js = """
                (function() {
                    var texts = [];
                    var chipDivs = document.querySelectorAll('div.ytChipShapeChip');
                    for (var i = 0; i < chipDivs.length; i++) {
                        texts.push(chipDivs[i].textContent.trim());
                    }
                    return texts;
                })();
                """
                chip_texts = self.browser.execute_script(debug_js)
                print(f"Available chip texts: {chip_texts}")
            
        except Exception as e:
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
        """Extract metadata from a YouTube Shorts video page using Description panel"""
        import time
        from selenium.webdriver.common.action_chains import ActionChains
        
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
            
            # Wait for Shorts player to load
            try:
                WebDriverWait(self.browser.driver, self.browser.page_load_timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-reel-video-renderer, #shorts-player"))
                )
            except:
                self.browser.wait_for_page_load()
            
            time.sleep(1)  # Small wait for video to be interactive
            
            # Check if this is a Shorts video
            is_shorts = '/shorts/' in video_url
            
            if is_shorts:
                # For Shorts: Hover over video, click three dots, open Description panel
                metadata = self._extract_shorts_metadata(metadata)
            else:
                # For regular videos: Use traditional method
                metadata = self._extract_regular_video_metadata(metadata)
            
        except Exception as e:
            print(f"Warning: Could not extract full metadata for {video_url}: {str(e)}")
        
        return metadata
    
    def _extract_shorts_metadata(self, metadata: dict) -> dict:
        """Extract metadata from Shorts using Description panel"""
        import time
        from selenium.webdriver.common.action_chains import ActionChains
        
        try:
            # Step 1: Find and hover over the video player area to make controls visible
            try:
                # Find the video player area
                player_selectors = [
                    "#shorts-player",
                    "ytd-reel-video-renderer",
                    "#player-container",
                    "div.player-container",
                    "ytd-shorts"
                ]
                
                player = None
                for selector in player_selectors:
                    try:
                        player = self.browser.find_element(By.CSS_SELECTOR, selector)
                        if player:
                            break
                    except:
                        continue
                
                if player:
                    # Hover over the player to reveal controls
                    actions = ActionChains(self.browser.driver)
                    actions.move_to_element(player).perform()
                    time.sleep(0.5)
            except Exception as e:
                print(f"Could not hover over player: {e}")
            
            # Step 2: Find and click the three dots menu button
            three_dots_selectors = [
                "button.yt-spec-button-shape-next--icon-button[aria-label*='More']",
                "button[aria-label='More actions']",
                "button[aria-label*='actions']",
                "#button[aria-label*='More']",
                "yt-icon-button#button",
                "ytd-menu-renderer button",
                "button.ytd-menu-renderer"
            ]
            
            menu_clicked = False
            for selector in three_dots_selectors:
                try:
                    buttons = self.browser.driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        # Check if button is visible and contains three dots icon
                        if btn.is_displayed():
                            btn.click()
                            menu_clicked = True
                            time.sleep(0.5)
                            break
                    if menu_clicked:
                        break
                except:
                    continue
            
            # Alternative: Use JavaScript to click the menu button
            if not menu_clicked:
                js_click_menu = """
                (function() {
                    // Find buttons with three-dot menu icon
                    var buttons = document.querySelectorAll('button');
                    for (var btn of buttons) {
                        var ariaLabel = btn.getAttribute('aria-label') || '';
                        if (ariaLabel.toLowerCase().includes('more') || 
                            ariaLabel.toLowerCase().includes('action')) {
                            // Check if it's in the shorts player area
                            var parent = btn.closest('ytd-reel-video-renderer, ytd-shorts, #shorts-container');
                            if (parent) {
                                btn.click();
                                return 'clicked';
                            }
                        }
                    }
                    
                    // Try clicking any visible menu button
                    var menuButtons = document.querySelectorAll('ytd-menu-renderer button, yt-icon-button#button');
                    for (var mb of menuButtons) {
                        if (mb.offsetParent !== null) {
                            mb.click();
                            return 'clicked menu';
                        }
                    }
                    
                    return 'not found';
                })();
                """
                result = self.browser.execute_script(js_click_menu)
                if result and 'clicked' in result:
                    menu_clicked = True
                    time.sleep(0.5)
            
            # Step 3: Click on Description option in the menu
            if menu_clicked:
                description_clicked = False
                
                # Try to find and click Description menu item
                desc_selectors = [
                    "tp-yt-paper-listbox ytd-menu-service-item-renderer",
                    "ytd-menu-service-item-renderer",
                    "tp-yt-paper-item",
                    "yt-list-item-view-model"
                ]
                
                for selector in desc_selectors:
                    try:
                        items = self.browser.driver.find_elements(By.CSS_SELECTOR, selector)
                        for item in items:
                            text = item.text.lower().strip()
                            if 'description' in text:
                                item.click()
                                description_clicked = True
                                time.sleep(0.8)
                                break
                        if description_clicked:
                            break
                    except:
                        continue
                
                # Alternative: Use JavaScript to click Description
                if not description_clicked:
                    js_click_desc = """
                    (function() {
                        // Find menu items containing "Description"
                        var items = document.querySelectorAll('ytd-menu-service-item-renderer, tp-yt-paper-item, yt-list-item-view-model');
                        for (var item of items) {
                            var text = (item.textContent || item.innerText).toLowerCase();
                            if (text.includes('description')) {
                                item.click();
                                return 'clicked description';
                            }
                        }
                        return 'not found';
                    })();
                    """
                    result = self.browser.execute_script(js_click_desc)
                    if result and 'clicked' in result:
                        description_clicked = True
                        time.sleep(0.8)
                
                # Step 4: Extract data from the Description panel (right side)
                if description_clicked:
                    metadata = self._extract_from_description_panel(metadata)
            
            # Fallback: Try to extract basic info from visible elements
            if not metadata['title']:
                metadata = self._extract_shorts_basic_info(metadata)
            
        except Exception as e:
            print(f"Error extracting Shorts metadata: {e}")
            # Try fallback extraction
            metadata = self._extract_shorts_basic_info(metadata)
        
        return metadata
    
    def _extract_from_description_panel(self, metadata: dict) -> dict:
        """Extract metadata from the Description panel on the right side"""
        import time
        
        try:
            # Wait for the panel to appear
            time.sleep(0.5)
            
            # Panel selectors for Shorts description panel
            panel_selectors = [
                "ytd-engagement-panel-section-list-renderer",
                "#engagement-panel",
                "[panel-target-id='engagement-panel-structured-description']",
                "ytd-structured-description-content-renderer"
            ]
            
            panel = None
            for selector in panel_selectors:
                try:
                    panel = self.browser.find_element(By.CSS_SELECTOR, selector)
                    if panel and panel.is_displayed():
                        break
                except:
                    continue
            
            # Extract title from panel header
            try:
                title_selectors = [
                    "ytd-engagement-panel-title-header-renderer #title",
                    "#title yt-formatted-string",
                    "h2 yt-formatted-string",
                    ".title"
                ]
                for selector in title_selectors:
                    try:
                        title_elem = self.browser.find_element(By.CSS_SELECTOR, selector)
                        if title_elem and title_elem.text.strip():
                            metadata['title'] = title_elem.text.strip()
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract stats using JavaScript - more reliable for dynamic content
            js_extract_stats = """
            (function() {
                var stats = {};
                
                // Find the description panel
                var panel = document.querySelector('ytd-engagement-panel-section-list-renderer, #engagement-panel');
                if (!panel) return stats;
                
                // Extract from factoids/stats section
                var factoids = panel.querySelectorAll('factoid-renderer, .factoid, [class*="factoid"]');
                for (var f of factoids) {
                    var text = (f.textContent || f.innerText).trim();
                    var value = f.querySelector('.factoid-value, [class*="value"]');
                    var label = f.querySelector('.factoid-label, [class*="label"]');
                    
                    if (value && label) {
                        var v = value.textContent.trim();
                        var l = label.textContent.trim().toLowerCase();
                        
                        if (l.includes('like')) stats.likes = v;
                        if (l.includes('view')) stats.views = v;
                        if (l.includes('comment')) stats.comments = v;
                    }
                }
                
                // Alternative: Try to find stats by common patterns
                var allText = panel.innerText || panel.textContent;
                var lines = allText.split('\\n').map(l => l.trim()).filter(l => l);
                
                for (var i = 0; i < lines.length; i++) {
                    var line = lines[i].toLowerCase();
                    var value = lines[i];
                    
                    // Check for number patterns with labels
                    if (line.includes('views') && !stats.views) {
                        var match = value.match(/([\\d,.]+[KMB]?)\\s*views?/i);
                        if (match) stats.views = match[1];
                    }
                    if (line.includes('likes') && !stats.likes) {
                        var match = value.match(/([\\d,.]+[KMB]?)\\s*likes?/i);
                        if (match) stats.likes = match[1];
                    }
                    
                    // Check for date patterns (Feb 24, 2024, etc.)
                    var dateMatch = value.match(/([A-Za-z]{3}\\s+\\d{1,2},?\\s*\\d{4}|\\d{4})/);
                    if (dateMatch && !stats.upload_date) {
                        stats.upload_date = dateMatch[1];
                    }
                }
                
                // Get title from panel header
                var titleElem = panel.querySelector('#title, .title, h2');
                if (titleElem) {
                    stats.title = titleElem.textContent.trim();
                }
                
                return stats;
            })();
            """
            
            stats = self.browser.execute_script(js_extract_stats)
            if stats:
                if stats.get('title') and not metadata['title']:
                    metadata['title'] = stats['title']
                if stats.get('views'):
                    metadata['views'] = stats['views']
                if stats.get('likes'):
                    metadata['likes'] = stats['likes']
                if stats.get('comments'):
                    metadata['comments'] = stats['comments']
                if stats.get('upload_date'):
                    metadata['upload_date'] = stats['upload_date']
            
            # Close the description panel by clicking X or pressing Escape
            try:
                close_btn = self.browser.find_element(By.CSS_SELECTOR, 
                    "ytd-engagement-panel-title-header-renderer #close-button, button[aria-label='Close']")
                if close_btn:
                    close_btn.click()
            except:
                # Try pressing Escape
                from selenium.webdriver.common.keys import Keys
                self.browser.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            
        except Exception as e:
            print(f"Error extracting from description panel: {e}")
        
        return metadata
    
    def _extract_shorts_basic_info(self, metadata: dict) -> dict:
        """Fallback: Extract basic info from visible Shorts elements"""
        try:
            # Extract title from video title overlay
            title_selectors = [
                "h2.ytShortsVideoTitleViewModelShortsVideoTitle span",
                "yt-formatted-string.ytShortsVideoTitleViewModelShortsVideoTitle",
                ".title.ytShortsVideoTitleViewModelShortsVideoTitle",
                "span.yt-core-attributed-string--link-inherit-color",
                "h2.title yt-formatted-string"
            ]
            
            for selector in title_selectors:
                try:
                    elem = self.browser.find_element(By.CSS_SELECTOR, selector)
                    if elem and elem.text.strip():
                        metadata['title'] = elem.text.strip()
                        break
                except:
                    continue
            
            # Extract likes from the like button
            try:
                likes_selectors = [
                    "button[aria-label*='like'] span",
                    "#like-button span",
                    "ytd-toggle-button-renderer[is-icon-button] #text",
                    "[id*='like'] .yt-spec-button-shape-next__button-text-content"
                ]
                
                for selector in likes_selectors:
                    try:
                        elem = self.browser.find_element(By.CSS_SELECTOR, selector)
                        if elem and elem.text.strip():
                            likes_text = elem.text.strip()
                            if any(c.isdigit() for c in likes_text):
                                metadata['likes'] = likes_text
                                break
                    except:
                        continue
            except:
                pass
            
            # Extract comments count
            try:
                comments_selectors = [
                    "button[aria-label*='comment'] span",
                    "#comments-button span",
                    "[id*='comment'] .yt-spec-button-shape-next__button-text-content"
                ]
                
                for selector in comments_selectors:
                    try:
                        elem = self.browser.find_element(By.CSS_SELECTOR, selector)
                        if elem and elem.text.strip():
                            comments_text = elem.text.strip()
                            if any(c.isdigit() for c in comments_text):
                                metadata['comments'] = comments_text
                                break
                    except:
                        continue
            except:
                pass
            
        except Exception as e:
            print(f"Error extracting basic Shorts info: {e}")
        
        return metadata
    
    def _extract_regular_video_metadata(self, metadata: dict) -> dict:
        """Extract metadata from regular (non-Shorts) videos"""
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
            self.set_sort_mode(config.sort_mode, config.page_load_timeout)
            
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

