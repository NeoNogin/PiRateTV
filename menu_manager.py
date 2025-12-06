import os
import socket

class MenuManager:
    def __init__(self, local_manager, plex_manager, state_manager):
        self.local_manager = local_manager
        self.plex_manager = plex_manager
        self.current_manager = local_manager # Default to local
        self.state_manager = state_manager
        self.active = False
        
        # Level 0: Source Select
        # Level 1: Shows
        # Level 2: Seasons
        # Level 3: Episodes
        self.level = 0
        
        # We need to track selection at each level
        self.selected_show_index = 0
        self.selected_season_index = 0
        
        # Cursor position for the *current* list
        self.cursor = 0
        
        # Stack stores cursor positions of previous levels
        self.cursor_stack = []

    def enter_menu(self):
        """Activates menu mode."""
        self.active = True
        self.level = 0 # Always start at Source Select
        self.cursor = 0
        self.cursor_stack = []
        print("Menu Mode: Entered")

    def exit_menu(self):
        """Deactivates menu mode."""
        self.active = False
        print("Menu Mode: Exited")
        
    def get_current_view(self):
        """Returns the title and list of items for the current menu state."""
        
        # --- Level 0: Source Selection ---
        if self.level == 0:
            title = "Select Source"
            
            # Get IP address for Web Server Status
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip_address = s.getsockname()
                s.close()
                if isinstance(ip_address, tuple):
                    ip_str = ip_address[0]
                else:
                    ip_str = str(ip_address)
            except Exception:
                ip_str = "N/A"

            is_enabled = self.state_manager.get_state().get('web_server_enabled', True)
            web_status = f"Web: {ip_str}" if is_enabled else "Web: OFF"

            items = ["Local Media", "Plex Media", web_status]
            return title, items

        # --- Content Browsing Levels ---
        # Ensure the current manager has content
        if not self.current_manager.shows:
            return "No Media", []

        if self.level == 1: # Shows
            title = "Shows"
            items = [s['name'] for s in self.current_manager.shows]
            return title, items
            
        elif self.level == 2: # Seasons
            show = self.current_manager.shows[self.selected_show_index]
            title = show['name']
            items = [s['name'] for s in show['seasons']]
            return title, items
            
        elif self.level == 3: # Episodes
            show = self.current_manager.shows[self.selected_show_index]
            season = show['seasons'][self.selected_season_index]
            title = season['name']
            
            # Plex episodes are objects, Local are strings/paths
            # We want to display the title/filename
            display_items = []
            for e in season['episodes']:
                if isinstance(e, str): # Local file path
                     display_items.append(os.path.basename(e))
                elif hasattr(e, 'title'): # Plex object
                    display_items.append(e.title)
                else:
                    display_items.append(str(e))
            
            return title, display_items
            
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
            "TOGGLE_WEB_SERVER"
            tuple (manager_type, show_idx, season_idx, episode_idx) (if an episode was selected)
        """
        _, items = self.get_current_view()
        if not items: return None

        if self.level == 0:
            # Source Selection
            if self.cursor == 0: # Local Media
                print("Selected Source: Local")
                self.current_manager = self.local_manager
                self.cursor_stack.append(self.cursor)
                self.level = 1
                self.cursor = 0
                return None
            elif self.cursor == 1: # Plex Media
                print("Selected Source: Plex")
                self.current_manager = self.plex_manager
                self.cursor_stack.append(self.cursor)
                self.level = 1
                self.cursor = 0
                return None
            elif self.cursor == 2: # Web Server
                return "TOGGLE_WEB_SERVER"

        elif self.level == 1: # Shows
            print(f"Selected Show: {items[self.cursor]}")
            self.selected_show_index = self.cursor
            self.cursor_stack.append(self.cursor)
            self.level = 2
            self.cursor = 0
            return None
            
        elif self.level == 2: # Seasons
            print(f"Selected Season: {items[self.cursor]}")
            self.selected_season_index = self.cursor
            self.cursor_stack.append(self.cursor)
            self.level = 3
            self.cursor = 0
            return None
            
        elif self.level == 3: # Episodes
            print(f"Selected Episode: {items[self.cursor]}")
            # Play selection!
            # Return which manager is active so main.py knows
            return (self.current_manager, self.selected_show_index, self.selected_season_index, self.cursor)

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