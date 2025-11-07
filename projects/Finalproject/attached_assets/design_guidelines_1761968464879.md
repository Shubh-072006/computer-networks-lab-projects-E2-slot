# Network Simulation Visualizer - Design Guidelines

## Design System: Material Design with Technical Focus

**Principles**: Information clarity, purposeful hierarchy, immediate visual feedback, educational accessibility

---

## Typography

**Font Stack**:
- Primary: Inter/Roboto
- Monospace: JetBrains Mono/Roboto Mono (packet data, logs, technical values)

**Scale**:
```
Page Title:       text-3xl font-bold
Section Headers:  text-xl font-semibold
Subsections:      text-base font-medium
Body:             text-sm
Technical Data:   text-sm font-mono
Labels:           text-xs
```

**Rules**:
- Monospace exclusively for hex/technical data
- Medium line-height for data-dense areas
- Tight line-height for compact logs

---

## Layout & Spacing

**Spacing Units**: 2, 4, 8, 12, 16

```
Component padding:  p-4
Section spacing:    space-y-8
Element gaps:       gap-4
Inline spacing:     space-x-2
Log entries:        space-y-2
Containers:         max-w-screen-2xl mx-auto
Side panels:        w-80 or w-96
```

**Grid Structure**:
- Desktop: 70/30 split (visualization/controls)
- Tablet: 2-column, full-width event log
- Mobile: Single column stack

---

## Core Components

### Dashboard Layout
```
- Top nav: title + global controls (start/stop)
- Main grid: network canvas + side panel
- Bottom: collapsible event log
```

### Panel Cards
```
- shadow-md, rounded-lg, p-4
- Header: icon + text-base font-medium
- Clear section separation
```

### Network Canvas
```
- min-h-[500px], full-width
- Nodes: Client, Server, Moderator
- Edges: Directed arrows, color-coded states
- Packet animation: 1-2s transit, pulse effects
- Labels: REQ, ACK, NACK, DATA badges
```

### Control Panel
```
Buttons: Start, Pause, Step, Reset (gap-2, icon + text)
Speed slider: 1x, 2x, 5x
Matrix input: Tabs (Manual/Upload/Random)
Operation selector: Add, Subtract, Multiply, Transpose
Execute: Prominent primary button
```

### Packet Inspector
```
Accordion/fixed panel sections:
- Header Info, Payload, Checksum, Metadata
- Monospace formatting throughout
- Copy-to-clipboard buttons
- Syntax highlighting for encrypted/decrypted
```

### Statistics Dashboard
```
grid-cols-2 gap-4 cards:
- Metric value: text-2xl font-bold
- Label: text-sm + icon
- Metrics: Sent, Received, Retransmissions, Timeouts, Success Rate
- Live updates with subtle transitions
- Status indicators (success/warning/error)
```

### Event Log
```
max-h-64 overflow-y-auto, reverse chronological
- Monospace timestamps: HH:MM:SS.mmm
- Colored event type indicators
- Row hover states, space-y-1
```

### Interactive Elements

**Buttons**:
```
Primary:   px-4 py-2, solid, rounded-md
Secondary: Outlined/ghost variants
Icon:      w-10 h-10, centered
```

**Forms**:
```
Inputs:  border, px-3 py-2
Labels:  block mb-1, above inputs
Matrix:  Table-like cell inputs
Upload:  border-dashed drop zone
```

**Tooltips**: Technical terms, packet data on click, help icons

---

## Information Architecture

### Primary Views (Tab Navigation)

1. **Simulation** (default)
   - Network topology (top center)
   - Control panel (top right)
   - Statistics sidebar (right)
   - Event log (bottom dock)

2. **Matrix Operations**
   - Input panels (left)
   - Operation selector (center top)
   - Result display (right)
   - Packet visualization (center bottom)

3. **Protocol Inspector**
   - Packet structure breakdown
   - State machine steps
   - Timing diagrams

---

## Visual Treatment

**Emphasis**:
- Active transmissions: Animated, prominent
- Errors: Distinct visual treatment
- Success: Positive feedback
- Idle: Muted

**Elevation**:
```
Floating buttons: Highest
Modals:          High + backdrop
Cards:           shadow-md
Canvas:          Base (flat)
```

**Animation**:
```
Packet flow:     Linear, 1-2s
State changes:   150-200ms
Panel collapse:  Smooth spring
```
All animations functional, not decorative.

---

## Accessibility

**Keyboard**:
- Tab order: top→bottom, left→right
- Shortcuts: Space (play/pause), arrows (step)
- Visible focus indicators

**Screen Readers**:
- Semantic HTML (nav, main, aside, section)
- ARIA labels on visualizations
- Live regions for event updates
- Text alternatives for visual states

**Visual**:
- WCAG AA contrast
- Icons + text labels
- Non-color indicators (shapes, icons)
- Min 44x44px touch targets

---

## Icons & Assets

**Icons** (Lucide React):
```
Network:  Network, Server, MonitorDot, Radio, Activity
Controls: Play, Pause, StepForward, RotateCcw
Data:     FileText, Lock, Unlock, CheckCircle, XCircle, AlertTriangle
Sizes:    w-4 h-4 (inline), w-5 h-5 (buttons)
```

**Diagrams**: Optional protocol/packet structure SVGs (minimal, functional)

---

## Content Guidelines

**Educational Context**:
- Brief section explanations
- Inline help tooltips
- Plain language + technical terms
- Quick start guide

**Data Presentation**:
- Matrices: Table grid
- Packets: Key-value pairs, monospace
- Stats: Large numbers + labels
- Logs: Time, Event, Details columns

**Microcopy**:
```
Buttons:      Action-oriented ("Start Simulation", "Send Packet")
Errors:       Specific, actionable
Empty states: "No packets sent yet. Click 'Start Simulation' to begin."
Loading:      Progress + descriptive text
```

---

## Responsive Breakpoints

| Size | Layout | Notes |
|------|--------|-------|
| **lg+** | 2-3 columns | All panels visible, full-width canvas |
| **md** | 2 columns | Full-width log, accessible top controls |
| **sm** | Stack | Min aspect ratio canvas, accordion sections, bottom sheet controls |