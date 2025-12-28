"""Custom exceptions for the YouTube Channel Analyzer"""


class ScrapingError(Exception):
    """Base exception for scraping errors"""
    pass


class YouTubeScrapingError(ScrapingError):
    """Exception raised when YouTube scraping fails"""
    pass


class TranscriptScrapingError(ScrapingError):
    """Exception raised when transcript scraping fails"""
    pass


class BrowserError(Exception):
    """Exception raised when browser operations fail"""
    pass


class ExcelError(Exception):
    """Exception raised when Excel operations fail"""
    pass


class ValidationError(Exception):
    """Exception raised when input validation fails"""
    pass

