#!/bin/bash
# Installs basic stuff on a remote machine
sudo apt update

# Install curl (required for following steps)
sudo apt install -y curl

# Install and configure git (required for cloning or, optionally, modifying repos)
sudo apt install -y git
# rebase per default to avoid headaches with merge commits
git config --global pull.rebase true

# Install vim (generally useful for quick file editing on the machine)
sudo apt install -y vim

# Install Docker (commands adapted from guide at https://docs.docker.com/engine/install/ubuntu/)
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
# Install the required Docker packages
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Configure better logging (with log rotation), especially to save disk space
# Define the Docker daemon configuration file path
DOCKER_DAEMON_CONFIG_FILE="/etc/docker/daemon.json"
# Create the JSON configuration
# using 'local' log drive has several advantages over the default json-file driver, including better performance and disk usage
# max-size is the maximum size of the log file before it is rotated (per default it would be unlimited)
# max-file is the maximum number of log files to retain before deleting the oldest (per default it would be unlimited)
LOG_CONFIG='{
  "log-driver": "local",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}'
# Create a backup of the existing configuration file if it exists
if [ -f "$DOCKER_DAEMON_CONFIG_FILE" ]; then
  sudo cp "$DOCKER_DAEMON_CONFIG_FILE" "$DOCKER_DAEMON_CONFIG_FILE.bak"
fi
# Store the new log config
echo "$LOG_CONFIG" | sudo tee "$DOCKER_DAEMON_CONFIG_FILE" > /dev/null
# Restart the Docker service to apply the new configuration
sudo systemctl restart docker
# user this to check the status of the Docker service - skipping here as it would cause the script to hang (requires user input)
# sudo systemctl status docker
# Print a success message
echo "Docker log driver configuration updated to 'local' with log rotation settings."

# Add the current user to the docker group to avoid needing to use sudo for every Docker command
sudo groupadd docker
sudo usermod -aG docker $USER