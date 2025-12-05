# main.py (Updated for gpiozero and stability)
from gpiozero import Button, HoldMixin
from signal import pause
import time
import os
import vlc
import atexit
import ctypes
from PIL import Image

import config
from media_manager import MediaManager
from display_manager import DisplayManager
from audio_manager import AudioManager
from state_manager import StateManager
from menu_manager import MenuManager
from web_server import start_web_server_thread

# --- Ensure Media Directory Exists ---
os.makedirs(config.MEDIA_ROOT_DIR, exist_ok=True)

# --- Global Application State & Managers ---
vlc_instance = vlc.Instance("--aout=alsa", "--quiet", "--no-video-title-show", "--no-xlib")
media_player = vlc_instance.media_player_new()
event_manager = media_player.event_manager()

media_manager = MediaManager(config.MEDIA_ROOT_DIR)
display_manager = DisplayManager()
audio_manager = AudioManager()
state_manager = StateManager(config.STATE_FILE_PATH)
menu_manager = MenuManager(media_manager)

is_sleeping = False
is_playing = False
media_ended_flag = False

# --- Video Buffer Setup ---
VIDEO_WIDTH = 240
VIDEO_HEIGHT = 240
# RV24 format is 3 bytes per pixel (R, G, B)
VIDEO_BUFFER_SIZE = VIDEO_WIDTH * VIDEO_HEIGHT * 3
video_buffer = ctypes.create_string_buffer(VIDEO_BUFFER_SIZE)

# --- VLC Video Callbacks ---
@vlc.CallbackDecorators.VideoLockCb
def lock_cb(opaque, planes):
    # Tell VLC to write into our pre-allocated buffer
    planes[0] = ctypes.cast(video_buffer, ctypes.c_void_p)

@vlc.CallbackDecorators.VideoUnlockCb
def unlock_cb(opaque, picture, planes):
    # Data has been written, we can process it now if needed,
    # but we usually handle display in the display callback.
    pass

@vlc.CallbackDecorators.VideoDisplayCb
def display_cb(opaque, picture):
    """Called by VLC when a frame is ready to be displayed."""
    if is_sleeping: return
    if menu_manager.active: return

    # Create a PIL Image from the raw buffer data
    # 'RV24' corresponds to RGB
    try:
        img = Image.frombytes("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), video_buffer.raw, "raw", "RGB")
        
        display_manager.display_frame(img)
    except Exception as e:
        print(f"Frame error: {e}")

# --- Button Setup (using gpiozero) ---
# Button with hold capability for Rewind (Long) / Volume (Short)
button_tl = Button(config.BUTTON_TL, pull_up=True, bounce_time=0.05, hold_time=config.LONG_PRESS_THRESHOLD)
# Button with hold capability for previous episode
button_tr = Button(config.BUTTON_TR, pull_up=True, bounce_time=0.05, hold_time=config.LONG_PRESS_THRESHOLD)
# Button with hold capability for rotation (Long) / Sleep (Short)
button_bl = Button(config.BUTTON_BL, pull_up=True, bounce_time=0.05, hold_time=config.LONG_PRESS_THRESHOLD)
# Button with hold capability for fast forward
button_br = Button(config.BUTTON_BR, pull_up=True, bounce_time=0.05, hold_time=config.LONG_PRESS_THRESHOLD)

# --- Core Functions ---
def save_current_state():
    """Saves the current playback state to a file."""
    playback_pos = media_player.get_time() / 1000.0 if media_player.is_playing() else 0
    state_manager.save_state(
        current_show_idx=media_manager.current_show_idx,
        current_season_idx=media_manager.current_season_idx,
        current_episode_idx=media_manager.current_episode_idx,
        playback_position=playback_pos,
        volume_percent=audio_manager.get_current_volume(),
        is_sleeping=is_sleeping,
        shuffle_enabled=media_manager.shuffle_enabled
    )
    print(f"State saved at position: {playback_pos:.2f}s")

def start_playback(episode_path, resume_position_s=0):
    """Starts or resumes playback of a given media file."""
    global is_playing
    if not episode_path or not os.path.exists(episode_path):
        print(f"Error: Episode not found at {episode_path}")
        display_manager.show_playback_info(media_manager.get_current_episode_info(), "Error", "File Not Found", audio_manager.get_current_volume(), False)
        is_playing = False
        return

    print(f"Starting playback: {os.path.basename(episode_path)}")
    media = vlc_instance.media_new(episode_path)
    media_player.set_media(media)
    media_player.play()
    is_playing = True

    # It takes a moment for the media to be parsed; we wait briefly before setting time
    time.sleep(0.5)
    if resume_position_s > 0:
        media_player.set_time(int(resume_position_s * 1000))

    update_display()

def stop_playback():
    """Stops the VLC media player."""
    global is_playing
    if media_player.is_playing():
        media_player.stop()
    is_playing = False
    print("Playback stopped.")

def update_display():
    """Updates the screen with the current playback info."""
    if is_sleeping:
        return

    if menu_manager.active:
        title, items = menu_manager.get_current_view()
        display_manager.draw_menu(title, items, menu_manager.cursor)
    else:
        current_pos_s = media_player.get_time() / 1000.0
        total_duration_s = media_player.get_length() / 1000.0
        
        display_manager.show_playback_info(
            show_info=media_manager.get_current_episode_info(),
            current_time_str=format_time(current_pos_s),
            total_time_str=format_time(total_duration_s),
            volume_percent=audio_manager.get_current_volume(),
            is_playing=media_player.is_playing(),
            is_shuffled=media_manager.shuffle_enabled
        )

def format_time(seconds):
    """Formats seconds into a MM:SS string."""
    if seconds is None or seconds < 0: return "00:00"
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"

# --- Button Handlers ---
def handle_next_episode():
    if is_sleeping: wake_up(); return
    
    if menu_manager.active:
        # Menu Mode: Select / Enter
        print("Menu: Select")
        result = menu_manager.select()
        if result:
            # Play selection
            show_idx, season_idx, episode_idx = result
            print(f"Menu: Playing selection {show_idx}-{season_idx}-{episode_idx}")
            media_manager.set_current_indices(show_idx, season_idx, episode_idx)
            menu_manager.exit_menu()
            stop_playback()
            start_playback(media_manager.get_current_episode_path())
            save_current_state()
        else:
            # Just navigating deeper
            update_display()
    else:
        # Playback Mode: Next Episode
        print("Button: Next Episode")
        stop_playback()
        media_manager.next_episode()
        save_current_state()
        start_playback(media_manager.get_current_episode_path())

def handle_prev_episode():
    if is_sleeping: wake_up(); return
    
    if menu_manager.active:
        # Menu Mode: UP
        menu_manager.scroll_up()
        update_display()
    else:
        # Playback Mode: Previous Episode
        print("Button: Previous Episode")
        stop_playback()
        media_manager.prev_episode()
        save_current_state()
        start_playback(media_manager.get_current_episode_path())

def handle_next_show():
    if is_sleeping: wake_up(); return
    
    if menu_manager.active:
        # Menu Mode: Back
        menu_manager.back()
        # If we exited menu mode (cancelled), resume playback
        if not menu_manager.active:
             if not media_player.is_playing():
                 print("Menu exited. Resuming playback...")
                 media_player.play()
        update_display()
    else:
        # Playback Mode: Next Show
        print("Button: Next Show")
        stop_playback()
        media_manager.next_show()
        save_current_state()
        start_playback(media_manager.get_current_episode_path())

def handle_fast_forward():
    if is_sleeping: wake_up(); return
    print("Button: Fast Forward (30s)")
    if media_player.is_playing():
        length = media_player.get_length()
        current_time = media_player.get_time()
        # Skip 30 seconds (30000 ms)
        new_time = current_time + 30000
        
        if new_time > length:
            new_time = length - 1000 # Go to 1 second before end
        
        media_player.set_time(new_time)
        print(f"Seeked to {new_time/1000.0}s")

def handle_rewind():
    if is_sleeping: wake_up(); return
    
    if menu_manager.active:
        # In menu, Long Press A could duplicate UP or do nothing.
        # Let's keep it simple: UP
        menu_manager.scroll_up()
        update_display()
    else:
        # Playback Mode: Rewind
        print("Button: Rewind (30s)")
        if media_player.is_playing():
            current_time = media_player.get_time()
            # Rewind 30 seconds (30000 ms)
            new_time = current_time - 30000
            
            if new_time < 0:
                new_time = 0
            
            media_player.set_time(new_time)
            print(f"Seeked to {new_time/1000.0}s")

def handle_cycle_volume():
    if is_sleeping: wake_up(); return
    print("Button: Cycle Volume")
    new_volume = audio_manager.cycle_volume_preset()
    media_player.audio_set_volume(new_volume)
    update_display()

def handle_toggle_shuffle():
    if is_sleeping: wake_up(); return
    
    if menu_manager.active:
        # Menu Mode: Down
        menu_manager.scroll_down()
        update_display()
    else:
        # Playback Mode: Toggle Shuffle
        new_state = not media_manager.shuffle_enabled
        media_manager.set_shuffle_mode(new_state)
        print(f"Button: Toggle Shuffle -> {new_state}")
        update_display()

def enter_menu_mode():
    if is_sleeping: wake_up(); return
    print("Entering Menu Mode")
    if media_player.is_playing():
        print("Pausing playback for menu...")
        media_player.pause()
    menu_manager.enter_menu()
    update_display()

def handle_sleep_wake():
    global is_sleeping
    if is_sleeping:
        wake_up()
    else:
        go_to_sleep()

def handle_rotate_screen():
    if is_sleeping: wake_up(); return
    print("Button: Rotate Screen")
    display_manager.rotate_screen()
    # If paused/menu, update display to show rotation immediately
    if not media_player.is_playing():
        update_display()

def go_to_sleep():
    global is_sleeping
    print("Going to sleep...")
    is_sleeping = True
    save_current_state()
    stop_playback()
    display_manager.show_sleep_screen()

def wake_up():
    global is_sleeping
    print("Waking up...")
    is_sleeping = False
    display_manager.reinit_display()
    # Reload state to resume correctly
    state = state_manager.load_state()
    media_manager.set_current_indices(
        state['current_show_idx'],
        state['current_season_idx'],
        state['current_episode_idx']
    )
    audio_manager.set_volume_by_value(state['volume_percent'])
    media_player.audio_set_volume(state['volume_percent'])
    start_playback(media_manager.get_current_episode_path(), state['playback_position'])

# --- VLC Event Callback ---
def handle_media_ended(event):
    """Called by VLC when the current media finishes playing."""
    # We set a flag here instead of calling logic directly,
    # to avoid threading issues with VLC callbacks.
    global media_ended_flag
    print("VLC Event: Media Ended.")
    media_ended_flag = True

# --- System Setup & Teardown ---
def setup():
    """Initializes the application, loads state, and assigns button actions."""
    font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
    os.makedirs(font_dir, exist_ok=True)
    
    # Register cleanup function to be called on exit
    atexit.register(cleanup)
    
    # Assign button handlers
    
    # Button State Tracker (to differentiate short press from long hold)
    button_states = {
        'tl_held': False,
        'bl_held': False,
        'br_held': False
    }

    # Button State Tracker
    button_states = {
        'tl_held': False,
        'tr_held': False,
        'bl_held': False,
        'br_held': False,
        'bl_action_handled': False, # To track if X was used in combo
        'br_used_as_modifier': False # To track if Y was used as modifier
    }

    # --- Top Left (A): Prev Episode (Short) / Menu (Long) ---
    def on_tl_held():
        button_states['tl_held'] = True
        if menu_manager.active:
            # If already in menu, long press acts as fast scroll up or just regular up
            handle_prev_episode() # Maps to UP in menu
        else:
            enter_menu_mode() # REPLACES Rewind
        
    def on_tl_released():
        if not button_states['tl_held']:
            handle_prev_episode()
        button_states['tl_held'] = False
        
    button_tl.when_held = on_tl_held
    button_tl.when_released = on_tl_released

    # --- Top Right (B): Next Episode (Short) / Fast Forward (Long) ---
    def on_tr_held():
        button_states['tr_held'] = True
        handle_fast_forward()

    def on_tr_released():
        if not button_states['tr_held']:
            handle_next_episode()
        button_states['tr_held'] = False

    button_tr.when_held = on_tr_held
    button_tr.when_released = on_tr_released
    # Clear old simple handlers if any
    button_tr.when_pressed = None

    # --- Bottom Left (X): Shuffle (Short) / Sleep (Long) / Volume (If Y held) ---
    def on_bl_pressed():
        # Check if Y is held down to trigger Combo
        if button_br.is_pressed:
            print("Combo: Y held + X pressed -> Cycle Volume")
            button_states['br_used_as_modifier'] = True
            handle_cycle_volume()
            # Mark action as handled so release doesn't trigger shuffle
            button_states['bl_action_handled'] = True
        else:
            button_states['bl_action_handled'] = False

    def on_bl_held():
        if button_states.get('bl_action_handled', False): return
        
        button_states['bl_held'] = True
        handle_sleep_wake()

    def on_bl_released():
        # If action was handled (e.g. combo), reset flag and do nothing
        if button_states.get('bl_action_handled', False):
            button_states['bl_action_handled'] = False
            return

        if not button_states['bl_held']:
            handle_toggle_shuffle() # Short press is now Shuffle
        button_states['bl_held'] = False

    button_bl.when_pressed = on_bl_pressed
    button_bl.when_held = on_bl_held
    button_bl.when_released = on_bl_released
    
    # --- Bottom Right (Y): Next Show (Short) / Rotate (Long) / Modifier ---
    def on_br_held():
        # Only trigger if we haven't already triggered for this hold press
        if not button_states['br_held']:
            button_states['br_held'] = True
            handle_rotate_screen()

    def on_br_released():
        # If used as modifier, do NOT trigger Next Show
        if not button_states['br_held'] and not button_states.get('br_used_as_modifier', False):
            handle_next_show()
        
        button_states['br_held'] = False
        button_states['br_used_as_modifier'] = False # Reset modifier flag

    button_br.when_held = on_br_held
    button_br.when_released = on_br_released

    # Attach VLC event listener
    event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, handle_media_ended)
    
    # --- Setup VLC Video Output to Memory ---
    # Register the callbacks
    media_player.video_set_callbacks(lock_cb, unlock_cb, display_cb, None)
    # Set the format (RV24 = RGB 24-bit, 240x240, Pitch = Width * 3)
    media_player.video_set_format("RV24", VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_WIDTH * 3)

    # Load initial state
    initial_state = state_manager.get_state()
    media_manager.set_current_indices(
        initial_state['current_show_idx'],
        initial_state['current_season_idx'],
        initial_state['current_episode_idx']
    )
    audio_manager.set_volume_by_value(initial_state['volume_percent'])
    media_player.audio_set_volume(initial_state['volume_percent'])
    
    if 'shuffle_enabled' in initial_state:
        media_manager.set_shuffle_mode(initial_state['shuffle_enabled'])

    # Start playback based on loaded state
    if initial_state.get('is_sleeping', False):
        go_to_sleep()
    else:
        print("Resuming playback from last state...")
        episode_path = media_manager.get_current_episode_path()
        if episode_path:
            start_playback(episode_path, initial_state['playback_position'])
        else:
            print("No media found to play on startup.")
            display_manager.show_playback_info(media_manager.get_current_episode_info(), "N/A", "N/A", audio_manager.get_current_volume(), False)

def cleanup():
    """A cleanup function to be called on application exit."""
    print("Cleaning up and shutting down...")
    if not is_sleeping:
        save_current_state()
    if media_player:
        media_player.stop()
        media_player.release()
    if vlc_instance:
        vlc_instance.release()
    display_manager.clear_screen()
    display_manager.turn_off_backlight()
    print("Application exited.")

# --- Main Application Class ---
class MainApp:
    def __init__(self):
        # Your existing global variables become instance variables
        self.vlc_instance = vlc_instance
        self.media_player = media_player
        self.event_manager = event_manager
        self.media_manager = media_manager
        self.display_manager = display_manager
        self.audio_manager = audio_manager
        self.state_manager = state_manager
        self.menu_manager = menu_manager
        self.is_sleeping = is_sleeping
        self.is_playing = is_playing
        self.media_ended_flag = media_ended_flag
        self.media_ended_flag = media_ended_flag
        
        # Start the web server in a separate thread
        start_web_server_thread(self)

    def play_pause(self):
        """Toggles play/pause state of the media player."""
        if self.media_player.is_playing():
            self.media_player.pause()
        else:
            self.media_player.play()

    def next_episode(self):
        """Handles the logic for playing the next episode."""
        handle_next_episode()

    def prev_episode(self):
        """Handles the logic for playing the previous episode."""
        handle_prev_episode()

    def next_show(self):
        """Handles the logic for playing the next show."""
        handle_next_show()

    def rewind(self):
        """Handles the logic for rewinding."""
        handle_rewind()

    def fast_forward(self):
        """Handles the logic for fast forwarding."""
        handle_fast_forward()

    def toggle_shuffle(self):
        """Handles the logic for toggling shuffle."""
        handle_toggle_shuffle()

    def rotate_screen(self):
        """Handles the logic for rotating the screen."""
        handle_rotate_screen()

    def volume_up(self):
        """Increases the volume."""
        new_volume = self.audio_manager.volume_up()
        self.media_player.audio_set_volume(new_volume)
        return new_volume

    def volume_down(self):
        """Decreases the volume."""
        new_volume = self.audio_manager.volume_down()
        self.media_player.audio_set_volume(new_volume)
        return new_volume

    def get_current_video_path(self):
        """Returns the path and filename of the current video for streaming."""
        episode_path = self.media_manager.get_current_episode_path()
        if episode_path and os.path.exists(episode_path):
            directory, filename = os.path.split(episode_path)
            return directory, filename
        return None, None

    def is_safe_path(self, path_to_check):
        """Checks if a given path is safely within the media root directory."""
        base_path = os.path.abspath(self.media_manager.media_root_dir)
        check_path = os.path.abspath(os.path.join(base_path, path_to_check))
        return os.path.commonpath([base_path]) == os.path.commonpath([base_path, check_path])

    def play_media(self, file_path):
        """Plays a specific media file."""
        # This assumes the file_path is a full, safe path to a media file
        stop_playback()
        # You might need a way to figure out show/season/episode from path
        # For now, let's just play it directly.
        start_playback(os.path.join(self.media_manager.media_root_dir, file_path))

    def handle_upload(self, file_stream, filename):
        """Handles file uploads from the web interface, preserving directory structure."""
        from werkzeug.utils import secure_filename

        # Sanitize each path component to prevent traversal attacks but keep directory structure.
        # Browsers use '/' as a separator in webkitRelativePath.
        path_parts = filename.split('/')
        safe_parts = [secure_filename(part) for part in path_parts]
        safe_relative_path = os.path.join(*safe_parts)

        # Double-check that the resulting path is not trying to escape the media root.
        if not self.is_safe_path(safe_relative_path):
            print(f"Error: Unsafe path detected during upload: {safe_relative_path}")
            return

        save_path = os.path.join(self.media_manager.media_root_dir, safe_relative_path)

        try:
            # Create parent directories if they don't exist
            directory = os.path.dirname(save_path)
            os.makedirs(directory, exist_ok=True)
            
            # Write the file
            with open(save_path, 'wb') as f:
                f.write(file_stream.read())
            print(f"File uploaded successfully to {save_path}")
            
            # After upload, rescan the media library
            self.media_manager.scan_media()
        except Exception as e:
            print(f"Error saving uploaded file: {e}")

# --- Main Loop ---
if __name__ == "__main__":
    try:
        main_app = MainApp()
        setup()
        # The main loop now just keeps the script alive and periodically updates the display
        while True:
            # Check if media finished playing (signaled by callback)
            if media_ended_flag:
                print("Main Loop: Handling Media End...")
                media_ended_flag = False
                time.sleep(0.5) # Short pause
                media_manager.next_episode()
                save_current_state()
                start_playback(media_manager.get_current_episode_path())

            time.sleep(0.1) # Update interval
    except KeyboardInterrupt:
        print("\nCtrl+C pressed. Exiting.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup()