#!/bin/bash

# PITV Installation Script

echo "Starting PITV installation..."

# 1. Update package list
echo "Updating package list..."
sudo apt-get update

# 2. Install system dependencies
# vlc/libvlc-dev: Required for the VLC media player
# alsa-utils: Required for volume control (amixer)
# python3-pip: Required to install Python packages
# python3-full: Required for creating virtual environments
echo "Installing system dependencies..."
sudo apt-get install -y vlc libvlc-dev alsa-utils python3-pip python3-full

# 3. Set up Virtual Environment and Install Dependencies
echo "Setting up Python virtual environment..."
# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate and install
echo "Installing Python dependencies into virtual environment..."
source venv/bin/activate
pip install -r requirements.txt

# Create a handy run script
echo "#!/bin/bash" > run.sh
echo "cd \"\$(dirname \"\$0\")\"" >> run.sh
echo "source venv/bin/activate" >> run.sh
echo "python3 main.py" >> run.sh
chmod +x run.sh

# 4. Create default directories
# Based on config.py defaults: ~/media_player_app/media
APP_DIR="$HOME/media_player_app"
MEDIA_DIR="$APP_DIR/media"

if [ ! -d "$MEDIA_DIR" ]; then
    echo "Creating media directory at $MEDIA_DIR..."
    mkdir -p "$MEDIA_DIR"
else
    echo "Media directory already exists at $MEDIA_DIR"
fi

# 5. Enable SPI (Instructional)
echo ""
echo "--------------------------------------------------------"
echo "Installation Complete!"
echo "--------------------------------------------------------"
echo "IMPORTANT: This application requires SPI to be enabled."
echo "If you haven't enabled it yet, run 'sudo raspi-config',"
echo "navigate to 'Interface Options' -> 'SPI', and enable it."
echo "--------------------------------------------------------"
echo "To start the player, run:"
echo "./run.sh"
echo "--------------------------------------------------------"