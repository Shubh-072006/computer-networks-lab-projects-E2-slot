import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { FileText, Copy, CheckCircle, Lock, Unlock } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import type { Packet } from "@shared/schema";

interface PacketInspectorProps {
  packet: Packet | null;
}

export function PacketInspector({ packet }: PacketInspectorProps) {
  const { toast } = useToast();

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied to clipboard",
      description: `${label} copied successfully`,
    });
  };

  if (!packet) {
    return (
      <Card className="h-full">
        <CardHeader>
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary" />
            <CardTitle className="text-xl font-semibold">Packet Inspector</CardTitle>
          </div>
          <CardDescription>
            Click on a packet in the network visualization to inspect its details
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground text-center py-12 border border-dashed rounded-md">
            No packet selected
          </div>
        </CardContent>
      </Card>
    );
  }

  const getPacketTypeColor = (type: string) => {
    switch (type) {
      case 'REQ': return 'bg-blue-500';
      case 'ACK': return 'bg-green-500';
      case 'NACK': return 'bg-red-500';
      case 'DATA': return 'bg-purple-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-primary" />
          <CardTitle className="text-xl font-semibold">Packet Inspector</CardTitle>
        </div>
        <CardDescription>
          Detailed packet information and payload inspection
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Accordion type="multiple" defaultValue={["header", "payload"]} className="space-y-2">
          <AccordionItem value="header" className="border rounded-md px-4">
            <AccordionTrigger className="hover:no-underline">
              <span className="text-base font-medium">Header Information</span>
            </AccordionTrigger>
            <AccordionContent className="space-y-3 pt-2">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <div className="text-xs text-muted-foreground">Packet ID</div>
                  <div className="flex items-center gap-2">
                    <code className="text-xs font-mono">{packet.id}</code>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={() => copyToClipboard(packet.id, "Packet ID")}
                      data-testid="button-copy-id"
                    >
                      <Copy className="w-3 h-3" />
                    </Button>
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="text-xs text-muted-foreground">Type</div>
                  <Badge className={getPacketTypeColor(packet.type)}>
                    {packet.type}
                  </Badge>
                </div>

                <div className="space-y-1">
                  <div className="text-xs text-muted-foreground">Sequence #</div>
                  <code className="text-xs font-mono">{packet.sequenceNumber}</code>
                </div>

                <div className="space-y-1">
                  <div className="text-xs text-muted-foreground">Timestamp</div>
                  <code className="text-xs font-mono">
                    {new Date(packet.timestamp).toLocaleTimeString()}.
                    {packet.timestamp % 1000}
                  </code>
                </div>

                <div className="space-y-1">
                  <div className="text-xs text-muted-foreground">Sender</div>
                  <code className="text-xs font-mono">{packet.senderId}</code>
                </div>

                <div className="space-y-1">
                  <div className="text-xs text-muted-foreground">Receiver</div>
                  <code className="text-xs font-mono">{packet.receiverId}</code>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="payload" className="border rounded-md px-4">
            <AccordionTrigger className="hover:no-underline">
              <span className="text-base font-medium">Payload Display</span>
            </AccordionTrigger>
            <AccordionContent className="space-y-3 pt-2">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {packet.encrypted ? (
                      <Lock className="w-4 h-4 text-amber-500" />
                    ) : (
                      <Unlock className="w-4 h-4 text-green-500" />
                    )}
                    <span className="text-xs text-muted-foreground">
                      {packet.encrypted ? "Encrypted" : "Plain text"}
                    </span>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => copyToClipboard(packet.payload, "Payload")}
                    data-testid="button-copy-payload"
                  >
                    <Copy className="w-3 h-3" />
                  </Button>
                </div>
                <div className={`p-3 rounded-md border font-mono text-xs break-all ${
                  packet.encrypted ? 'bg-amber-500/5 border-amber-500/20' : 'bg-card'
                }`}>
                  {packet.payload}
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="checksum" className="border rounded-md px-4">
            <AccordionTrigger className="hover:no-underline">
              <span className="text-base font-medium">Checksum & Integrity</span>
            </AccordionTrigger>
            <AccordionContent className="space-y-3 pt-2">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="text-xs text-muted-foreground">Checksum</div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => copyToClipboard(packet.checksum, "Checksum")}
                    data-testid="button-copy-checksum"
                  >
                    <Copy className="w-3 h-3" />
                  </Button>
                </div>
                <div className="p-3 rounded-md border bg-card">
                  <code className="text-xs font-mono break-all">{packet.checksum}</code>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="text-muted-foreground">Integrity verified</span>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="metadata" className="border rounded-md px-4">
            <AccordionTrigger className="hover:no-underline">
              <span className="text-base font-medium">Metadata</span>
            </AccordionTrigger>
            <AccordionContent className="space-y-3 pt-2">
              <div className="grid grid-cols-2 gap-3">
                {packet.chunks !== undefined && (
                  <div className="space-y-1">
                    <div className="text-xs text-muted-foreground">Chunks</div>
                    <code className="text-xs font-mono">{packet.chunks}</code>
                  </div>
                )}
                <div className="space-y-1">
                  <div className="text-xs text-muted-foreground">Size</div>
                  <code className="text-xs font-mono">{packet.payload.length} bytes</code>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>
  );
}
