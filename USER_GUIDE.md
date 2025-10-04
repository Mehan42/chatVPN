# XVPN User Guide

## Introduction

Welcome to XVPN - an intelligent VPN system with AI-powered transport management, automatic monitoring, and self-healing capabilities.

## Getting Started

### System Requirements

- Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+ recommended)
- At least 1GB RAM
- Internet connection

### Installation

#### Windows
1. Download the Windows installer from the releases page
2. Run the installer as Administrator
3. Follow the installation wizard

#### macOS
```bash
brew tap xvpn/xvpn
brew install xvpn-client
```

#### Linux
```bash
git clone https://github.com/Mehan42/chatVPN.git
cd chatVPN
./install_client.sh
```

## First Time Setup

### 1. Obtain Client Configuration

Contact your XVPN administrator to get your client configuration file (`client.json`).

### 2. Place Configuration File

Place the `client.json` file in:
- **Windows**: `C:\Program Files\XVPN\client\clients\`
- **macOS**: `~/Library/Application Support/XVPN/clients/`
- **Linux**: `~/chatvpn/client/clients/`

### 3. Launch XVPN Client

Double-click the XVPN icon or run:
```bash
python3 ~/chatvpn/client/chatvpn_gui.py
```

## Using the GUI

### Main Window

The main window displays:
- **Connection Status**: ON/OFF indicator
- **IP Address**: Your current external IP
- **Security Indicator**: Color-coded security level (Green = Excellent, Red = Poor)
- **Transport Information**: Current transport protocol
- **Connection Speed**: Upload/Download speeds

### Connection Controls

#### Connect/Disconnect Button
- Click to toggle VPN connection
- Changes to "Connecting..." during establishment
- Shows "Disconnect" when connected

#### Request Configuration Button
- Downloads latest configuration from server
- Updates transport manifests
- Refreshes available transports

#### Change UUID Button
- Allows switching between client profiles
- Useful for multiple accounts

### Security Monitoring

The security indicator shows:
- **Green (5/5)**: Excellent security, no leaks
- **Yellow (3-4/5)**: Good security with minor issues
- **Orange (2/5)**: Fair security, some concerns
- **Red (0-1/5)**: Poor security, potential leaks

Hover over the indicator to see detailed security analysis.

### Transport Information

Displays current transport:
- Protocol type (VLESS, VMess, Trojan, etc.)
- Server location
- Connection quality metrics

## Advanced Features

### Transport Switching

XVPN automatically switches transports when:
- Current transport becomes unstable
- Security score drops below threshold
- Network conditions change

Manual transport switching:
1. Click "Transports" menu
2. Select preferred transport
3. Connection will switch immediately

### Proxy Modes

XVPN supports multiple proxy modes:
- **TUN**: Standard VPN tunnel (default)
- **SOCKS5**: SOCKS5 proxy
- **HTTP**: HTTP proxy
- **Transparent**: Transparent proxy
- **Auto**: Automatic mode selection

Change proxy mode:
1. Click "Settings" menu
2. Select "Proxy Mode"
3. Choose desired mode

### IPv6 Support

XVPN supports IPv6 dual-stack:
- Automatic IPv4/IPv6 selection
- IPv6 leak protection
- Dual-stack connectivity monitoring

Check IPv6 status in the main window footer.

## Troubleshooting

### Connection Issues

1. **Cannot connect to any transport**
   - Check internet connection
   - Request new configuration
   - Contact administrator

2. **Slow connection speeds**
   - Try different transport
   - Check network bandwidth
   - Close bandwidth-intensive applications

3. **IP leak detected**
   - Restart VPN connection
   - Check firewall settings
   - Update client software

### Security Warnings

1. **Low security score**
   - Run security diagnostics
   - Check for DNS leaks
   - Verify transport configuration

2. **Certificate warnings**
   - Update client software
   - Check system time
   - Contact administrator

### Common Solutions

#### Refresh Configuration
1. Click "Request Configuration"
2. Wait for download completion
3. Restart VPN connection

#### Reset Connection
1. Click "Disconnect"
2. Wait for full disconnection
3. Click "Connect"

#### Update Client
1. Check for updates in "Help" menu
2. Download latest version
3. Install update

## Notifications

XVPN sends notifications for:
- Connection status changes
- Security alerts
- Transport switches
- System updates

Manage notification settings:
1. Click "Settings" menu
2. Select "Notifications"
3. Adjust preferences

## Keyboard Shortcuts

- **Ctrl+C**: Copy selected text
- **Ctrl+V**: Paste clipboard content
- **Ctrl+R**: Request configuration
- **Ctrl+Q**: Quit application
- **F1**: Show help
- **F5**: Refresh status

## Command Line Usage

For advanced users, XVPN can be controlled via command line:

```bash
# Start VPN
python3 chatvpn_backend.py start

# Stop VPN
python3 chatvpn_backend.py stop

# Request configuration
python3 chatvpn_backend.py config

# Check status
python3 chatvpn_backend.py status

# Set proxy mode
python3 chatvpn_backend.py proxy --mode socks5 --port 1080
```

## Privacy and Security

### Data Collection

XVPN collects minimal data:
- Connection logs (timestamps, transport used)
- Performance metrics (speed, latency)
- Error reports (for debugging)

No browsing history or personal data is collected.

### Encryption

All connections use:
- AES-256 encryption
- Perfect Forward Secrecy
- Certificate pinning
- TLS 1.3 support

### Kill Switch

XVPN includes an automatic kill switch:
- Blocks internet traffic when VPN disconnects
- Prevents IP leaks
- Automatically reconnects

Enable/disable in Settings > Security.

## Support

### Documentation
- Online documentation: https://docs.xvpn.local
- FAQ: https://docs.xvpn.local/faq
- API documentation: https://docs.xvpn.local/api

### Community Support
- Telegram group: t.me/xvpn_community
- Reddit: r/xvpn
- Discord: discord.gg/xvpn

### Professional Support
- Email: support@xvpn.local
- Business hours: 9AM-5PM UTC
- Premium support available

## Changelog

For latest changes, see [CHANGELOG.md](CHANGELOG.md)

## License

XVPN is licensed under the MIT License. See [LICENSE](LICENSE) for details.