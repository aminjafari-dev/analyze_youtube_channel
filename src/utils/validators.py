"""Input validation utilities"""

import re
from urllib.parse import urlparse
from src.exceptions.custom_exceptions import ValidationError


def validate_youtube_url(url: str) -> bool:
    """Validate YouTube channel URL"""
    if not url or not isinstance(url, str):
        return False
    
    # Remove whitespace
    url = url.strip()
    
    # Check if it's a valid URL
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False
    
    # Check if it's YouTube domain
    if 'youtube.com' not in parsed.netloc and 'youtu.be' not in parsed.netloc:
        return False
    
    # Check for channel patterns
    channel_patterns = [
        r'/channel/',
        r'/c/',
        r'/user/',
        r'/@',
    ]
    
    # Check if it matches any channel pattern or is a video URL (we'll extract channel from video)
    if any(re.search(pattern, url) for pattern in channel_patterns):
        return True
    
    # Also accept video URLs (we can extract channel from them)
    if '/watch' in url or '/shorts/' in url:
        return True
    
    return False


def validate_video_count(count: int) -> bool:
    """Validate video count"""
    return isinstance(count, int) and 1 <= count <= 50


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for filesystem"""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename


def extract_channel_name_from_url(url: str) -> str:
    """Extract channel name/identifier from URL"""
    url = url.strip()
    
    # Extract from @username
    match = re.search(r'/@([^/?]+)', url)
    if match:
        return match.group(1)
    
    # Extract from /c/ or /channel/
    match = re.search(r'/(?:c|channel|user)/([^/?]+)', url)
    if match:
        return match.group(1)
    
    # Default fallback
    return "Unknown_Channel"

