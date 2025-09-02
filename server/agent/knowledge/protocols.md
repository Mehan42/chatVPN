# Protocol: T0 failed 3x
- Switch to T1 (immediate)
- Log event to database
- Push report to admin via TG
- If T1 fails within 120s, apply T2_priority++ and attempt T2

# Protocol: API /manifest unreachable > 5min
- Try fallback manifest URLs from fallback.json
- If none reachable, switch to proxy-only mode (local SOCKS) and notify admin
- Cache last known good manifest for offline operation

# Protocol: All transports down
- Start local debug collection: gather /var/log/xvpn/*, journalctl -u xvpn-core -n 1000
- Package into /opt/xvpn/agent/logs/case_<timestamp>.tar.gz
- Attempt DNS and DoH tests from fallback resources
- If unsuccessful, send minimal report to admin and set status MANUAL_INTERVENTION_REQUIRED

# Protocol: Mask score degradation
- If mask_score < 3, immediately switch to next transport
- Log all mask_score changes for analysis
- If pattern detected (consistent degradation), rotate client credentials
- Update transport priority based on mask performance

# Protocol: Connection timeout
- Retry current transport 2 more times with exponential backoff
- If still failing, mark transport as degraded and switch to next
- Reset fail_count after 1 hour of no attempts
- Log detailed connection attempts for debugging

# Protocol: DNS resolution failure
- Switch to DoH (DNS-over-HTTPS) from fallback.json
- Try alternative DNS servers: 1.1.1.1, 8.8.8.8, 9.9.9.9
- If DNS completely fails, use IP addresses from fallback resources
- Alert admin via Telegram if DNS issues persist > 10min

# Protocol: Certificate validation error
- Log certificate details and validation error
- Attempt connection with certificate pinning bypass (if configured)
- Switch to next transport if certificate issues persist
- Schedule certificate refresh for next maintenance window
