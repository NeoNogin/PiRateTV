To Do List
Based on the current codebase, which implements a solid "TV-style" media player for Raspberry Pi with Pirate Audio, here are several feature ideas categorized by their function that would significantly enhance the project:

1. Visual & UI Enhancements
Cover Art Support:
Concept: Display a poster.jpg or folder.jpg from the Show or Season directory instead of just text on the small screen.
Implementation: Update MediaManager to scan for image files and DisplayManager to render them (scaled to 240x240) when a new show starts or while paused.
Visual Progress Bar:
Concept: Add a slim progress bar at the bottom of the playback screen to visualize time remaining.
Implementation: In display_manager.show_playback_info, draw a rectangle whose width is calculated by (current_time / total_time) * screen_width.
"TV Guide" / Menu Mode:
Concept: Currently, navigation relies on blind cycling. A menu mode would allow scrolling through a list of shows/episodes.
Implementation: Use a specific button combo (e.g., hold A+B) to enter "Menu Mode" where buttons UP/DOWN scroll through a list and A selects.
2. Advanced Playback Features
"Shuffle / Channel Surfing" Mode:
Concept: A mode that randomly plays episodes from any show, simulating a broadcast TV channel experience.
Implementation: Add a flag in MediaManager that, when active, picks a random show/season/episode instead of the sequential next_episode.
Resume-Per-Show:
Concept: Currently, state.json saves one global state. If you switch shows, you lose your spot in the previous one.
Implementation: Change state.json structure to store a dictionary of show_name: { season_idx, episode_idx, time } so you can jump back into any show exactly where you left off.
Sleep Timer:
Concept: Automatically stop playback and sleep after a set time (great for bedtime use).
Implementation: A simple countdown timer logic in the main.py loop.
3. Remote Management (Headless Quality of Life)
Web Interface (Web Remote):
Concept: A lightweight web page hosted on the Pi to control playback from your phone.
Implementation: Use a micro-framework like Flask or Bottle to expose endpoints like /play, /pause, /next.
File Upload Server:
Concept: Upload video files directly from your PC/Phone browser without needing scp or removing the SD card.
Implementation: Add a file upload route to the Web Interface.
WiFi / IP Status Screen:
Concept: Display the Pi's IP address on the Pirate Audio screen to facilitate connection.
Implementation: A specific button combo that runs hostname -I and displays the result.
4. Hardware Integrations
Battery Status (if portable):
Concept: If you use a PiSugar or UPS HAT, show a battery icon.
Implementation: Read I2C battery data and draw a small icon in DisplayManager.
I recommend starting with Cover Art Support or Resume-Per-Show as they offer the highest immediate value for a dedicated media player device.