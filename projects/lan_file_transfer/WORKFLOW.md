# System Workflow - Step by Step

## Complete File Transfer Process

### Phase 1: Server Setup
1. **Server starts** (GUI/CLI/Programmatic)
2. **TCP socket** binds to port (default 8888)
3. **UDP discovery service** starts on port 8889
4. **Server waits** for client connections

### Phase 2: Client Discovery
1. **Client sends UDP broadcast** to 255.255.255.255:8889
2. **All servers respond** with their IP and port
3. **Client receives list** of available servers
4. **User selects server** or enters manually

### Phase 3: Connection & Authentication
1. **Client connects** to server via TCP
2. **Server sends auth request** (JSON message)
3. **Client responds** with password
4. **Server verifies** password and sends success/failure

### Phase 4: File Transfer
1. **Client calculates** file hash (MD5)
2. **Client sends metadata** (filename, size, hash)
3. **Server validates** file size and sends ready signal
4. **Client sends file data** in chunks (1KB each)
5. **Server receives and writes** file to disk
6. **Server calculates hash** of received file
7. **Hash verification** - success or failure response

### Phase 5: Cleanup
1. **Connection closes**
2. **Logs updated** with transfer details
3. **GUI updates** (if applicable)

## Security Features
- **Pre-shared password** authentication
- **MD5 hash verification** for file integrity
- **Safe filename handling** (removes invalid characters)
- **File size limits** (100MB max)

## Error Handling
- **Connection timeouts**
- **Authentication failures**
- **File size validation**
- **Hash mismatch detection**
- **Network interruption recovery**
