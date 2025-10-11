// Package tunnelverifier provides an interface for integration with the XVPN system
package tunnelverifier

import (
	"context"
	"io"
)

// ITunnelVerifier defines the interface for tunnel verification
type ITunnelVerifier interface {
	// Start begins the tunnel verification process
	Start(ctx context.Context) error
	
	// Stop stops the tunnel verification process
	Stop(ctx context.Context) error
	
	// IsTunnelingValid checks if the tunneling is currently valid
	IsTunnelingValid() (bool, error)
}

// ILoggable defines the interface for integration with the logging system
type ILoggable interface {
	// SetLogger sets the logger for the tunnel verifier
	SetLogger(logger io.Writer)
	
	// GetLogs returns the logs for the tunnel verification processes
	GetLogs() (string, error)
}

// Integration with state machine
// The tunnel verifier should be integrated into the state machine transitions
// to start verification when VPN is connected and stop when disconnected