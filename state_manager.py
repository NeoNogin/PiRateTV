# state_manager.py
import json
import os
import config

class StateManager:
    def __init__(self, state_file_path):
        self.state_file_path = state_file_path
        self.default_state = {
            'current_show_idx': 0,
            'current_season_idx': 0,
            'current_episode_idx': 0,
            'playback_position': 0, # in seconds
            'volume_percent': config.VOLUME_PRESETS[-1], # Default to max preset volume
            'is_sleeping': False,
            'shuffle_enabled': False
        }
        self.state = self.load_state()

    def load_state(self):
        """Loads the player state from the JSON file."""
        if os.path.exists(self.state_file_path):
            try:
                with open(self.state_file_path, 'r') as f:
                    loaded_state = json.load(f)
                    # Merge with default state to handle new fields in future
                    return {**self.default_state, **loaded_state}
            except json.JSONDecodeError:
                print(f"Error decoding state file '{self.state_file_path}', starting with default state.")
                return self.default_state
            except IOError as e:
                print(f"Error reading state file '{self.state_file_path}': {e}, starting with default state.")
                return self.default_state
        print("No state file found, starting with default state.")
        return self.default_state

    def save_state(self, current_show_idx, current_season_idx, current_episode_idx,
                   playback_position, volume_percent, is_sleeping, shuffle_enabled):
        """Saves the current player state to the JSON file."""
        self.state = {
            'current_show_idx': current_show_idx,
            'current_season_idx': current_season_idx,
            'current_episode_idx': current_episode_idx,
            'playback_position': playback_position,
            'volume_percent': volume_percent,
            'is_sleeping': is_sleeping,
            'shuffle_enabled': shuffle_enabled
        }
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.state_file_path), exist_ok=True)
            with open(self.state_file_path, 'w') as f:
                json.dump(self.state, f, indent=4)
            print("State saved.")
        except IOError as e:
            print(f"Error saving state file '{self.state_file_path}': {e}")

    def get_state(self):
        """Returns the current loaded state."""
        return self.state
