# ObscuR - Dark Web Cyber Threat Intelligence Tool

## Context

ObscuR is a specialized tool designed for **Cyber Threat Intelligence (CTI)** with a focus on malware surveillance across dark web hidden services. This tool enables security professionals to monitor, analyze, and structure cyber threats.

### The Challenge

The dark web represents a critical but challenging source of threat intelligence, accessible only through specialized tools like the **Tor** network. Forums, marketplaces, and hidden services on the dark web often contain early indicators of emerging cyber threats, including:

- New malware variants and families
- Zero-day exploits
- Attack techniques and tactics
- Data breaches and stolen information

### Project Objectives

1. **Hidden Service Monitoring**: Securely access and monitor .onion sites containing valuable threat data
2. **Automated Change Detection**: Compare versions of web pages over time to identify new threats
3. **Notification System**: Alert users to significant changes through structured RSS feeds
4. **Information Extraction**: Use NLP techniques to extract and categorize threat intelligence
5. **Standardized Intelligence**: Format findings using recognized threat intelligence standards for maximum interoperability

### Key Features

- **Dark Web Monitoring**: Secure minitoring of Tor hidden services
- **Change Detection**: Automated comparison of content across time 
- **Notification System**: RSS feeds to track updates and changes
- **Information Extraction**: NLP-based analysis of collected content
- **STIX Integration**: Standardized threat intelligence formatting
- **Containerized Deployment**: Secure, isolated execution environment

## Quick Start

### Using Docker (Recommended)

The easiest way to deploy ObscuR is using Docker:

```sh
# Clone the repository
git clone https://github.com/yourusername/obscur.git
cd obscur

# Create your config file from the example
cp .env.example .env
# Edit the .env file with your configuration
nano .env

# Start the required services
docker compose -f docker-compose.yml up -d

# Build the ObscuR container
docker build -f obscur.Dockerfile -t obscur .

# Run the tool
./start.sh
```

## Configuration

ObscuR uses YAML-based configuration files to define monitoring targets. For detailed configuration options:

[→ View Configuration Documentation](config/README.md)

## Architecture

ObscuR consists of several interconnected services:

### Core Services

- **Tor Proxy**: Provides secure access to .onion sites (port 9050/9051)
- **RSS Web Server**: Delivers notification feeds (port 8000)
- **MinIO Object Storage**: Stores extracted data and screenshots (ports 9000/9001)
- **ObscuR Container**: Main application running inside the Tor proxy network

### Network Configuration

The ObscuR container must run within the same network as the Tor proxy to access hidden services and MinIO:

```yaml
# Docker networking configuration
docker run \
  --network container:obscur-tor \  # Share network with the Tor container
  # ...other parameters
  "obscur"
```

## Periodic Execution

### Using Cron

To schedule ObscuR to run at specific intervals:

```sh
# Edit crontab
crontab -e

# Add a line to run daily at 2 AM
0 2 * * * cd /path/to/obscur && ./start.sh >> /path/to/obscur/cron.log 2>&1
```

### Using Systemd

For more robust scheduling with systemd:

1. Create a service file at `/etc/systemd/system/obscur.service`:

```ini
[Unit]
Description=ObscuR Dark Web CTI Tool
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=/path/to/obscur
ExecStartPre=/usr/bin/docker compose -f docker-compose.yml up -d
ExecStart=/path/to/obscur/start.sh
User=your-username
Group=your-group

[Install]
WantedBy=multi-user.target
```

2. Create a timer file at `/etc/systemd/system/obscur.timer`:

```ini
[Unit]
Description=Run ObscuR CTI Tool daily

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

3. Enable and start the timer:

```sh
sudo systemctl daemon-reload
sudo systemctl enable obscur.timer
sudo systemctl start obscur.timer
```

## Local Development Setup

If you prefer to run ObscuR directly on your system without Docker:

### Dependencies

#### Tor Browser

```sh
sh scripts/install_tbb.sh
```

#### Virtual Screen (for headless browsing)

```sh
# Fedora
sudo dnf install xorg-x11-server-Xvfb

# Ubuntu/Debian
sudo apt install xvfb
```

### Python Setup

```sh
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip3 install -r src/requirements.txt
```

### Development Environment

Start the required services using the development compose file:

```sh
docker compose -f docker-compose-dev.yml up -d
```

Run the tool locally:

```sh
python3 src/main.py
```
