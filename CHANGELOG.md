# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - YYYY-MM-DD

### Added
- Initial release of XVPN system
- Server components: API, Agent, Bot, Worker, Orchestrator
- Client components: GUI application with state machine
- Docker support with Traefik load balancer
- AI-powered transport switching with ChromaDB RAG system
- Health monitoring and automatic failover
- IPv6 dual-stack support
- Multiple proxy modes (SOCKS5, HTTP, transparent)
- Telegram bot management interface
- Comprehensive documentation and installation guides

### Changed
- Improved installation scripts with proper error handling
- Enhanced security with TLS certificate pinning
- Optimized performance with uv package manager
- Better error reporting and logging

### Fixed
- Various bug fixes and stability improvements
- Security vulnerabilities in network communication
- Compatibility issues with different Linux distributions

## [1.0.0] - 2025-10-04

### Added
- Initial stable release
- Core VPN functionality with XRay backend
- Intelligent transport management
- Automated health monitoring
- Client-server architecture with REST API
- Containerized deployment with Docker Compose
- Comprehensive documentation

[Unreleased]: https://github.com/Mehan42/chatVPN/compare/v1.0.0...HEAD