"""Configuration settings"""

# Browser settings
BROWSER_HEADLESS = False
BROWSER_TIMEOUT = 10  # seconds - default page load timeout

# Scraping settings
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 2  # seconds
DEFAULT_VIDEO_COUNT = 10
MAX_VIDEO_COUNT = 50

# YouTube URLs
YOUTUBE_BASE_URL = "https://www.youtube.com"
TRANSCRIPT_SERVICE_URL = "https://tubetranscript.com/en/"

# Excel settings
EXCEL_COLUMNS = [
    'Channel Name',
    'Video Title',
    'Video URL',
    'Upload Date',
    'Views',
    'Likes',
    'Comments',
    'Description',
    'Transcript'
]

# GUI settings
WINDOW_TITLE = "YouTube Channel Analyzer"
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700

