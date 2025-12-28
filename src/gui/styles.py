"""GUI styling constants"""

# Colors
COLOR_PRIMARY = "#1a73e8"
COLOR_SECONDARY = "#34a853"
COLOR_DANGER = "#ea4335"
COLOR_BACKGROUND = "#f5f5f5"
COLOR_TEXT = "#202124"
COLOR_BORDER = "#dadce0"

# Fonts
FONT_DEFAULT = ("Segoe UI", 10)
FONT_HEADING = ("Segoe UI", 12, "bold")
FONT_LABEL = ("Segoe UI", 9)
FONT_MONOSPACE = ("Consolas", 9)

# Sizes
BUTTON_HEIGHT = 35
INPUT_HEIGHT = 30
PADDING = 10
BORDER_WIDTH = 1

# Styles dictionary for easy access
STYLES = {
    'button_primary': {
        'bg': COLOR_PRIMARY,
        'fg': 'white',
        'font': FONT_DEFAULT,
        'relief': 'flat',
        'cursor': 'hand2',
        'activebackground': '#1557b0',
        'activeforeground': 'white'
    },
    'button_secondary': {
        'bg': COLOR_SECONDARY,
        'fg': 'white',
        'font': FONT_DEFAULT,
        'relief': 'flat',
        'cursor': 'hand2',
        'activebackground': '#2d8f47',
        'activeforeground': 'white'
    },
    'button_danger': {
        'bg': COLOR_DANGER,
        'fg': 'white',
        'font': FONT_DEFAULT,
        'relief': 'flat',
        'cursor': 'hand2',
        'activebackground': '#c5221f',
        'activeforeground': 'white'
    },
    'entry': {
        'font': FONT_DEFAULT,
        'relief': 'solid',
        'borderwidth': BORDER_WIDTH,
        'bg': 'white',
        'fg': COLOR_TEXT
    },
    'label': {
        'font': FONT_LABEL,
        'fg': COLOR_TEXT,
        'bg': COLOR_BACKGROUND
    },
    'label_heading': {
        'font': FONT_HEADING,
        'fg': COLOR_TEXT,
        'bg': COLOR_BACKGROUND
    }
}

