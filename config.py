# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# GPIO Pin Definitions for Pirate Audio Buttons (BCM numbering)
# As per Pirate Audio README: A=5, B=6, X=16, Y=24
# Mapped to your desired functionality:
BUTTON_TL = 5  # Top Left (A) - Volume presets
BUTTON_TR = 6  # Top Right (B) - Next/Prev Episode
BUTTON_BL = 16 # Bottom Left (X) - Toggle Sleep/Wake
BUTTON_BR = 24 # Bottom Right (Y) - Next Show

# Volume Presets (0-100%)
VOLUME_PRESETS = [0, 25, 50, 100]

# Media Root Directory
MEDIA_ROOT_DIR = os.path.join(os.path.expanduser('~'), 'media_player_app', 'media')

# State File Path (for saving/loading player state)
STATE_FILE_PATH = os.path.join(os.path.expanduser('~'), 'media_player_app', 'state.json')

# Long Press Threshold (seconds)
LONG_PRESS_THRESHOLD = 2.0

# Screen Inactivity Timers (seconds)
SCREEN_DIM_TIMEOUT = 30  # Time before backlight might dim (not directly supported by ST7789, acts as off)
SCREEN_OFF_TIMEOUT = 60  # Time before screen backlight turns completely off

# Plex Configuration
PLEX_BASEURL = os.getenv('PLEX_BASEURL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')
