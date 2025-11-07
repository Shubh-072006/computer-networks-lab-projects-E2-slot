# VS Code Setup Guide - UDP Network Simulator

Complete step-by-step instructions to view and run this project in Visual Studio Code.

## Prerequisites

Before you begin, ensure you have:
- **Node.js** (v18 or later) - [Download here](https://nodejs.org/)
- **Visual Studio Code** - [Download here](https://code.visualstudio.com/)
- **Git** (optional, for version control)

---

## Step 1: Open Project in VS Code

### Option A: From Replit
1. Click the **three dots menu** (⋮) in Replit
2. Select **"Download as zip"**
3. Extract the zip file to your desired location
4. Open VS Code
5. Click **File → Open Folder**
6. Navigate to the extracted folder and click **Select Folder**

### Option B: From Command Line
```bash
# Navigate to your projects directory
cd ~/projects

# If you have the project cloned
cd udp-network-simulator

# Open in VS Code
code .
```

---

## Step 2: Install Dependencies

### Open Integrated Terminal
- Press `` Ctrl+` `` (backtick) or
- Click **Terminal → New Terminal** from the menu

### Install Packages
```bash
npm install
```

This will install all required dependencies including:
- React & TypeScript
- vis-network (for network visualization)
- shadcn/ui components
- Express server
- And all other dependencies

**Wait for installation to complete** (usually 1-2 minutes)

---

## Step 3: Start the Development Server

In the terminal, run:
```bash
npm run dev
```

You should see output similar to:
```
> dev
> NODE_ENV=development tsx server/index.ts

Server running on http://0.0.0.0:5000
Vite dev server ready
```

---

## Step 4: View the Application

1. **Open your browser** (Chrome, Firefox, Edge, or Safari)
2. Navigate to: **`http://localhost:5000`**
3. You should see the **UDP Network Simulator** interface

---

## Step 5: Understanding the Project Structure

```
udp-network-simulator/
├── client/                      # Frontend React application
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   │   ├── MatrixInput.tsx        # Matrix input with 700×700 support
│   │   │   ├── NetworkTopology.tsx    # Network graph visualization
│   │   │   ├── ControlPanel.tsx       # Simulation controls
│   │   │   ├── PacketInspector.tsx    # Packet details viewer
│   │   │   ├── StatisticsPanel.tsx    # Protocol statistics
│   │   │   ├── EventLog.tsx           # Network event logger
│   │   │   ├── ResultDisplay.tsx      # Operation results display
│   │   │   └── ThemeToggle.tsx        # Dark/light mode toggle
│   │   ├── pages/
│   │   │   └── NetworkSimulator.tsx   # Main application page
│   │   ├── App.tsx            # App router
│   │   └── main.tsx           # Entry point
│   └── index.html             # HTML template
├── server/                     # Backend Express server
│   ├── index.ts              # Server entry point
│   ├── routes.ts             # API routes
│   └── vite.ts               # Vite dev server integration
├── shared/                     # Shared code between client/server
│   ├── schema.ts             # TypeScript types
│   └── matrix-operations.ts  # Matrix calculation logic
├── package.json               # Dependencies & scripts
└── vite.config.ts            # Vite configuration
```

---

## Step 6: Using the Application

### Matrix Operations Tab

1. **Select Operation**: Choose from:
   - Addition (A + B)
   - Subtraction (A - B)
   - Multiplication (A × B)
   - Transpose (A^T)
   - Inverse (A^-1)
   - Determinant (det A)
   - Scalar Multiply (k × A)

2. **Test Large Matrices**: Quick buttons for:
   - 10×10
   - 50×50
   - 100×100
   - 500×500
   - **700×700** ⚡ (highlighted)

3. **Manual Input**:
   - Set custom rows/cols (up to 700×700)
   - Click "Resize" to create the matrix
   - Click "Random" to fill with random values
   - For matrices ≤10×10, you can edit individual cells

4. **Execute**: Click "Execute Operation" to:
   - Send UDP request packet
   - Calculate the result
   - Receive ACK and response packets
   - View the result

### Simulation Tab

1. **Network Topology**: Visual representation of Client ↔ Server ↔ Moderator
2. **Control Panel**: 
   - Start/Pause simulation
   - Step through packet-by-packet
   - Adjust simulation speed (0.5x to 5x)
   - Reset simulation

3. **Event Log**: Real-time network events:
   - Packet sent/received
   - ACK/NACK messages
   - Timeouts
   - Retransmissions
   - Checksum errors

4. **Statistics Panel**: Protocol metrics:
   - Packets sent/received
   - Retransmissions count
   - Timeouts
   - Checksum errors
   - Success rate percentage

5. **Packet Inspector**: Detailed packet information:
   - Header (seq, sender, receiver, timestamp)
   - Payload (operation, encrypted data)
   - Checksum & integrity
   - Metadata (chunks, packet ID)

---

## Step 7: Testing Matrix Operations

### Example 1: Small Matrix Addition
```
1. Go to "Matrix Operations" tab
2. Keep default 2×2 matrices
3. Select "Addition (A + B)"
4. Click "Execute Operation"
5. View result in the Result Display
6. Switch to "Simulation" tab to see packet flow
```

### Example 2: Large Matrix Multiplication (700×700)
```
1. Go to "Matrix Operations" tab
2. Click the "700×700" button (with lightning bolt)
3. Select "Multiplication (A × B)"
4. Click "Execute Operation"
5. Watch the processing time (may take a few seconds)
6. Result will show preview of first rows
7. Click "Download" to save full result
```

### Example 3: Determinant Calculation
```
1. Select "Determinant (det A)"
2. Matrix B will be disabled (single matrix operation)
3. Create a square matrix (e.g., 3×3)
4. Click "Execute Operation"
5. Result will show a single number
```

### Example 4: Scalar Multiplication
```
1. Select "Scalar Multiply (k × A)"
2. Enter a scalar value (e.g., 5)
3. Set up Matrix A
4. Click "Execute Operation"
5. Result = every element × scalar value
```

---

## Step 8: Understanding the Network Simulation

### UDP Protocol Features Demonstrated:

1. **Stop-and-Wait Protocol**:
   - Client sends request packet
   - Waits for ACK from server
   - Server processes and sends response
   - All visible in event log

2. **Packet Structure**:
   ```json
   {
     "type": "OPERATION_REQUEST",
     "seq": 1,
     "data": "encrypted_matrix_data",
     "operation": "multiply",
     "sender": "client",
     "receiver": "server",
     "checksum": "md5_hash",
     "totalChunks": 1,
     "chunkIndex": 0
   }
   ```

3. **Error Detection**:
   - MD5 checksums verify data integrity
   - NACK packets signal errors
   - Automatic retransmission on failure

4. **Network Nodes**:
   - **Client**: Sends operation requests
   - **Server**: Processes operations, sends results
   - **Moderator**: Monitors all network traffic (visualization)

---

## Step 9: Recommended VS Code Extensions

Install these extensions for better development experience:

1. **ESLint** (`dbaeumer.vscode-eslint`)
   - Linting for JavaScript/TypeScript
   
2. **Prettier** (`esbenp.prettier-vscode`)
   - Code formatting

3. **TypeScript Vue Plugin** (`Vue.volar`)
   - Enhanced TypeScript support

4. **Tailwind CSS IntelliSense** (`bradlc.vscode-tailwindcss`)
   - Autocomplete for Tailwind classes

5. **GitLens** (`eamodio.gitlens`) (optional)
   - Git history and blame

### Installing Extensions:
1. Press `Ctrl+Shift+X` (Windows/Linux) or `Cmd+Shift+X` (Mac)
2. Search for extension name
3. Click "Install"

---

## Step 10: Development Workflow

### File Organization
- **Add new components**: `client/src/components/`
- **Add new pages**: `client/src/pages/`
- **Modify types**: `shared/schema.ts`
- **Matrix operations**: `shared/matrix-operations.ts`

### Hot Reload
- Changes auto-reload in browser
- No need to restart server for most changes
- TypeScript errors show in VS Code and browser

### Debugging

#### Browser DevTools:
1. Press `F12` in browser
2. **Console tab**: View logs and errors
3. **Network tab**: See HTTP requests
4. **Elements tab**: Inspect DOM

#### VS Code Debugging:
1. Set breakpoints: Click left of line number
2. Press `F5` to start debugging
3. Choose "Node.js" when prompted

---

## Step 11: Common Commands

### Development
```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run typecheck

# Linting
npm run lint
```

### Troubleshooting
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite

# Check Node version
node --version  # Should be 18+
```

---

## Step 12: Viewing in Split Screen

### Option 1: Side-by-Side Editor and Browser
1. Open browser on right half of screen
2. VS Code on left half
3. See live updates as you code

### Option 2: VS Code Built-in Browser Preview
1. Install "Live Preview" extension
2. Press `Ctrl+Shift+P`
3. Type "Live Preview: Show Preview"
4. Opens browser inside VS Code

---

## Keyboard Shortcuts (VS Code)

| Action | Windows/Linux | Mac |
|--------|---------------|-----|
| Open file | `Ctrl+P` | `Cmd+P` |
| Command palette | `Ctrl+Shift+P` | `Cmd+Shift+P` |
| Toggle terminal | `` Ctrl+` `` | `` Cmd+` `` |
| Find in files | `Ctrl+Shift+F` | `Cmd+Shift+F` |
| Go to definition | `F12` | `F12` |
| Format document | `Shift+Alt+F` | `Shift+Option+F` |
| Toggle sidebar | `Ctrl+B` | `Cmd+B` |
| Multi-cursor | `Alt+Click` | `Option+Click` |

---

## Performance Notes

### Matrix Size vs Processing Time:
- **10×10**: < 1ms
- **100×100**: ~10ms
- **500×500**: ~500ms - 1s
- **700×700**: ~2-5s (multiplication), faster for simpler operations

### Browser Performance:
- Chrome/Edge: Best performance
- Firefox: Good performance
- Safari: Good performance
- Use Chrome DevTools Performance tab to profile

---

## Features Summary

✅ **All matrix operations from original project**:
- Addition, Subtraction, Multiplication
- Transpose, Inverse, Determinant
- Scalar Multiply

✅ **Matrix input up to 700×700**:
- Manual entry (for small matrices)
- Random generation
- Custom dimensions
- File preview for large matrices

✅ **Network simulation visualization**:
- Real-time packet animation
- Stop-and-Wait protocol demonstration
- Event logging
- Protocol statistics
- Packet inspection

✅ **Modern web interface**:
- Dark/light mode
- Responsive design
- Toast notifications
- Result download
- Processing time display

---

## Support & Troubleshooting

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000  # Mac/Linux
netstat -ano | findstr :5000  # Windows

# Kill the process or change port in server/index.ts
```

### Module Not Found Errors
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### TypeScript Errors
- Check `tsconfig.json` for proper configuration
- Ensure all types are imported from `@shared/schema`
- Run `npm run typecheck` to see all errors

---

## Next Steps

1. **Experiment**: Try different matrix sizes and operations
2. **Explore Code**: Read through components to understand structure
3. **Customize**: Modify colors in `tailwind.config.ts`
4. **Extend**: Add new matrix operations or network features
5. **Deploy**: Build and deploy to a hosting service

---

## Resources

- [Replit Documentation](https://docs.replit.com/)
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/)
- [vis-network Docs](https://visjs.github.io/vis-network/docs/network/)

---

**Enjoy exploring the UDP Network Simulator!** 🚀

For questions or issues, check the browser console (`F12`) and terminal output for error messages.
