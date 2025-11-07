import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Network, Activity } from "lucide-react";
import type { NetworkNode, Packet } from "@shared/schema";

interface NetworkVisualizationProps {
  nodes: NetworkNode[];
  activePackets: Packet[];
  onNodeClick?: (nodeId: string) => void;
  onPacketClick?: (packetId: string) => void;
}

interface AnimatedPacket extends Packet {
  progress: number;
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
}

export function NetworkVisualization({
  nodes,
  activePackets,
  onNodeClick,
  onPacketClick,
}: NetworkVisualizationProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [animatedPackets, setAnimatedPackets] = useState<Map<string, AnimatedPacket>>(new Map());
  const animationFrameRef = useRef<number>();

  const getNodePosition = (nodeId: string): { x: number, y: number } => {
    const node = nodes.find(n => n.id === nodeId);
    if (node?.x !== undefined && node?.y !== undefined) {
      return { x: node.x, y: node.y };
    }

    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(canvas.width, canvas.height) / 3;

    const nodeIndex = nodes.findIndex(n => n.id === nodeId);
    const totalNodes = nodes.length;
    const angle = (nodeIndex / totalNodes) * 2 * Math.PI - Math.PI / 2;

    return {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  };

  const getPacketColor = (type: string): string => {
    switch (type) {
      case 'REQ': return '#3b82f6'; // blue
      case 'ACK': return '#10b981'; // green
      case 'NACK': return '#ef4444'; // red
      case 'DATA': return '#8b5cf6'; // purple
      default: return '#6b7280'; // gray
    }
  };

  const drawNetwork = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw edges between nodes
    ctx.strokeStyle = 'rgba(100, 116, 139, 0.3)';
    ctx.lineWidth = 2;
    nodes.forEach((fromNode, i) => {
      nodes.slice(i + 1).forEach(toNode => {
        const from = getNodePosition(fromNode.id);
        const to = getNodePosition(toNode.id);
        
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.stroke();
        
        // Draw arrow
        const angle = Math.atan2(to.y - from.y, to.x - from.x);
        const headLen = 10;
        ctx.beginPath();
        ctx.moveTo(to.x, to.y);
        ctx.lineTo(
          to.x - headLen * Math.cos(angle - Math.PI / 6),
          to.y - headLen * Math.sin(angle - Math.PI / 6)
        );
        ctx.moveTo(to.x, to.y);
        ctx.lineTo(
          to.x - headLen * Math.cos(angle + Math.PI / 6),
          to.y - headLen * Math.sin(angle + Math.PI / 6)
        );
        ctx.stroke();
      });
    });

    // Draw nodes
    nodes.forEach(node => {
      const pos = getNodePosition(node.id);
      const radius = 30;

      ctx.beginPath();
      ctx.arc(pos.x, pos.y, radius, 0, 2 * Math.PI);
      
      switch (node.type) {
        case 'client':
          ctx.fillStyle = '#3b82f6';
          break;
        case 'server':
          ctx.fillStyle = '#10b981';
          break;
        case 'moderator':
          ctx.fillStyle = '#f59e0b';
          break;
      }
      
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 3;
      ctx.stroke();

      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 12px Inter';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(node.label.charAt(0).toUpperCase(), pos.x, pos.y);

      ctx.fillStyle = '#1f2937';
      ctx.font = '11px Inter';
      ctx.fillText(node.label, pos.x, pos.y + radius + 15);
    });

    // Draw animated packets
    animatedPackets.forEach(packet => {
      const x = packet.fromX + (packet.toX - packet.fromX) * packet.progress;
      const y = packet.fromY + (packet.toY - packet.fromY) * packet.progress;
      
      ctx.beginPath();
      ctx.arc(x, y, 8, 0, 2 * Math.PI);
      ctx.fillStyle = getPacketColor(packet.type);
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Pulse effect
      ctx.beginPath();
      ctx.arc(x, y, 12 + Math.sin(Date.now() / 200) * 3, 0, 2 * Math.PI);
      ctx.strokeStyle = getPacketColor(packet.type) + '40';
      ctx.lineWidth = 2;
      ctx.stroke();
    });
  };

  const animate = () => {
    setAnimatedPackets(prev => {
      const updated = new Map(prev);
      let hasChanges = false;

      updated.forEach((packet, id) => {
        if (packet.progress < 1) {
          packet.progress += 0.01;
          hasChanges = true;
        } else {
          updated.delete(id);
          hasChanges = true;
        }
      });

      return hasChanges ? updated : prev;
    });

    drawNetwork();
    animationFrameRef.current = requestAnimationFrame(animate);
  };

  useEffect(() => {
    activePackets.forEach(packet => {
      if (!animatedPackets.has(packet.id)) {
        const from = getNodePosition(packet.senderId);
        const to = getNodePosition(packet.receiverId);
        
        setAnimatedPackets(prev => new Map(prev).set(packet.id, {
          ...packet,
          progress: 0,
          fromX: from.x,
          fromY: from.y,
          toX: to.x,
          toY: to.y,
        }));
      }
    });
  }, [activePackets]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const updateSize = () => {
      const container = canvas.parentElement;
      if (container) {
        canvas.width = container.clientWidth;
        canvas.height = Math.max(500, container.clientHeight);
      }
    };

    updateSize();
    window.addEventListener('resize', updateSize);

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('resize', updateSize);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [nodes]);

  useEffect(() => {
    drawNetwork();
  }, [nodes, animatedPackets]);

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Network className="w-5 h-5 text-primary" />
            <CardTitle className="text-xl font-semibold">Network Topology</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-mono text-muted-foreground">
              {activePackets.length} active
            </span>
          </div>
        </div>
        <CardDescription>
          Interactive visualization of UDP packet transmission
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex gap-2 flex-wrap">
            <Badge variant="secondary" className="gap-1">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span className="text-xs">Client</span>
            </Badge>
            <Badge variant="secondary" className="gap-1">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-xs">Server</span>
            </Badge>
            <Badge variant="secondary" className="gap-1">
              <div className="w-3 h-3 rounded-full bg-amber-500"></div>
              <span className="text-xs">Moderator</span>
            </Badge>
          </div>
          
          <div className="border rounded-lg overflow-hidden bg-card" data-testid="canvas-network">
            <canvas
              ref={canvasRef}
              className="w-full min-h-[500px] cursor-pointer"
              onClick={(e) => {
                const canvas = canvasRef.current;
                if (!canvas) return;
                
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                nodes.forEach(node => {
                  const pos = getNodePosition(node.id);
                  const dist = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2);
                  if (dist < 30 && onNodeClick) {
                    onNodeClick(node.id);
                  }
                });
              }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
