# display_manager.py
import ST7789 # Direct import for Pirate Audio display
from PIL import ImageFont, ImageDraw, Image 

import os
import time

class DisplayManager:
    def __init__(self):
        self.disp = None # Initialize to None
        self.width = 240 # Default width
        self.height = 240 # Default height

        try:
            # ST7789 display setup
            # Pirate Audio uses SPI0, CE1 (Chip Select 1) for the display.
            # 'cs' parameter in ST7789 library refers to the SPI Device Index (0 or 1), not the BCM pin.
            # CS0 = Device 0 (BCM 8), CS1 = Device 1 (BCM 7).
            self.disp = ST7789.ST7789(
                port=0,        # SPI bus 0
                cs=1,          # Chip Select Index 1 (Maps to BCM 7 / CE1 on Pirate Audio)
                dc=9,          # DC pin (BCM 9)
                backlight=13,  # Backlight pin (BCM 13)
                spi_speed_hz=62_500_000,
                rotation=0     # Rotation (0, 90, 180, 270)
            )
            
            # Initialize display
            self.disp.begin()

            self.width = self.disp.width
            self.height = self.disp.height

        except FileNotFoundError as e:
            print(f"ERROR: SPI device not found. Is SPI enabled in raspi-config? {e}")
            raise e # Re-raise to trigger service restart
        except Exception as e:
            print(f"ERROR: Could not initialize ST7789 display: {e}")
            raise e # Re-raise to trigger service restart

        # Load fonts
        font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
        self.font_path = os.path.join(font_dir, 'PixelOperator.ttf') # Ensure you have this font file
        
        try:
            self.font_small = ImageFont.truetype(self.font_path, 12)
            self.font_medium = ImageFont.truetype(self.font_path, 16)
            self.font_large = ImageFont.truetype(self.font_path, 20)
        except IOError:
            print("Warning: PixelOperator.ttf not found. Using default font.")
            self.font_small = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_large = ImageFont.load_default()
            
        # Create a blank image for drawing
        self.image = Image.new("RGB", (self.width, self.height), "black")
        self.draw = ImageDraw.Draw(self.image)
        
        self.last_update_time = time.time()
        self.screen_on = True
        self.current_rotation = 0

    def rotate_screen(self):
        """Cycles screen rotation through 0, 90, 180, 270 degrees."""
        if not self.disp: return
        
        # Cycle rotation: 0 -> 90 -> 180 -> 270 -> 0
        self.current_rotation = (self.current_rotation + 90) % 360
        
        print(f"Screen rotation set to {self.current_rotation} degrees")
        
        # Show a temporary confirmation on screen
        self.show_message(f"Rotation: {self.current_rotation}°")

    def show_message(self, message):
        """Displays a temporary full-screen message."""
        if not self.disp: return
        
        # Create a temporary image
        msg_img = Image.new("RGB", (self.width, self.height), "blue")
        draw = ImageDraw.Draw(msg_img)
        self._draw_text_centered(draw, self.height / 2 - 10, message, self.font_large)
        
        # Apply current rotation
        if self.current_rotation != 0:
            msg_img = msg_img.rotate(self.current_rotation)
            
        self.disp.display(msg_img)
        self.turn_on_backlight()
        time.sleep(0.5) # Pause briefly to let user see it

    def _draw_text_centered(self, draw, y, text, font, fill="white"):
        """Helper to draw text centered horizontally."""
        # textsize is deprecated; use textbbox (left, top, right, bottom)
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        text_width = right - left
        text_height = bottom - top
        
        x = (self.width - text_width) / 2
        draw.text((x, y), text, font=font, fill=fill)

    def show_playback_info(self, show_info, current_time_str="00:00", total_time_str="00:00", volume_percent=100, is_playing=True, is_shuffled=False):
        """Displays current playback information on the screen."""
        if not self.disp: # If display not initialized, print to console instead
            print(f"Display not available. Now playing: {show_info['show']} - {show_info['episode']} ({current_time_str}/{total_time_str}) Vol: {volume_percent}%")
            return

        if not self.screen_on: # If screen was off, turn it on
            self.turn_on_backlight()

        self.draw.rectangle((0, 0, self.width, self.height), fill="black")

        # Show Title
        self._draw_text_centered(self.draw, 10, show_info['show'], self.font_large, fill="cyan")

        # Season/Episode
        self._draw_text_centered(self.draw, 40, f"{show_info['season']}", self.font_medium)
        self._draw_text_centered(self.draw, 60, f"{show_info['episode']}", self.font_medium)

        # Playback Status
        status_text = "PLAYING" if is_playing else "PAUSED"
        if is_shuffled:
            status_text += " [SHUFFLE]"
        self._draw_text_centered(self.draw, 100, status_text, self.font_small, fill="green" if is_playing else "yellow")

        # Playback Time
        self._draw_text_centered(self.draw, 130, f"{current_time_str} / {total_time_str}", self.font_medium)

        # Volume
        self._draw_text_centered(self.draw, 160, f"Volume: {volume_percent}%", self.font_medium)

        # Apply rotation to UI if needed
        output_image = self.image
        if self.current_rotation != 0:
            output_image = self.image.rotate(self.current_rotation)

        self.disp.display(output_image)
        self.last_update_time = time.time() # Reset inactivity timer

    def display_frame(self, image):
        """Displays a full-screen image (video frame)."""
        if not self.disp: return
        if not self.screen_on: self.turn_on_backlight()
        
        # Determine if we need to resize or if it's already 240x240
        if image.size != (self.width, self.height):
             image = image.resize((self.width, self.height))
        
        # Apply rotation if needed
        if self.current_rotation != 0:
            image = image.rotate(self.current_rotation)
             
        self.disp.display(image)
        self.last_update_time = time.time()

    def show_sleep_screen(self):
        """Displays a sleep message and turns off backlight."""
        if not self.disp: return # Do nothing if display not available

        self.draw.rectangle((0, 0, self.width, self.height), fill="black")
        self._draw_text_centered(self.draw, self.height / 2 - 10, "Zzz...", self.font_large, fill="blue")
        self._draw_text_centered(self.draw, self.height / 2 + 20, "Press any button to wake", self.font_small, fill="gray")
        self.disp.display(self.image)
        self.disp.set_backlight(0) # Turn off backlight
        self.screen_on = False

    def turn_on_backlight(self):
        """Turns on the screen backlight."""
        if not self.disp: return # Do nothing if display not available

        self.disp.set_backlight(1) # Turn on backlight
        self.screen_on = True
        self.last_update_time = time.time() # Reset inactivity timer

    def turn_off_backlight(self):
        """Turns off the screen backlight."""
        if not self.disp: return # Do nothing if display not available

        self.disp.set_backlight(0) # Turn off backlight
        self.screen_on = False

    def clear_screen(self):
        """Clears the screen to black."""
        if not self.disp: return # Do nothing if display not available

        self.draw.rectangle((0, 0, self.width, self.height), fill="black")
        self.disp.display(self.image)
        self.screen_on = True # Clearing implies activity
        self.last_update_time = time.time()

    def update_screen_inactivity(self, screen_dim_timeout, screen_off_timeout):
        """Manages screen dimming/off based on inactivity."""
        if not self.disp: return # Do nothing if display not available
        if not self.screen_on: # If already off or sleeping, do nothing
            return

        elapsed = time.time() - self.last_update_time
        if elapsed > screen_off_timeout:
            self.turn_off_backlight()
        elif elapsed > screen_dim_timeout:
            # For ST7789, dimming is often simulated by turning off or just not doing anything
            # if a true dimming feature isn't available. Here, it will effectively just wait for off.
            pass

    def draw_menu(self, title, items, selected_index):
        """Draws a vertical menu list with scrolling."""
        if not self.disp: return
        if not self.screen_on: self.turn_on_backlight()

        self.draw.rectangle((0, 0, self.width, self.height), fill="black")

        # Title Bar
        self.draw.rectangle((0, 0, self.width, 30), fill="darkblue")
        self._draw_text_centered(self.draw, 5, title, self.font_medium, fill="white")

        # Menu Configuration
        MAX_VISIBLE_ITEMS = 7
        ITEM_HEIGHT = 25
        START_Y = 35

        # Determine viewport (scrolling)
        start_index = 0
        if selected_index >= MAX_VISIBLE_ITEMS:
             start_index = selected_index - MAX_VISIBLE_ITEMS + 1
        
        end_index = min(start_index + MAX_VISIBLE_ITEMS, len(items))

        y = START_Y
        for i in range(start_index, end_index):
            item_text = items[i]
            # Truncate text if too long
            # Simple truncation for now, could be improved with text width calculation
            if len(item_text) > 25:
                item_text = item_text[:22] + "..."

            if i == selected_index:
                # Highlight selection (White bar, Black text)
                self.draw.rectangle((0, y, self.width, y + ITEM_HEIGHT), fill="white")
                self.draw.text((10, y + 4), f"> {item_text}", font=self.font_medium, fill="black")
            else:
                # Normal item (Black bg, White text)
                self.draw.text((10, y + 4), item_text, font=self.font_medium, fill="white")
            y += ITEM_HEIGHT
        
        # Draw Scrollbar Indicators if list is long
        if start_index > 0:
            self._draw_text_centered(self.draw, 30, "^", self.font_small, fill="gray")
        if end_index < len(items):
             self._draw_text_centered(self.draw, self.height - 15, "v", self.font_small, fill="gray")

        # Apply rotation
        output_image = self.image
        if self.current_rotation != 0:
            output_image = self.image.rotate(self.current_rotation)

        self.disp.display(output_image)
        self.last_update_time = time.time()
