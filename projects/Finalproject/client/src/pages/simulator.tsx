import { useState, useEffect, useRef } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MatrixOperations } from "@/components/matrix-operations";
import { NetworkVisualization } from "@/components/network-visualization";
import { PacketInspector } from "@/components/packet-inspector";
import { StatisticsDashboard } from "@/components/statistics-dashboard";
import { EventLogComponent } from "@/components/event-log";
import { ControlPanel } from "@/components/control-panel";
import { PerformanceChart } from "@/components/performance-chart";
import { useToast } from "@/hooks/use-toast";
import type {
  NetworkNode,
  Packet,
  EventLog,
  NetworkStatistics,
  SimulationConfig,
  Matrix,
  MatrixOperationResult,
  WSMessage,
  PerformanceMetric,
} from "@shared/schema";

export default function Simulator() {
  const { toast } = useToast();
  const [isRunning, setIsRunning] = useState(false);
  const [selectedPacket, setSelectedPacket] = useState<Packet | null>(null);
  const [config, setConfig] = useState<SimulationConfig>({
    speed: 1,
    packetLossRate: 0,
    autoScroll: true,
  });

  const [nodes] = useState<NetworkNode[]>([
    { id: "client-1", type: "client", label: "Client 1" },
    { id: "server-1", type: "server", label: "Server" },
    { id: "moderator-1", type: "moderator", label: "Moderator" },
  ]);

  const [activePackets, setActivePackets] = useState<Packet[]>([]);
  const [events, setEvents] = useState<EventLog[]>([]);
  const [statistics, setStatistics] = useState<NetworkStatistics>({
    packetsSent: 0,
    packetsReceived: 0,
    packetsDropped: 0,
    retransmissions: 0,
    timeouts: 0,
    checksumErrors: 0,
    successRate: 100,
  });
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetric[]>([]);

  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("WebSocket connected");
    };

    ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);

        switch (message.type) {
          case 'packet_sent':
            const packetSent = message.payload as Packet;
            setActivePackets((prev) => [...prev, packetSent]);
            
            setTimeout(() => {
              setActivePackets((prev) => prev.filter((p) => p.id !== packetSent.id));
            }, 2000 / config.speed);
            break;

          case 'packet_received':
            const packetReceived = message.payload as Packet;
            setActivePackets((prev) => prev.filter((p) => p.id !== packetReceived.id));
            break;

          case 'packet_dropped':
            const packetDropped = message.payload as Packet;
            setActivePackets((prev) => prev.filter((p) => p.id !== packetDropped.id));
            break;

          case 'event_log':
            const eventLog = message.payload as EventLog;
            setEvents((prev) => [...prev, eventLog]);
            break;

          case 'statistics_update':
            setStatistics(message.payload);
            break;

          case 'simulation_state':
            setIsRunning(message.payload.isRunning);
            if (message.payload.config) {
              setConfig(message.payload.config);
            }
            break;
        }
      } catch (error) {
        console.error("WebSocket message error:", error);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      toast({
        title: "Connection Error",
        description: "Failed to connect to simulation server",
        variant: "destructive",
      });
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [toast]);

  const sendWSMessage = (type: string, payload?: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, payload }));
    }
  };

  const handleMatrixOperation = async (
    operation: string,
    matrixA: Matrix,
    matrixB?: Matrix
  ): Promise<MatrixOperationResult> => {
    try {
      const response = await fetch('/api/matrix/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ operation, matrixA, matrixB }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Matrix operation failed');
      }

      const result = await response.json();
      
      if (!result.error && typeof result.executionTime === 'number' && !isNaN(result.executionTime)) {
        const metric: PerformanceMetric = {
          id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          operation,
          matrixSize: `${matrixA.rows}×${matrixA.cols}`,
          rows: matrixA.rows,
          cols: matrixA.cols,
          executionTime: result.executionTime,
          timestamp: Date.now(),
        };
        setPerformanceMetrics((prev) => [...prev, metric]);
      }
      
      return result;
    } catch (error) {
      return {
        result: null,
        executionTime: 0,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  };

  const handleStart = () => {
    sendWSMessage('start');
  };

  const handlePause = () => {
    sendWSMessage('pause');
  };

  const handleStep = () => {
    sendWSMessage('step');
  };

  const handleReset = () => {
    sendWSMessage('reset');
    setActivePackets([]);
    setEvents([]);
    setSelectedPacket(null);
  };

  const handleConfigChange = (newConfig: Partial<SimulationConfig>) => {
    const updated = { ...config, ...newConfig };
    setConfig(updated);
    sendWSMessage('config', updated);
  };

  const handleNodeClick = (nodeId: string) => {
    console.log("Node clicked:", nodeId);
  };

  const handlePacketClick = (packetId: string) => {
    const packet = activePackets.find((p) => p.id === packetId);
    if (packet) {
      setSelectedPacket(packet);
    }
  };

  const handleExportLogs = () => {
    const dataStr = JSON.stringify(events, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `network-events-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);

    toast({
      title: "Export Successful",
      description: `Exported ${events.length} events to JSON file`,
    });
  };

  return (
    <div className="min-h-screen bg-background">
      <Tabs defaultValue="simulation" className="h-full">
        <div className="border-b">
          <div className="max-w-screen-2xl mx-auto px-4">
            <TabsList className="h-12">
              <TabsTrigger value="matrix" data-testid="tab-matrix">
                Matrix Operations
              </TabsTrigger>
              <TabsTrigger value="simulation" data-testid="tab-simulation">
                UDP Simulation
              </TabsTrigger>
            </TabsList>
          </div>
        </div>

        <TabsContent value="matrix" className="mt-0 p-4">
          <div className="max-w-screen-2xl mx-auto space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <MatrixOperations onExecute={handleMatrixOperation} />
              <PerformanceChart metrics={performanceMetrics} />
            </div>
          </div>
        </TabsContent>

        <TabsContent value="simulation" className="mt-0 h-[calc(100vh-48px)]">
          <div className="max-w-screen-2xl mx-auto h-full flex flex-col">
            {/* Main content with 70/30 split - fixed height */}
            <div className="h-[65%] grid grid-cols-1 lg:grid-cols-10 gap-4 p-4">
              {/* Left: Network canvas (70%) */}
              <div className="lg:col-span-7 h-full">
                <NetworkVisualization
                  nodes={nodes}
                  activePackets={activePackets}
                  onNodeClick={handleNodeClick}
                  onPacketClick={handlePacketClick}
                />
              </div>
              
              {/* Right: Control panels (30%) - fixed height with scroll */}
              <div className="lg:col-span-3 h-full overflow-y-auto space-y-4">
                <ControlPanel
                  isRunning={isRunning}
                  config={config}
                  onStart={handleStart}
                  onPause={handlePause}
                  onStep={handleStep}
                  onReset={handleReset}
                  onConfigChange={handleConfigChange}
                />
                <StatisticsDashboard statistics={statistics} />
                <PacketInspector packet={selectedPacket} />
              </div>
            </div>

            {/* Bottom: Docked event log - fixed height panel */}
            <div className="h-[35%] border-t bg-background flex flex-col">
              <div className="flex-1 p-4 overflow-hidden">
                <EventLogComponent
                  events={events}
                  autoScroll={config.autoScroll}
                  onExport={handleExportLogs}
                />
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
