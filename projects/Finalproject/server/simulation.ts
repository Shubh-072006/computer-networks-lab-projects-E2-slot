import { WebSocket } from 'ws';
import { randomUUID } from 'crypto';
import type {
  Packet,
  EventLog,
  NetworkStatistics,
  SimulationConfig,
  WSMessage,
} from '@shared/schema';

export class UDPSimulation {
  private clients: Set<WebSocket> = new Set();
  private statistics: NetworkStatistics = {
    packetsSent: 0,
    packetsReceived: 0,
    packetsDropped: 0,
    retransmissions: 0,
    timeouts: 0,
    checksumErrors: 0,
    successRate: 100,
  };
  private events: EventLog[] = [];
  private config: SimulationConfig = {
    speed: 1,
    packetLossRate: 0,
    autoScroll: true,
  };
  private isRunning = false;
  private intervalId?: NodeJS.Timeout;

  addClient(ws: WebSocket) {
    this.clients.add(ws);
    this.sendToClient(ws, {
      type: 'statistics_update',
      payload: this.statistics,
    });
    this.sendToClient(ws, {
      type: 'simulation_state',
      payload: { isRunning: this.isRunning, config: this.config },
    });
  }

  removeClient(ws: WebSocket) {
    this.clients.delete(ws);
  }

  private sendToClient(ws: WebSocket, message: WSMessage) {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    }
  }

  private broadcast(message: WSMessage) {
    this.clients.forEach((client) => {
      this.sendToClient(client, message);
    });
  }

  private generateChecksum(data: string): string {
    let hash = 0;
    for (let i = 0; i < data.length; i++) {
      const char = data.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(16).padStart(8, '0');
  }

  private createPacket(senderId: string, receiverId: string): Packet {
    const types: Array<'REQ' | 'ACK' | 'NACK' | 'DATA'> = ['REQ', 'ACK', 'NACK', 'DATA'];
    const type = types[Math.floor(Math.random() * types.length)];
    const payload = `Packet data ${this.statistics.packetsSent + 1} - ${Date.now()}`;
    
    return {
      id: randomUUID(),
      type,
      sequenceNumber: this.statistics.packetsSent + 1,
      senderId,
      receiverId,
      payload,
      checksum: this.generateChecksum(payload),
      timestamp: Date.now(),
      encrypted: Math.random() > 0.5,
      chunks: Math.floor(Math.random() * 5) + 1,
    };
  }

  private logEvent(event: Omit<EventLog, 'id' | 'timestamp'>) {
    const fullEvent: EventLog = {
      ...event,
      id: randomUUID(),
      timestamp: Date.now(),
    };
    this.events.push(fullEvent);
    this.broadcast({
      type: 'event_log' as any,
      payload: fullEvent,
    });
  }

  private updateStatistics(update: Partial<NetworkStatistics>) {
    this.statistics = { ...this.statistics, ...update };
    
    if (this.statistics.packetsSent > 0) {
      this.statistics.successRate = 
        (this.statistics.packetsReceived / this.statistics.packetsSent) * 100;
    }

    this.broadcast({
      type: 'statistics_update',
      payload: this.statistics,
    });
  }

  sendPacket() {
    const nodes = ['client-1', 'server-1', 'moderator-1'];
    const senderId = nodes[Math.floor(Math.random() * nodes.length)];
    const receiverId = nodes.filter(n => n !== senderId)[
      Math.floor(Math.random() * (nodes.length - 1))
    ];

    const packet = this.createPacket(senderId, receiverId);

    this.broadcast({
      type: 'packet_sent',
      payload: packet,
    });

    this.updateStatistics({
      packetsSent: this.statistics.packetsSent + 1,
    });

    this.logEvent({
      type: 'packet_sent',
      description: `Packet ${packet.type} #${packet.sequenceNumber} sent from ${senderId} to ${receiverId}`,
      packetId: packet.id,
      details: {
        type: packet.type,
        sender: senderId,
        receiver: receiverId,
      },
    });

    const shouldDrop = Math.random() < this.config.packetLossRate;
    
    setTimeout(() => {
      if (shouldDrop) {
        this.broadcast({
          type: 'packet_dropped',
          payload: packet,
        });

        this.updateStatistics({
          packetsDropped: this.statistics.packetsDropped + 1,
        });

        this.logEvent({
          type: 'packet_dropped',
          description: `Packet ${packet.type} #${packet.sequenceNumber} dropped`,
          packetId: packet.id,
        });
      } else {
        this.broadcast({
          type: 'packet_received',
          payload: packet,
        });

        this.updateStatistics({
          packetsReceived: this.statistics.packetsReceived + 1,
        });

        this.logEvent({
          type: 'packet_received',
          description: `Packet ${packet.type} #${packet.sequenceNumber} received by ${receiverId}`,
          packetId: packet.id,
        });
      }
    }, 2000 / this.config.speed);
  }

  start() {
    if (this.isRunning) return;

    this.isRunning = true;
    this.broadcast({
      type: 'simulation_state',
      payload: { isRunning: true, config: this.config },
    });

    this.intervalId = setInterval(() => {
      this.sendPacket();
    }, 2000 / this.config.speed);
  }

  pause() {
    if (!this.isRunning) return;

    this.isRunning = false;
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = undefined;
    }

    this.broadcast({
      type: 'simulation_state',
      payload: { isRunning: false, config: this.config },
    });
  }

  step() {
    this.sendPacket();
  }

  reset() {
    this.pause();
    this.statistics = {
      packetsSent: 0,
      packetsReceived: 0,
      packetsDropped: 0,
      retransmissions: 0,
      timeouts: 0,
      checksumErrors: 0,
      successRate: 100,
    };
    this.events = [];

    this.broadcast({
      type: 'statistics_update',
      payload: this.statistics,
    });
  }

  updateConfig(newConfig: Partial<SimulationConfig>) {
    this.config = { ...this.config, ...newConfig };

    if (this.isRunning && this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = setInterval(() => {
        this.sendPacket();
      }, 2000 / this.config.speed);
    }

    this.broadcast({
      type: 'simulation_state',
      payload: { isRunning: this.isRunning, config: this.config },
    });
  }

  getEvents(): EventLog[] {
    return this.events;
  }
}
