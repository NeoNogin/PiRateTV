# audio_manager.py
import subprocess
import config

class AudioManager:
    def __init__(self):
        self.volume_presets = config.VOLUME_PRESETS
        self.current_preset_idx = 0
        self.current_volume = 100 # Default volume
        # (The actual volume will be set based on loaded state in main.py)

    def _set_volume(self, volume_percent):
        """
        Sets the system volume using amixer.
        NOTE: This is disabled as it's unreliable. Volume is now controlled
        directly by the VLC player instance in main.py. This function is
        kept for compatibility but does nothing.
        """
        pass

    def cycle_volume_preset(self):
        """Cycles through predefined volume presets."""
        self.current_preset_idx = (self.current_preset_idx + 1) % len(self.volume_presets)
        new_volume = self.volume_presets[self.current_preset_idx]
        self.current_volume = new_volume
        self._set_volume(new_volume)
        return new_volume

    def get_current_volume(self):
        """Returns the current volume percentage."""
        return self.current_volume

    def set_volume_by_value(self, volume_percent):
        """Sets volume to a specific value."""
        # Clamp the volume between 0 and 100
        self.current_volume = max(0, min(100, volume_percent))
        
        # Update the preset index to the closest preset for display consistency
        self.current_preset_idx = min(range(len(self.volume_presets)),
                                      key=lambda i: abs(self.volume_presets[i] - self.current_volume))
        
        self._set_volume(self.current_volume)
