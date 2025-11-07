import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3, TrendingUp, TrendingDown, Activity, AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import type { NetworkStatistics } from "@shared/schema";

interface StatisticsDashboardProps {
  statistics: NetworkStatistics;
}

export function StatisticsDashboard({ statistics }: StatisticsDashboardProps) {
  const statCards = [
    {
      label: "Packets Sent",
      value: statistics.packetsSent,
      icon: TrendingUp,
      color: "text-blue-500",
      bgColor: "bg-blue-500/10",
    },
    {
      label: "Packets Received",
      value: statistics.packetsReceived,
      icon: TrendingDown,
      color: "text-green-500",
      bgColor: "bg-green-500/10",
    },
    {
      label: "Packets Dropped",
      value: statistics.packetsDropped,
      icon: XCircle,
      color: "text-red-500",
      bgColor: "bg-red-500/10",
    },
    {
      label: "Retransmissions",
      value: statistics.retransmissions,
      icon: Activity,
      color: "text-amber-500",
      bgColor: "bg-amber-500/10",
    },
    {
      label: "Timeout Events",
      value: statistics.timeouts,
      icon: AlertTriangle,
      color: "text-orange-500",
      bgColor: "bg-orange-500/10",
    },
    {
      label: "Checksum Errors",
      value: statistics.checksumErrors,
      icon: XCircle,
      color: "text-red-500",
      bgColor: "bg-red-500/10",
    },
  ];

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-primary" />
          <CardTitle className="text-xl font-semibold">Network Statistics</CardTitle>
        </div>
        <CardDescription>
          Real-time metrics and performance indicators
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          {statCards.map((stat) => {
            const Icon = stat.icon;
            return (
              <div
                key={stat.label}
                className="p-4 rounded-lg border bg-card space-y-2"
                data-testid={`stat-${stat.label.toLowerCase().replace(/\s+/g, '-')}`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">{stat.label}</span>
                  <div className={`p-1.5 rounded-md ${stat.bgColor}`}>
                    <Icon className={`w-4 h-4 ${stat.color}`} />
                  </div>
                </div>
                <div className="text-2xl font-bold font-mono">{stat.value}</div>
              </div>
            );
          })}
        </div>

        <div className="p-4 rounded-lg border bg-card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground">Success Rate</span>
            <CheckCircle2 className="w-4 h-4 text-green-500" />
          </div>
          <div className="space-y-2">
            <div className="text-2xl font-bold font-mono">
              {statistics.successRate.toFixed(1)}%
            </div>
            <div className="w-full bg-muted rounded-full h-2">
              <div
                className="bg-green-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${statistics.successRate}%` }}
              />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
