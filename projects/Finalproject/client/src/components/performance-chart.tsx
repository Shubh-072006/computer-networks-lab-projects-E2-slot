import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { TrendingUp, Database } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { PerformanceMetric } from "@shared/schema";

interface PerformanceChartProps {
  metrics: PerformanceMetric[];
}

export function PerformanceChart({ metrics }: PerformanceChartProps) {
  const validMetrics = metrics.filter(
    (m) => typeof m.executionTime === 'number' && !isNaN(m.executionTime)
  );

  const getChartData = () => {
    const grouped = new Map<string, PerformanceMetric[]>();
    
    validMetrics.forEach((metric) => {
      const key = metric.operation;
      if (!grouped.has(key)) {
        grouped.set(key, []);
      }
      grouped.get(key)?.push(metric);
    });

    const operations = Array.from(grouped.keys());
    const allSizes = new Set<string>();
    validMetrics.forEach((m) => allSizes.add(m.matrixSize));
    const sortedSizes = Array.from(allSizes).sort((a, b) => {
      const [aRows] = a.split('×').map(Number);
      const [bRows] = b.split('×').map(Number);
      return aRows - bRows;
    });

    return sortedSizes.map((size) => {
      const dataPoint: any = { size };
      operations.forEach((op) => {
        const metricsForOp = grouped.get(op) || [];
        const metricForSize = metricsForOp.find((m) => m.matrixSize === size);
        dataPoint[op] = metricForSize?.executionTime || null;
      });
      return dataPoint;
    });
  };

  const getOperations = () => {
    const ops = new Set<string>();
    validMetrics.forEach((m) => ops.add(m.operation));
    return Array.from(ops);
  };

  const colors = [
    "#3b82f6", // blue
    "#10b981", // green
    "#f59e0b", // amber
    "#ef4444", // red
    "#8b5cf6", // purple
    "#ec4899", // pink
  ];

  const chartData = getChartData();
  const operations = getOperations();

  if (validMetrics.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary" />
            <CardTitle className="text-xl font-semibold">Performance Metrics</CardTitle>
          </div>
          <CardDescription>
            Execution time analysis across different matrix sizes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground text-center py-12 border border-dashed rounded-md">
            No performance data yet. Execute matrix operations to start tracking performance metrics.
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary" />
            <CardTitle className="text-xl font-semibold">Performance Metrics</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-muted-foreground" />
            <Badge variant="secondary" className="text-xs font-mono">
              {validMetrics.length} operations
            </Badge>
          </div>
        </div>
        <CardDescription>
          Execution time analysis across different matrix sizes and operations
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="size"
                className="text-xs"
                label={{ value: 'Matrix Size', position: 'insideBottom', offset: -5 }}
              />
              <YAxis
                className="text-xs"
                label={{ value: 'Execution Time (ms)', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px',
                }}
                labelStyle={{ color: 'hsl(var(--foreground))' }}
              />
              <Legend wrapperStyle={{ paddingTop: '10px' }} />
              {operations.map((op, idx) => (
                <Line
                  key={op}
                  type="monotone"
                  dataKey={op}
                  stroke={colors[idx % colors.length]}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                  name={op.charAt(0).toUpperCase() + op.slice(1)}
                  connectNulls
                />
              ))}
            </LineChart>
          </ResponsiveContainer>

          <div className="grid grid-cols-2 gap-3">
            {operations.map((op, idx) => {
              const opMetrics = validMetrics.filter((m) => m.operation === op);
              const avgTime = opMetrics.reduce((sum, m) => sum + m.executionTime, 0) / opMetrics.length;
              const maxTime = Math.max(...opMetrics.map((m) => m.executionTime));
              
              return (
                <div
                  key={op}
                  className="p-3 border rounded-md space-y-1"
                  data-testid={`perf-stat-${op}`}
                >
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: colors[idx % colors.length] }}
                    />
                    <span className="text-sm font-medium capitalize">{op}</span>
                  </div>
                  <div className="text-xs text-muted-foreground space-y-0.5 font-mono">
                    <div>Avg: {avgTime.toFixed(2)}ms</div>
                    <div>Max: {maxTime.toFixed(2)}ms</div>
                    <div>Count: {opMetrics.length}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
