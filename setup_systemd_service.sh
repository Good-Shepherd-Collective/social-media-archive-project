#!/bin/bash
# Setup systemd service for the Social Media Archive Bot

echo "Setting up systemd service for Social Media Archive Bot..."

# Copy service file to systemd directory
sudo cp social-media-bot.service /etc/systemd/system/

# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable social-media-bot.service

# Start the service
sudo systemctl start social-media-bot.service

# Check status
sudo systemctl status social-media-bot.service

echo ""
echo "Service setup complete!"
echo ""
echo "Useful commands:"
echo "  Check status:  sudo systemctl status social-media-bot"
echo "  View logs:     sudo journalctl -u social-media-bot -f"
echo "  Stop bot:      sudo systemctl stop social-media-bot"
echo "  Start bot:     sudo systemctl start social-media-bot"
echo "  Restart bot:   sudo systemctl restart social-media-bot"
echo "  Disable:       sudo systemctl disable social-media-bot"
