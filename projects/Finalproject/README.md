# UDP Network Simulator

An interactive educational web application for visualizing and understanding UDP network protocols through real-time simulation and matrix operations.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Node](https://img.shields.io/badge/node-20.x-green.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue.svg)
![React](https://img.shields.io/badge/React-18.3-61dafb.svg)

## 👥 Team Members

- **SAMYUKTHA CHOWDARY VADLAMUDI** - 24BCE1625
- **BHUMIKA BAJAJ** - 24BCE1605
- **ANSHIKA JAIN** - 24BCE1573

---

## 📖 Overview

The UDP Network Simulator is a comprehensive educational platform designed to teach network protocol fundamentals through interactive visualization. The application combines two powerful features:

### 🌐 Network Protocol Simulation
- **Real-time UDP packet visualization** using the Stop-and-Wait protocol
- **Interactive network topology** with Client, Server, and Moderator nodes
- **Packet lifecycle management** including transmission, loss, corruption, and acknowledgment
- **Checksum validation** for error detection
- **ACK/NACK handling** with automatic retransmission
- **Timeout detection** and adaptive recovery
- **Event logging system** with JSON export capability
- **Live statistics dashboard** tracking packets, retransmissions, errors, and success rates

### 🔢 Matrix Operations
- **Comprehensive matrix calculator** supporting operations up to 700×700 dimensions
- **Supported operations**: Addition, Subtraction, Multiplication, Transpose, Inverse, Determinant
- **CSV file upload** for easy matrix input with validation
- **Performance profiling** with interactive charts showing execution time across different matrix sizes
- **Real-time computation** with progress indicators

---

## ✨ Key Features

### Educational Tools
- 📊 **Visual Learning**: Watch packets travel through the network with animated visualization
- 🎯 **Error Simulation**: Configurable packet loss and corruption rates
- 📝 **Detailed Logging**: Comprehensive event tracking with timestamps
- 📈 **Performance Metrics**: Real-time statistics and success rate tracking
- 🎨 **Interactive Controls**: Play, pause, step-through, and speed adjustment

### Technical Capabilities
- 🔄 **Real-time Communication**: WebSocket-based bidirectional updates
- 🌓 **Dark Mode Support**: Fully themed light/dark interface
- 📱 **Responsive Design**: Mobile, tablet, and desktop optimized
- ♿ **Accessibility**: WCAG AA compliant with keyboard navigation
- 🚀 **High Performance**: Optimized rendering and computation

---

## 🛠️ Technology Stack

### Frontend
- **React 18.3** - Modern UI library with hooks
- **TypeScript 5.6** - Type-safe development
- **Vite 5.4** - Fast development server and build tool
- **Tailwind CSS 3.4** - Utility-first styling framework
- **Shadcn/ui** - Accessible component library built on Radix UI
- **TanStack Query 5.6** - Server state management
- **Wouter 3.3** - Lightweight client-side routing
- **Recharts 2.15** - Data visualization for performance metrics
- **Lucide React** - Beautiful icon system

### Backend
- **Node.js 20.x** - JavaScript runtime
- **Express.js 4.21** - Web application framework
- **WebSocket (ws 8.18)** - Real-time bidirectional communication
- **TypeScript** - Full-stack type safety

### Development Tools
- **Drizzle ORM 0.39** - Type-safe database toolkit (configured for future use)
- **Zod 3.24** - Runtime type validation
- **esbuild 0.25** - Fast production bundling
- **tsx 4.20** - TypeScript execution

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js**: Version 20.x or higher ([Download](https://nodejs.org/))
- **npm**: Comes bundled with Node.js
- **Git**: For version control ([Download](https://git-scm.com/))

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/udp-network-simulator.git
cd udp-network-simulator
```

### 2. Install Dependencies

```bash
npm install
```

This will install all required packages for both frontend and backend.

### 3. Environment Setup

Create a `.env` file in the root directory (optional for basic usage):

```bash
PORT=5000
NODE_ENV=development
```

---

## 💻 Usage

### Development Mode

Start the development server with hot module replacement:

```bash
npm run dev
```

The application will be available at `http://localhost:5000`

### Production Build

Build the optimized production bundle:

```bash
npm run build
```

### Start Production Server

```bash
npm start
```

### Type Checking

Run TypeScript compiler for type checking:

```bash
npm run check
```

---

## 🎮 How to Use

### Network Simulation

1. **Start Simulation**: Click the "Start" button to begin packet transmission
2. **Configure Parameters**:
   - Adjust packet loss probability (0-100%)
   - Set corruption probability (0-100%)
   - Configure timeout duration (milliseconds)
   - Adjust simulation speed (0.5x - 5x)
3. **Monitor Events**: Watch the event log for real-time packet activity
4. **View Statistics**: Track packets sent, received, retransmissions, and errors
5. **Export Logs**: Download event logs as JSON for offline analysis

### Matrix Operations

1. **Input Method**:
   - **Manual Entry**: Type values directly into the matrix grid
   - **CSV Upload**: Import matrices from CSV files
   - **Random Generation**: Create random matrices for testing
2. **Select Operation**: Choose from addition, subtraction, multiplication, etc.
3. **Execute**: Click "Execute Operation" to compute results
4. **View Results**: See the resulting matrix and execution time
5. **Performance Charts**: Analyze computational complexity across different sizes

---

## 🏗️ Project Structure

```
udp-network-simulator/
├── client/                    # Frontend application
│   ├── src/
│   │   ├── components/        # Reusable React components
│   │   │   └── ui/           # Shadcn UI components
│   │   ├── pages/            # Page-level components
│   │   ├── lib/              # Utility functions and helpers
│   │   ├── hooks/            # Custom React hooks
│   │   ├── App.tsx           # Main application component
│   │   ├── main.tsx          # Entry point
│   │   └── index.css         # Global styles and design tokens
│   └── index.html            # HTML template
├── server/                    # Backend application
│   ├── routes.ts             # API route definitions
│   ├── storage.ts            # In-memory storage interface
│   ├── index.ts              # Server entry point
│   └── vite.ts               # Vite middleware configuration
├── shared/                    # Shared types and schemas
│   └── schema.ts             # Database schema and Zod types
├── design_guidelines.md       # Design system documentation
├── tailwind.config.ts         # Tailwind CSS configuration
├── tsconfig.json             # TypeScript configuration
├── vite.config.ts            # Vite build configuration
├── package.json              # Dependencies and scripts
└── README.md                 # This file
```

---

## 🎨 Design System

The application follows **Material Design** principles adapted for technical/educational content:

### Typography
- **Interface**: Inter/Roboto (clean, modern sans-serif)
- **Technical Data**: JetBrains Mono/Roboto Mono (monospace for data)

### Color Scheme
- Supports both light and dark modes
- Semantic color tokens (primary, secondary, destructive, muted, accent)
- WCAG AA compliant contrast ratios

### Components
- Built with Radix UI primitives for accessibility
- Styled with Tailwind CSS utilities
- Consistent spacing system (2/4/8/12/16px units)

For detailed design specifications, see [design_guidelines.md](./design_guidelines.md)

---

## 🔧 Configuration Options

### Simulation Parameters

Customize the UDP simulation behavior by adjusting these parameters:

| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| Loss Probability | Percentage of packets that get lost | 0-100% | 10% |
| Corruption Probability | Percentage of packets that get corrupted | 0-100% | 15% |
| Timeout Duration | Time to wait for ACK before retransmission | 500-10000ms | 2000ms |
| Network Delay | Simulated network latency range | 10-1000ms | 50-300ms |
| Simulation Speed | Playback speed multiplier | 0.5x-5x | 1x |

### Matrix Operations

| Parameter | Description | Maximum |
|-----------|-------------|---------|
| Matrix Dimensions | Rows × Columns | 700×700 |
| CSV File Size | Maximum upload size | 10MB |
| Computation Timeout | Maximum execution time | 30s |

---

## 🧪 Testing

The application includes comprehensive testing capabilities:

### Manual Testing
- Use the simulation controls to test different scenarios
- Adjust parameters to observe protocol behavior
- Verify error handling with high loss/corruption rates

### Performance Testing
- Use matrix operations with varying sizes
- Monitor execution time charts
- Test CSV upload with large matrices

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Getting Started

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes** and commit:
   ```bash
   git commit -m "Add amazing feature"
   ```
4. **Push to your branch**:
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

### Development Guidelines

- Follow the existing code style and conventions
- Write clear, descriptive commit messages
- Add comments for complex logic
- Test your changes thoroughly
- Update documentation as needed

### Code Quality Standards

- **TypeScript**: Use strict type checking
- **React**: Follow hooks best practices
- **Styling**: Use Tailwind CSS utilities
- **Accessibility**: Maintain WCAG AA compliance

---

## 📚 Educational Resources

### Understanding UDP

UDP (User Datagram Protocol) is a connectionless protocol that:
- Provides fast, lightweight communication
- Does not guarantee delivery or ordering
- Requires application-level error handling

### Stop-and-Wait Protocol

The simplest reliable data transfer protocol:
1. Send one packet and wait
2. Receiver validates with checksum
3. Receiver sends ACK (success) or NACK (error)
4. Sender retransmits on timeout or NACK
5. Repeat until all data is transmitted

### Key Concepts Demonstrated

- **Checksums**: Error detection using mathematical fingerprints
- **Sequence Numbers**: Packet identification and duplicate detection
- **Timeouts**: Recovery from lost acknowledgments
- **Retransmission**: Ensuring reliable delivery over unreliable networks

---

## 🐛 Troubleshooting

### Common Issues

**Problem**: Port 5000 already in use
```bash
# Solution: Change port in .env file
PORT=3000
```

**Problem**: WebSocket connection fails
```bash
# Solution: Ensure backend is running and firewall allows connections
npm run dev
```

**Problem**: TypeScript errors during build
```bash
# Solution: Clear build cache and reinstall
rm -rf node_modules dist
npm install
```

**Problem**: Matrix operation timeout
```bash
# Solution: Reduce matrix size or increase timeout in configuration
```

---

## 📊 Performance

### Optimization Techniques

- **Lazy Loading**: Large visualizations load on demand
- **Debouncing**: Input changes optimized
- **Virtualization**: Event log handles thousands of entries
- **Animation Optimization**: RequestAnimationFrame for smooth rendering
- **Code Splitting**: Vite-based dynamic imports

### Benchmarks

| Operation | Matrix Size | Average Time |
|-----------|-------------|--------------|
| Addition | 100×100 | ~5ms |
| Multiplication | 100×100 | ~150ms |
| Multiplication | 500×500 | ~25s |
| Inverse | 100×100 | ~200ms |

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

### Technologies & Libraries
- [React](https://react.dev/) - UI framework
- [Vite](https://vitejs.dev/) - Build tool
- [Tailwind CSS](https://tailwindcss.com/) - Styling framework
- [Shadcn/ui](https://ui.shadcn.com/) - Component library
- [Radix UI](https://www.radix-ui.com/) - Accessible primitives
- [TanStack Query](https://tanstack.com/query) - Data fetching
- [Recharts](https://recharts.org/) - Charting library
- [Lucide](https://lucide.dev/) - Icon system

### Inspiration
This project was created to make network protocol education more accessible and engaging through interactive visualization.

---

## 📧 Contact & Support

### Team Contact
For questions, suggestions, or collaboration opportunities:

- **Samyuktha Chowdary Vadlamudi** - 24BCE1625
- **Bhumika Bajaj** - 24BCE1605
- **Anshika Jain** - 24BCE1573

### Repository
- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/your-username/udp-network-simulator/issues)
- **Discussions**: Join conversations in [GitHub Discussions](https://github.com/your-username/udp-network-simulator/discussions)

---

## 🗺️ Roadmap

### Current Features (v1.0)
- ✅ UDP Stop-and-Wait protocol simulation
- ✅ Real-time packet visualization
- ✅ Matrix operations with CSV support
- ✅ Event logging and export
- ✅ Performance profiling charts

### Planned Features (v2.0)
- 🔄 Sliding Window protocol implementation
- 🔄 Go-Back-N and Selective Repeat protocols
- 🔄 TCP comparison mode
- 🔄 Network topology customization
- 🔄 Multi-user collaborative simulations
- 🔄 Database persistence for session history
- 🔄 Advanced encryption demonstrations

### Future Enhancements
- 📱 Mobile app version
- 🎓 Curriculum integration for educators
- 📖 Interactive tutorials and guided lessons
- 🏆 Gamification with challenges and achievements

---

## 📸 Screenshots

> **Note**: Add screenshots here after the application is deployed

### Network Simulation
![Network Simulation Dashboard](#)

### Matrix Operations
![Matrix Calculator Interface](#)

### Event Logging
![Event Log Export](#)

### Performance Charts
![Performance Profiling](#)

---

## 🌟 Star History

If you find this project useful, please consider giving it a star! ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=your-username/udp-network-simulator&type=Date)](https://star-history.com/#your-username/udp-network-simulator&Date)

---

<div align="center">

**Made with ❤️ for Computer Networks Education**

[Report Bug](https://github.com/your-username/udp-network-simulator/issues) · [Request Feature](https://github.com/your-username/udp-network-simulator/issues) · [Documentation](./design_guidelines.md)

</div>
