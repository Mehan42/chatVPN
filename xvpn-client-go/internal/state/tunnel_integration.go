// Package state provides integration between state machine and tunnel verifier
package state

import (
	"context"
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
		CheckInterval:       30 * time.Second, // Check every 30 seconds
		Timeout:             60 * time.Second, // 60 second timeout for each check
		VerificationEndpoints: []string{"8.8.8.8", "1.1.1.1"}, // Example non-RU IPs
		TestPayload:         "TUNNEL_TEST",
	}
	
	tv, err := tunnelverifier.New(config)
	if err != nil {
		return nil, err
	}
	
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
	h.stateMachine.addTransition(StateRunning, EventStartRequested, StateRunning, func(ctx *Context) error {
		// Start tunnel verification when VPN is running
		if err := h.StartTunnelVerification(); err != nil {
			ctx.LastError = err.Error()
			return err
		}
		return nil
	})
	
	// When entering Stopping or Idle state, stop tunnel verification
	h.stateMachine.addTransition(StateStopping, EventStopRequested, StateStopping, func(ctx *Context) error {
		// Stop tunnel verification when VPN is stopping
		if err := h.StopTunnelVerification(); err != nil {
			ctx.LastError = err.Error()
			return err
		}
		return nil
	})
	
	// When entering Idle state, stop tunnel verification
	h.stateMachine.addTransition(StateIdle, EventStopRequested, StateIdle, func(ctx *Context) error {
		// Stop tunnel verification when VPN is idle
		if err := h.StopTunnelVerification(); err != nil {
			ctx.LastError = err.Error()
			return err
		}
		return nil
	})
}