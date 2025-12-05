#!/bin/bash

# PITV Autostart Setup Script

echo "Configuring PITV to start on boot..."

# Detect the real user (even if run with sudo)
if [ -n "$SUDO_USER" ]; then
    CURRENT_USER=$SUDO_USER
else
    CURRENT_USER=$(whoami)
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR=$SCRIPT_DIR
SERVICE_NAME="pitv.service"

echo "Detected User: $CURRENT_USER"
echo "Detected Path: $APP_DIR"

# Check if venv exists
if [ ! -f "$APP_DIR/venv/bin/python3" ]; then
    echo "ERROR: Virtual environment not found at $APP_DIR/venv"
    echo "Please run install.sh first."
    exit 1
fi

# Fix permissions (in case installed as root)
echo "Ensuring correct file permissions..."
chown -R $CURRENT_USER:$CURRENT_USER "$APP_DIR"

# Also fix permissions for the media/state directory in the user's home
# (We assume standard /home/USERNAME structure or finding it via eval)
USER_HOME=$(eval echo "~$CURRENT_USER")
MEDIA_APP_DIR="$USER_HOME/media_player_app"
if [ -d "$MEDIA_APP_DIR" ]; then
    echo "Fixing permissions for $MEDIA_APP_DIR..."
    chown -R $CURRENT_USER:$CURRENT_USER "$MEDIA_APP_DIR"
fi

# Create the systemd service file
# We add a 10-second delay to ensure the desktop/audio system is fully up.
# We also set PYTHONUNBUFFERED so logs show up in journalctl immediately.
cat > $SERVICE_NAME <<EOF
[Unit]
Description=PITV Media Player
# Wait for more system services to be online before starting
After=network-online.target sound.target graphical.target
Wants=network-online.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$APP_DIR
Environment="HOME=${USER_HOME}"
Environment=PYTHONUNBUFFERED=1
# Add a longer delay to ensure hardware is fully ready
ExecStartPre=/bin/sleep 15
ExecStart=$APP_DIR/run.sh
Restart=always
RestartSec=10

[Install]
WantedBy=graphical.target
EOF

# Install the service
echo "Installing systemd service..."
# Move if it exists, otherwise just copy
if [ -f "/etc/systemd/system/$SERVICE_NAME" ]; then
    sudo systemctl stop $SERVICE_NAME
fi

sudo mv $SERVICE_NAME /etc/systemd/system/
sudo systemctl daemon-reload

echo "Enabling service..."
sudo systemctl enable $SERVICE_NAME

echo "Starting service..."
sudo systemctl start $SERVICE_NAME

echo "--------------------------------------------------------"
echo "Autostart setup complete!"
echo "Service installed as: /etc/systemd/system/$SERVICE_NAME"
echo ""
echo "DEBUGGING:"
echo "If it is not working, check the logs with:"
echo "sudo journalctl -u pitv.service -f"
echo "--------------------------------------------------------"