# UDP Network Simulator - Design Guidelines

## Design Approach: Material Design with Technical Focus

**Rationale**: This is a technical, educational tool requiring information clarity and precision. Material Design provides the structured foundation needed for data-dense interfaces while maintaining visual clarity.

**Core Principles**: 
- Information hierarchy over decoration
- Immediate visual feedback for network events
- Educational accessibility for protocol understanding
- Purposeful use of space for technical data

---

## Typography System

**Font Families**:
- **Interface**: Inter or Roboto (clean, modern sans-serif)
- **Technical Data**: JetBrains Mono or Roboto Mono (packet payloads, checksums, logs, hex values)

**Type Scale**:
```
Page Title:       text-3xl font-bold
Section Headers:  text-xl font-semibold  
Card Headers:     text-base font-medium
Body Text:        text-sm
Technical Data:   text-sm font-mono
Labels/Captions:  text-xs
```

**Typography Rules**:
- Use monospace exclusively for technical values (checksums, hex, timestamps, packet data)
- Medium line-height (1.5) for dense information areas
- Tight line-height (1.2) for compact event logs
- Clear hierarchy: headers distinct from body content

---

## Layout & Spacing System

**Spacing Primitives**: Tailwind units of 2, 4, 8, 12, 16

```
Component padding:     p-4
Section spacing:       space-y-8
Element gaps:          gap-4
Inline spacing:        space-x-2
Log entry spacing:     space-y-2
Container max-width:   max-w-screen-2xl mx-auto
Side panel widths:     w-80 or w-96
```

**Grid Structure**:
- **Desktop (lg+)**: 70/30 split (network canvas / control panels)
- **Tablet (md)**: 2-column grid, full-width event log
- **Mobile (sm)**: Single column stack

---

## Core Component Library

### Dashboard Layout
```
Top Navigation Bar:
- App title/logo (left)
- Global controls: Start/Stop simulation (right)
- Theme toggle (far right)

Main Content Grid:
- Left: Network topology canvas (large focal area)
- Right: Control panel + Statistics sidebar
- Bottom: Collapsible event log dock

Tab Navigation:
- Matrix Operations tab
- Simulation tab
```

### Panel Cards
```
Structure: shadow-md, rounded-lg, p-4
Header: Icon + text-base font-medium
Content sections with clear separation
Subtle elevation hierarchy
```

### Network Canvas (Primary Visualization)
```
Dimensions: min-h-[500px], w-full
Node Types: Client, Server, Moderator (distinct visual treatment)
Edges: Directed arrows with labels
Packet Animation: 1-2s linear transit with pulse effect
Packet Labels: REQ, ACK, NACK, DATA (color-coded badges)
Interactive: Click nodes/edges for details
```

### Control Panel
```
Button Group: Start, Pause, Step, Reset
- Layout: gap-2, horizontal flex
- Style: Icon + text label
- Hierarchy: Primary (Start/Execute), Secondary (others)

Speed Slider: 0.5x, 1x, 2x, 5x simulation speed

Matrix Configuration:
- Tab interface: Manual / Random generation
- Operation selector dropdown
- Dimension inputs (up to 700×700)
- Execute button (prominent primary action)
```

### Packet Inspector
```
Layout: Accordion sections or fixed panel
Sections:
- Header Information (seq, type, sender/receiver)
- Payload Display (monospace formatting)
- Checksum & Integrity
- Metadata (chunks, timestamps)

Features:
- Copy-to-clipboard buttons for values
- Syntax highlighting for encrypted vs decrypted data
- Expandable/collapsible sections
```

### Statistics Dashboard
```
Grid Layout: grid-cols-2 gap-4

Metric Cards:
- Large numeric value: text-2xl font-bold
- Label below: text-sm with icon
- Color-coded status indicators

Tracked Metrics:
- Packets Sent/Received
- Retransmissions
- Timeout Events
- Checksum Errors
- Success Rate (percentage with visual indicator)

Update Behavior: Live updates with subtle transitions (150-200ms)
```

### Event Log
```
Container: max-h-64, overflow-y-auto
Order: Reverse chronological (newest first)

Entry Format:
- Timestamp: HH:MM:SS.mmm (font-mono, text-xs)
- Event Type: Color-coded indicator dot
- Event Description: text-sm
- Technical Details: font-mono text-xs (collapsed)

Interaction: 
- Hover states on rows
- Click to expand details
- Auto-scroll option
```

---

## Interactive Elements

### Buttons
```
Primary: Solid fill, px-4 py-2, rounded-md
Secondary: Outlined variant, same padding
Ghost: Transparent with hover state
Icon Only: w-10 h-10, centered icon

States: Hover, active, disabled (all clearly distinct)
```

### Form Inputs
```
Text Inputs: border, px-3 py-2, rounded-md
Labels: block mb-1, positioned above input
Matrix Grid: Table-like cell inputs for small matrices
Number Inputs: With increment/decrement controls
Dropdowns: Clear current selection display
```

### Tooltips & Help
```
Trigger: Help icons, hover on technical terms
Content: Brief explanations, packet structure info
Positioning: Auto-adjust to viewport
```

---

## Visual Treatment (No Color Specifications)

### Emphasis Hierarchy
- **Active transmissions**: Most prominent (animated, high contrast)
- **Error states**: Distinct visual treatment with alert indicators
- **Success states**: Positive feedback with checkmarks
- **Idle states**: Muted, lower contrast

### Elevation System
```
Floating Action Buttons: Highest elevation
Modal Overlays: High elevation + backdrop
Panel Cards: shadow-md elevation
Network Canvas: Base level (flat)
```

### Animation Guidelines
```
Packet Flow: Linear easing, 1-2s duration
State Changes: 150-200ms smooth transitions
Panel Collapse: Smooth spring animation
Loading States: Subtle pulse or spinner

Rule: All animations must be functional, not decorative
```

---

## Accessibility Requirements

### Keyboard Navigation
- Tab order: Top → Bottom, Left → Right
- Shortcuts: Space (play/pause), Arrow keys (step through)
- Visible focus indicators on all interactive elements
- Skip links for main content areas

### Screen Reader Support
- Semantic HTML: `<nav>`, `<main>`, `<aside>`, `<section>`
- ARIA labels on visualization elements
- Live regions for event log updates
- Text alternatives for all visual network states

### Visual Accessibility
- WCAG AA contrast ratios minimum
- Icons paired with text labels
- Non-color-dependent indicators (shapes, patterns, icons)
- Minimum 44×44px touch targets
- Focus visible on all interactive elements

---

## Icon System (Lucide React)

```
Network Icons: Network, Server, MonitorDot, Radio, Activity
Control Icons: Play, Pause, StepForward, RotateCcw, Settings
Data Icons: FileText, Lock, Unlock, CheckCircle, XCircle, AlertTriangle
UI Icons: ChevronDown, X, Menu, Eye, Download, Copy

Sizes:
- Inline with text: w-4 h-4
- Button icons: w-5 h-5
- Large feature icons: w-8 h-8
```

---

## Content Strategy

### Educational Context
- Brief section explanations at the top of each panel
- Inline help tooltips for technical terms
- Plain language descriptions paired with technical terminology
- Quick start guide accessible from help icon

### Data Presentation
- **Matrices**: Table grid layout, scrollable for large sizes
- **Packets**: Key-value pairs in monospace
- **Statistics**: Large numbers with descriptive labels
- **Logs**: Timestamp, Event Type, Details in columns

### Microcopy Guidelines
```
Buttons: Action-oriented ("Start Simulation", "Send Packet", "Execute Operation")
Errors: Specific and actionable ("Dimensions must match for addition")
Empty States: Helpful guidance ("No packets sent yet. Click 'Start Simulation' to begin.")
Loading: Progress indication + descriptive text
```

---

## Responsive Strategy

| Breakpoint | Layout | Key Adjustments |
|------------|--------|-----------------|
| **lg+** (1024px+) | Full 2-3 column | All panels visible, side-by-side layout |
| **md** (768px) | 2 columns | Stack some panels, full-width event log |
| **sm** (<768px) | Single column | Accordion sections, bottom sheet controls, maintain canvas aspect ratio |

---

## Images

**No images required** for this technical application. The visual focus is on:
- Network topology visualization (generated via vis-network library)
- Data tables and matrices
- Real-time graphs and charts
- Technical diagrams and packet structures

All visual elements are data-driven and programmatically generated.

---

## Special Considerations

### Network Topology Visualization
- Use vis-network library for interactive graph
- Node styling distinct for Client/Server/Moderator roles
- Animated edges for packet transmission
- Color-coded packet types visible during transit
- Click interactions for node/packet inspection

### Matrix Display Strategy
- For matrices ≤10×10: Editable grid cells
- For matrices >10×10: Preview first 5 rows + element count
- Display dimensions prominently
- Provide download option for large result sets
- Show processing time for operations

### Performance Optimization
- Lazy load large matrix visualizations
- Debounce input changes
- Virtualize event log for long sessions
- Optimize animation frame rate
- Progressive rendering for network topology