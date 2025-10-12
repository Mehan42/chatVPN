// Package state provides integration between state machine and tunnel verifier
package state

import (
	"context"
	"log"
	"time"
	"xvpn-client-go/internal/tunnelverifier"
)

// ITunnelVerifierStateHandler defines the interface for state machine integration with tunnel verifier
type ITunnelVerifierStateHandler interface {
	// StartTunnelVerification starts the tunnel verification process
	StartTunnelVerification() error
	
	// StopTunnelVerification stops the tunnel verification process
	StopTunnelVerification() error
	
	// IsTunnelVerificationValid checks if tunneling is currently valid
	IsTunnelVerificationValid() (bool, error)
}

// TunnelVerifierStateHandler implements the integration between state machine and tunnel verifier
type TunnelVerifierStateHandler struct {
	stateMachine   *VPNStateMachine
	tunnelVerifier *tunnelverifier.TunnelVerifier
	ctx            context.Context
	cancel         context.CancelFunc
}

// NewTunnelVerifierStateHandler creates a new handler for tunnel verifier integration
func NewTunnelVerifierStateHandler(sm *VPNStateMachine) (*TunnelVerifierStateHandler, error) {
	// Create tunnel verifier config
	config := tunnelverifier.Config{
		// Use default configuration for now - these will be customizable later
		CheckInterval:         30 * time.Second, // Check every 30 seconds
		Timeout:              60 * time.Second, // 60 second timeout for each check
		VerificationEndpoints: []string{"8.8.8.8", "1.1.1.1"}, // Example non-RU IPs
		TestPayload:          "TUNNEL_TEST",
		LogLevel:             "info", // Default log level
		IPCheckService:       "https://httpbin.org/ip", // Service to check external IP
		CheckIPLeak:          true,  // Enable IP leak checking
		CheckDNSLeak:         true,  // Enable DNS leak checking
		VerifyRouting:        true,  // Enable traffic routing verification
	}
	
	tv, err := tunnelverifier.New(config)
	if err != nil {
		return nil, err
	}
	
	// Integrate logging with the tunnel verifier
	// Using default logger for now since we don't have access to the centralized logging system here
	tv.SetLogger(log.Writer())
	
	ctx, cancel := context.WithCancel(context.Background())
	
	handler := &TunnelVerifierStateHandler{
		stateMachine:   sm,
		tunnelVerifier: tv,
		ctx:            ctx,
		cancel:         cancel,
	}
	
	return handler, nil
}

// StartTunnelVerification starts the tunnel verification process
func (h *TunnelVerifierStateHandler) StartTunnelVerification() error {
	return h.tunnelVerifier.Start(h.ctx)
}

// StopTunnelVerification stops the tunnel verification process
func (h *TunnelVerifierStateHandler) StopTunnelVerification() error {
	return h.tunnelVerifier.Stop(h.ctx)
}

// IsTunnelVerificationValid checks if tunneling is currently valid
func (h *TunnelVerifierStateHandler) IsTunnelVerificationValid() (bool, error) {
	return h.tunnelVerifier.IsTunnelingValid()
}

// IntegrateWithStateMachine integrates the tunnel verifier with state transitions
func (h *TunnelVerifierStateHandler) IntegrateWithStateMachine() {
	// Add transition handlers to start/stop tunnel verification based on state
	
	// When entering Running state, start tunnel verification
	h.stateMachine.addTransition(StateIdle, EventStartRequested, StateRunning, func(ctx *Context) error {
		// Start tunnel verification when VPN transitions to running
		if err := h.StartTunnelVerification(); err != nil {
			// Only log the error, don't fail the state transition
			log.Printf("Warning: Failed to start tunnel verification: %v", err)
			// Don't set ctx.LastError to avoid transition failure
		}
		log.Println("Tunnel verification started as VPN entered Running state")
		return nil
	})
	
	// When entering Stopping state, stop tunnel verification
	h.stateMachine.addTransition(StateRunning, EventStopRequested, StateStopping, func(ctx *Context) error {
		// Stop tunnel verification when VPN is stopping
		if err := h.StopTunnelVerification(); err != nil {
			// Only log the error, don't fail the state transition
			log.Printf("Warning: Failed to stop tunnel verification: %v", err)
			// Don't set ctx.LastError to avoid transition failure
		}
		log.Println("Tunnel verification stopped as VPN entered Stopping state")
		return nil
	})
	
	// Also stop tunnel verification when transitioning from Running to Idle (directly)
	h.stateMachine.addTransition(StateRunning, EventStopRequested, StateIdle, func(ctx *Context) error {
		// Stop tunnel verification when VPN becomes idle from running
		if err := h.StopTunnelVerification(); err != nil {
			// Only log the error, don't fail the state transition
			log.Printf("Warning: Failed to stop tunnel verification: %v", err)
			// Don't set ctx.LastError to avoid transition failure
		}
		log.Println("Tunnel verification stopped as VPN entered Idle state from Running")
		return nil
	})
}