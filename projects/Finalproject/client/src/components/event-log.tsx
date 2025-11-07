import { useEffect, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { FileText, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { EventLog, EventType } from "@shared/schema";

interface EventLogProps {
  events: EventLog[];
  autoScroll?: boolean;
  onExport?: () => void;
}

export function EventLogComponent({ events, autoScroll = true, onExport }: EventLogProps) {
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && scrollAreaRef.current) {
      const scrollElement = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollElement) {
        scrollElement.scrollTop = scrollElement.scrollHeight;
      }
    }
  }, [events, autoScroll]);

  const getEventTypeColor = (type: EventType): string => {
    switch (type) {
      case 'packet_sent': return 'bg-blue-500';
      case 'packet_received': return 'bg-green-500';
      case 'packet_dropped': return 'bg-red-500';
      case 'retransmission': return 'bg-amber-500';
      case 'timeout': return 'bg-orange-500';
      case 'checksum_error': return 'bg-red-500';
      case 'ack_received': return 'bg-green-500';
      case 'nack_received': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getEventTypeLabel = (type: EventType): string => {
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const formatTimestamp = (timestamp: number): string => {
    const date = new Date(timestamp);
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const seconds = date.getSeconds().toString().padStart(2, '0');
    const ms = (timestamp % 1000).toString().padStart(3, '0');
    return `${hours}:${minutes}:${seconds}.${ms}`;
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary" />
            <CardTitle className="text-xl font-semibold">Event Log</CardTitle>
          </div>
          {onExport && (
            <Button
              variant="outline"
              size="sm"
              onClick={onExport}
              data-testid="button-export-logs"
            >
              <ChevronDown className="w-4 h-4 mr-2" />
              Export
            </Button>
          )}
        </div>
        <CardDescription>
          Real-time network events and packet transmission history
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea ref={scrollAreaRef} className="h-64 w-full rounded-md border">
          <div className="p-4 space-y-2">
            {events.length === 0 ? (
              <div className="text-sm text-muted-foreground text-center py-8">
                No events yet. Start the simulation to begin logging network activity.
              </div>
            ) : (
              events.map((event) => (
                <div
                  key={event.id}
                  className="p-2 rounded-md hover-elevate border"
                  data-testid={`event-log-${event.id}`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${getEventTypeColor(event.type)}`} />
                    <div className="flex-1 min-w-0 space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <code className="text-xs font-mono text-muted-foreground">
                          {formatTimestamp(event.timestamp)}
                        </code>
                        <Badge variant="secondary" className="text-xs">
                          {getEventTypeLabel(event.type)}
                        </Badge>
                      </div>
                      <div className="text-sm">{event.description}</div>
                      {event.details && Object.keys(event.details).length > 0 && (
                        <details className="text-xs text-muted-foreground font-mono">
                          <summary className="cursor-pointer hover:text-foreground">
                            Technical details
                          </summary>
                          <div className="mt-1 p-2 bg-muted rounded-md">
                            {JSON.stringify(event.details, null, 2)}
                          </div>
                        </details>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
