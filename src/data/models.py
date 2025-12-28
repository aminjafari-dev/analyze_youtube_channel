"""Data models for YouTube Channel Analyzer"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class VideoData:
    """Data model for YouTube video information"""
    channel_name: str
    video_title: str
    video_url: str
    upload_date: Optional[str] = None
    views: Optional[str] = None
    likes: Optional[str] = None
    comments: Optional[str] = None
    description: Optional[str] = None
    transcript: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert VideoData to dictionary for Excel export"""
        return {
            'Channel Name': self.channel_name,
            'Video Title': self.video_title,
            'Video URL': self.video_url,
            'Upload Date': self.upload_date or '',
            'Views': self.views or '',
            'Likes': self.likes or '',
            'Comments': self.comments or '',
            'Description': self.description or '',
            'Transcript': self.transcript or ''
        }


@dataclass
class ScrapingConfig:
    """Configuration for scraping operations"""
    channel_url: str
    video_count: int = 10
    sort_mode: str = "Popular"  # Popular or Recent
    retry_attempts: int = 3
    retry_delay: int = 2  # seconds
    page_load_timeout: int = 10  # seconds - maximum wait time for page loading
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.channel_url:
            return False
        if self.video_count < 1 or self.video_count > 50:
            return False
        if self.sort_mode not in ["Popular", "Recent"]:
            return False
        return True

