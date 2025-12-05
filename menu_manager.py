import os
import socket

class MenuManager:
    def __init__(self, media_manager, state_manager):
        self.media_manager = media_manager
        self.state_manager = state_manager
        self.active = False
        self.level = 0 # 0: Shows, 1: Seasons, 2: Episodes
        
        # We need to track selection at each level to generate the next list
        self.selected_show_index = 0
        self.selected_season_index = 0
        
        # Cursor position for the *current* list
        self.cursor = 0
        
        # To remember cursor position when going back
        # Stack stores cursor positions of previous levels
        self.cursor_stack = []

    def enter_menu(self):
        """Activates menu mode."""
        self.active = True
        self.level = 0
        self.cursor = 0
        self.cursor_stack = []
        print("Menu Mode: Entered")

    def exit_menu(self):
        """Deactivates menu mode."""
        self.active = False
        print("Menu Mode: Exited")
        
    def get_current_view(self):
        """Returns the title and list of items for the current menu state."""
        if not self.media_manager.shows:
            return "No Media", []
        
        # Get IP address
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()
            s.close()
        except Exception:
            ip_address = "N/A"

        if self.level == 0:
            title = "Shows"
            items = [s['name'] for s in self.media_manager.shows]
            
            # Web Server Status
            is_enabled = self.state_manager.get_state().get('web_server_enabled', True)
            if is_enabled:
                if isinstance(ip_address, tuple):
                    ip_str = ip_address[0]
                else:
                    ip_str = str(ip_address)
                items.append(f"Web: {ip_str}")
            else:
                items.append("Web: OFF")
            
            return title, items
            
        elif self.level == 1:
            show = self.media_manager.shows[self.selected_show_index]
            title = show['name']
            items = [s['name'] for s in show['seasons']]
            return title, items
            
        elif self.level == 2:
            show = self.media_manager.shows[self.selected_show_index]
            season = show['seasons'][self.selected_season_index]
            title = season['name']
            items = [os.path.basename(e) for e in season['episodes']]
            return title, items
            
        return "Error", []

    def scroll_up(self):
        """Moves the cursor up."""
        if self.cursor > 0:
            self.cursor -= 1
            print(f"Menu Up: {self.cursor}")
            
    def scroll_down(self):
        """Moves the cursor down."""
        _, items = self.get_current_view()
        if self.cursor < len(items) - 1:
            self.cursor += 1
            print(f"Menu Down: {self.cursor}")
            
    def select(self):
        """
        Selects the current item.
        Returns: 
            None (if navigating deeper into menu)
            tuple (show_idx, season_idx, episode_idx) (if an episode was selected to play)
        """
        _, items = self.get_current_view()
        if not items: return None

        if self.level == 0:
            # Check if it's the last item (Web Server Toggle)
            if self.cursor == len(items) - 1:
                 return "TOGGLE_WEB_SERVER"

            print(f"Selected Show: {items[self.cursor]}")
            self.selected_show_index = self.cursor
            self.cursor_stack.append(self.cursor)
            self.level = 1
            self.cursor = 0
            return None
            
        elif self.level == 1:
            print(f"Selected Season: {items[self.cursor]}")
            self.selected_season_index = self.cursor
            self.cursor_stack.append(self.cursor)
            self.level = 2
            self.cursor = 0
            return None
            
        elif self.level == 2:
            print(f"Selected Episode: {items[self.cursor]}")
            # Play selection!
            return (self.selected_show_index, self.selected_season_index, self.cursor)

    def back(self):
        """Goes back one level or exits menu."""
        if self.level > 0:
            self.level -= 1
            if self.cursor_stack:
                self.cursor = self.cursor_stack.pop()
            else:
                self.cursor = 0
            print("Menu Back")
        else:
            self.exit_menu()