# LAN File Transfer System Architecture

## System Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    LAN File Transfer System                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │    GUI      │    │    CLI      │    │  Programmatic│     │
│  │ Interface   │    │ Interface   │    │    API       │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                   │                   │           │
│         └───────────────────┼───────────────────┘           │
│                             │                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                main.py (Entry Point)                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                             │                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Server    │    │   Client    │    │ Discovery   │     │
│  │ (TCP)       │    │ (TCP)       │    │ (UDP)       │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                   │                   │           │
│         └───────────────────┼───────────────────┘           │
│                             │                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Network Layer (TCP/UDP)                   │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## File Structure & Purposes

### Core Components
- **main.py** - Entry point with CLI interface
- **server.py** - TCP server for receiving files
- **client.py** - TCP client for sending files
- **discovery.py** - UDP service for automatic server discovery

### GUI Components
- **gui_server.py** - Tkinter GUI for server management
- **gui_client.py** - Tkinter GUI for client operations

### Support Files
- **config.py** - Configuration settings and constants
- **utils.py** - Utility functions (logging, file operations, networking)
- **demo.py** - Demonstration script
- **test_system.py** - Test suite

## Data Flow
1. **Discovery Phase**: UDP broadcast to find servers
2. **Connection Phase**: TCP connection to selected server
3. **Authentication Phase**: Password verification
4. **Transfer Phase**: File metadata + data transfer
5. **Verification Phase**: Hash verification for integrity
