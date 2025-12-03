# audio_manager.py
import subprocess
import config

class AudioManager:
    def __init__(self):
        self.volume_presets = config.VOLUME_PRESETS
        self.current_preset_idx = 0
        # (The actual volume will be set based on loaded state in main.py)

    def _set_volume(self, volume_percent):
        """Sets the system volume using amixer."""
        mixers = ['PCM', 'Master', 'Headphone', 'Digital', 'HDMI']
        success = False
        
        for mixer in mixers:
            try:
                subprocess.run(['amixer', '-q', 'set', mixer, f'{volume_percent}%'], check=True, capture_output=True)
                print(f"Volume set to {volume_percent}% using mixer '{mixer}'")
                success = True
                break
            except subprocess.CalledProcessError:
                continue
        
        if not success:
            print("Warning: Could not set volume. No suitable mixer control found.")
            print("Available controls (amixer scontrols):")
            try:
                subprocess.run(['amixer', 'scontrols'])
            except Exception:
                print("Could not list controls.")

    def cycle_volume_preset(self):
        """Cycles through predefined volume presets."""
        self.current_preset_idx = (self.current_preset_idx + 1) % len(self.volume_presets)
        new_volume = self.volume_presets[self.current_preset_idx]
        self._set_volume(new_volume)
        return new_volume

    def get_current_volume(self):
        """Returns the current volume percentage based on the last set preset."""
        return self.volume_presets[self.current_preset_idx]

    def set_volume_by_value(self, volume_percent):
        """Sets volume to a specific value and updates the internal preset index."""
        # Find the closest preset index to the desired volume
        if volume_percent in self.volume_presets:
            self.current_preset_idx = self.volume_presets.index(volume_percent)
        else:
            # If not an exact preset, find the closest one
            self.current_preset_idx = min(range(len(self.volume_presets)),
                                          key=lambda i: abs(self.volume_presets[i] - volume_percent))
        self._set_volume(volume_percent)
