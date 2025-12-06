# media_manager.py
import os
import glob
import random

class MediaManager:
    def __init__(self, media_root_dir):
        self.media_root_dir = media_root_dir
        self.shows = []
        self.current_show_idx = 0
        self.current_season_idx = 0
        self.current_episode_idx = 0
        self.shuffle_enabled = False
        self.all_episodes = []
        self.scan_media()

    def scan_media(self):
        """Scans the media_root_dir for shows, seasons, and episodes."""
        self.shows = []
        show_dirs = sorted([d for d in os.listdir(self.media_root_dir) if os.path.isdir(os.path.join(self.media_root_dir, d))])

        for show_name in show_dirs:
            show_path = os.path.join(self.media_root_dir, show_name)
            seasons = []
            season_dirs = sorted([d for d in os.listdir(show_path) if os.path.isdir(os.path.join(show_path, d))])

            for season_name in season_dirs:
                season_path = os.path.join(show_path, season_name)
                # Find common video file extensions (case-insensitive)
                episodes = sorted(glob.glob(os.path.join(season_path, '*.[mM][pP]4')) +
                                  glob.glob(os.path.join(season_path, '*.[mM][kK][vV]')) +
                                  glob.glob(os.path.join(season_path, '*.[aA][vV][iI]'))) # Add more as needed
                if episodes: # Only add season if it contains episodes
                    seasons.append({'name': season_name, 'episodes': episodes})
            if seasons: # Only add show if it contains seasons
                self.shows.append({'name': show_name, 'seasons': seasons})

        if not self.shows:
            print(f"Warning: No media found in {self.media_root_dir}")

        # Flatten library for shuffle
        self.all_episodes = []
        for show_idx, show in enumerate(self.shows):
            for season_idx, season in enumerate(show['seasons']):
                for episode_idx, _ in enumerate(season['episodes']):
                    self.all_episodes.append((show_idx, season_idx, episode_idx))

    def set_shuffle_mode(self, enabled):
        """Enables or disables shuffle mode."""
        self.shuffle_enabled = enabled
        print(f"Shuffle mode set to: {enabled}")

    def get_random_episode(self):
        """Selects a random episode from the flattened library."""
        if not self.all_episodes: return
        
        show_idx, season_idx, episode_idx = random.choice(self.all_episodes)
        self.set_current_indices(show_idx, season_idx, episode_idx)
        print(f"Random episode selected: {self.get_current_episode_info()}")

    def get_current_episode_path(self):
        """Returns the full path to the current episode."""
        try:
            return self.shows[self.current_show_idx]['seasons'][self.current_season_idx]['episodes'][self.current_episode_idx]
        except IndexError:
            return None

    def get_current_episode_info(self):
        """Returns a dictionary with current show, season, episode names."""
        try:
            show_name = self.shows[self.current_show_idx]['name']
            season_name = self.shows[self.current_show_idx]['seasons'][self.current_season_idx]['name']
            episode_path = self.get_current_episode_path()
            episode_name = os.path.basename(episode_path) if episode_path else "N/A"
            return {
                'show': show_name,
                'season': season_name,
                'episode': episode_name
            }
        except IndexError:
            return {
                'show': "No Show",
                'season': "No Season",
                'episode': "No Episode"
            }

    def next_episode(self):
        """Advances to the next episode, or next season/show if at end."""
        if not self.shows: return
        
        if self.shuffle_enabled:
            self.get_random_episode()
            return

        self.current_episode_idx += 1
        current_season_episodes = self.shows[self.current_show_idx]['seasons'][self.current_season_idx]['episodes']
        
        if self.current_episode_idx >= len(current_season_episodes):
            self.current_episode_idx = 0
            self.current_season_idx += 1
            
            if self.current_season_idx >= len(self.shows[self.current_show_idx]['seasons']):
                self.current_season_idx = 0
                self.current_show_idx += 1
                
                if self.current_show_idx >= len(self.shows):
                    self.current_show_idx = 0 # Loop back to first show
        print(f"Next episode: {self.get_current_episode_info()}")

    def prev_episode(self):
        """Goes back to the previous episode, or previous season/show if at beginning."""
        if not self.shows: return

        self.current_episode_idx -= 1
        if self.current_episode_idx < 0:
            self.current_season_idx -= 1
            if self.current_season_idx < 0:
                self.current_show_idx -= 1
                if self.current_show_idx < 0:
                    self.current_show_idx = len(self.shows) - 1 # Loop back to last show
                self.current_season_idx = len(self.shows[self.current_show_idx]['seasons']) - 1 # Last season of current show
            self.current_episode_idx = len(self.shows[self.current_show_idx]['seasons'][self.current_season_idx]['episodes']) - 1
        print(f"Previous episode: {self.get_current_episode_info()}")

    def next_show(self):
        """Advances to the next show, looping if at end."""
        if not self.shows: return

        self.current_show_idx += 1
        if self.current_show_idx >= len(self.shows):
            self.current_show_idx = 0
        self.current_season_idx = 0
        self.current_episode_idx = 0
        print(f"Next show: {self.get_current_episode_info()}")

    def find_episode_indices(self, file_path):
        """
        Given a file path (relative to media_root_dir), finds the
        (show_idx, season_idx, episode_idx) that corresponds to it.
        Returns None if not found.
        """
        abs_path = os.path.abspath(os.path.join(self.media_root_dir, file_path))
        
        for show_idx, show in enumerate(self.shows):
            for season_idx, season in enumerate(show['seasons']):
                for episode_idx, episode_abs_path in enumerate(season['episodes']):
                    # 'episode_abs_path' from glob is already absolute or relative depending on glob usage.
                    # In scan_media, we used os.path.join(self.media_root_dir, ...), so it should be absolute-ish.
                    # Let's compare abspaths to be safe.
                    if os.path.abspath(episode_abs_path) == abs_path:
                        return show_idx, season_idx, episode_idx
        return None

    def set_current_indices(self, show_idx, season_idx, episode_idx):
        """Sets the current playback indices, clamping to valid ranges."""
        if not self.shows: return

        if 0 <= show_idx < len(self.shows):
            self.current_show_idx = show_idx
            if 0 <= season_idx < len(self.shows[show_idx]['seasons']):
                self.current_season_idx = season_idx
                if 0 <= episode_idx < len(self.shows[show_idx]['seasons'][season_idx]['episodes']):
                    self.current_episode_idx = episode_idx
                else:
                    self.current_episode_idx = 0
            else:
                self.current_season_idx = 0
                self.current_episode_idx = 0
        else:
            self.current_show_idx = 0
            self.current_season_idx = 0
            self.current_episode_idx = 0
        print(f"Set indices to: {self.get_current_episode_info()}")

    def list_directory(self, sub_path=''):
        """Lists the contents of a directory within the media root."""
        # Security: Prevent directory traversal attacks
        base_path = os.path.abspath(self.media_root_dir)
        target_path = os.path.abspath(os.path.join(base_path, sub_path))

        if not target_path.startswith(base_path):
            return {"error": "Access denied"}, 403

        try:
            items = os.listdir(target_path)
            contents = {'dirs': [], 'files': []}
            for item in sorted(items):
                item_path = os.path.join(target_path, item)
                if os.path.isdir(item_path):
                    contents['dirs'].append(item)
                else:
                    contents['files'].append(item)
            return contents, 200
        except FileNotFoundError:
            return {"error": "Directory not found"}, 404
        except Exception as e:
            return {"error": str(e)}, 500
