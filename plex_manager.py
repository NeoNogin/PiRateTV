import random
from plexapi.server import PlexServer
import config

class PlexManager:
    def __init__(self):
        self.baseurl = config.PLEX_BASEURL
        self.token = config.PLEX_TOKEN
        self.server = None
        self.shows = []
        self.current_show_idx = 0
        self.current_season_idx = 0
        self.current_episode_idx = 0
        self.shuffle_enabled = False
        self.all_episodes = [] # Flattened list for shuffle
        
        try:
            self.connect()
            self.scan_media()
        except Exception as e:
            print(f"Plex Init Error: {e}")

    def connect(self):
        print(f"Connecting to Plex at {self.baseurl}...")
        self.server = PlexServer(self.baseurl, self.token)
        print(f"Connected to Plex Server: {self.server.friendlyName}")

    def scan_media(self):
        """Scans Plex TV libraries."""
        self.shows = []
        self.all_episodes = []
        
        if not self.server: 
            return

        # Find all TV Show libraries
        tv_sections = [s for s in self.server.library.sections() if s.type == 'show']
        
        if not tv_sections:
            print("No TV Show libraries found on Plex Server.")
            return

        print(f"Scanning {len(tv_sections)} TV libraries...")
        
        for section in tv_sections:
            print(f"Scanning library: {section.title}")
            # Fetch all shows
            plex_shows = section.all()
            
            for show in plex_shows:
                # Build structure: {'name': 'Show Name', 'seasons': [{'name': 'Season 1', 'episodes': [obj, obj]}]}
                seasons_list = []
                
                # Fetch seasons (Plex usually returns them sorted, but good to be safe)
                for season in show.seasons():
                    episode_list = season.episodes()
                    if episode_list:
                        seasons_list.append({
                            'name': season.title,
                            'episodes': episode_list 
                        })
                
                if seasons_list:
                    self.shows.append({
                        'name': show.title,
                        'seasons': seasons_list
                    })

        # Sort shows alphabetically
        self.shows.sort(key=lambda x: x['name'])
        
        print(f"Found {len(self.shows)} shows from Plex.")

        # Flatten library for shuffle
        self.all_episodes = []
        for show_idx, show in enumerate(self.shows):
            for season_idx, season in enumerate(show['seasons']):
                for episode_idx, _ in enumerate(season['episodes']):
                    self.all_episodes.append((show_idx, season_idx, episode_idx))

    def set_shuffle_mode(self, enabled):
        """Enables or disables shuffle mode."""
        self.shuffle_enabled = enabled
        print(f"Plex Shuffle mode set to: {enabled}")

    def get_random_episode(self):
        """Selects a random episode from the flattened library."""
        if not self.all_episodes: return
        
        show_idx, season_idx, episode_idx = random.choice(self.all_episodes)
        self.set_current_indices(show_idx, season_idx, episode_idx)
        print(f"Random Plex episode selected: {self.get_current_episode_info()}")

    def get_current_episode_obj(self):
        """Returns the actual Plex Episode object."""
        try:
            return self.shows[self.current_show_idx]['seasons'][self.current_season_idx]['episodes'][self.current_episode_idx]
        except IndexError:
            return None

    def get_current_episode_path(self):
        """Returns the direct stream URL to the current episode."""
        ep = self.get_current_episode_obj()
        if ep:
            return ep.getStreamURL()
        return None

    def get_current_episode_info(self):
        """Returns a dictionary with current show, season, episode names."""
        try:
            show_name = self.shows[self.current_show_idx]['name']
            season_name = self.shows[self.current_show_idx]['seasons'][self.current_season_idx]['name']
            ep = self.get_current_episode_obj()
            episode_name = ep.title if ep else "N/A"
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
        """Advances to the next episode."""
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
        print(f"Next Plex episode: {self.get_current_episode_info()}")

    def prev_episode(self):
        """Goes back to the previous episode."""
        if not self.shows: return

        self.current_episode_idx -= 1
        if self.current_episode_idx < 0:
            self.current_season_idx -= 1
            if self.current_season_idx < 0:
                self.current_show_idx -= 1
                if self.current_show_idx < 0:
                    self.current_show_idx = len(self.shows) - 1
                self.current_season_idx = len(self.shows[self.current_show_idx]['seasons']) - 1
            self.current_episode_idx = len(self.shows[self.current_show_idx]['seasons'][self.current_season_idx]['episodes']) - 1
        print(f"Previous Plex episode: {self.get_current_episode_info()}")

    def next_show(self):
        """Advances to the next show."""
        if not self.shows: return

        self.current_show_idx += 1
        if self.current_show_idx >= len(self.shows):
            self.current_show_idx = 0
        self.current_season_idx = 0
        self.current_episode_idx = 0
        print(f"Next Plex show: {self.get_current_episode_info()}")

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
        print(f"Set Plex indices to: {self.get_current_episode_info()}")

    def list_directory(self, sub_path=''):
        """
        Mock of list_directory to allow browsing via web interface.
        sub_path format: 'ShowName/SeasonName'
        """
        contents = {'dirs': [], 'files': []}
        
        # Root: List Shows
        if not sub_path or sub_path == '.' or sub_path == '/':
            for show in self.shows:
                contents['dirs'].append(show['name'])
            return contents, 200

        parts = [p for p in sub_path.split('/') if p and p != '.']
        
        # Level 1: Seasons in a Show
        if len(parts) == 1:
            show_name = parts[0]
            show = next((s for s in self.shows if s['name'] == show_name), None)
            if show:
                for season in show['seasons']:
                    contents['dirs'].append(season['name'])
                return contents, 200
        
        # Level 2: Episodes in a Season
        elif len(parts) == 2:
            show_name = parts[0]
            season_name = parts[1]
            show = next((s for s in self.shows if s['name'] == show_name), None)
            if show:
                season = next((s for s in show['seasons'] if s['name'] == season_name), None)
                if season:
                    for ep in season['episodes']:
                        contents['files'].append(ep.title)
                    return contents, 200

        return {"error": "Path not found"}, 404

    def find_episode_indices(self, virtual_path):
        """
        Finds indices from a virtual path string "Show/Season/EpisodeTitle".
        Returns (show_idx, season_idx, episode_idx) or None.
        """
        parts = [p for p in virtual_path.split('/') if p]
        if len(parts) != 3: return None
        
        show_name, season_name, episode_title = parts
        
        for show_idx, show in enumerate(self.shows):
            if show['name'] == show_name:
                for season_idx, season in enumerate(show['seasons']):
                    if season['name'] == season_name:
                        for episode_idx, ep in enumerate(season['episodes']):
                            if ep.title == episode_title:
                                return show_idx, season_idx, episode_idx
        return None