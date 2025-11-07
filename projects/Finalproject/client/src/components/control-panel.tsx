import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Play, Pause, StepForward, RotateCcw, Settings } from "lucide-react";
import type { SimulationConfig } from "@shared/schema";

interface ControlPanelProps {
  isRunning: boolean;
  config: SimulationConfig;
  onStart: () => void;
  onPause: () => void;
  onStep: () => void;
  onReset: () => void;
  onConfigChange: (config: Partial<SimulationConfig>) => void;
}

export function ControlPanel({
  isRunning,
  config,
  onStart,
  onPause,
  onStep,
  onReset,
  onConfigChange,
}: ControlPanelProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Settings className="w-5 h-5 text-primary" />
          <CardTitle className="text-xl font-semibold">Simulation Control</CardTitle>
        </div>
        <CardDescription>
          Configure and control the UDP network simulation
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex gap-2">
          {isRunning ? (
            <Button
              onClick={onPause}
              variant="secondary"
              className="flex-1"
              data-testid="button-pause"
            >
              <Pause className="w-4 h-4 mr-2" />
              Pause
            </Button>
          ) : (
            <Button
              onClick={onStart}
              variant="default"
              className="flex-1"
              data-testid="button-start"
            >
              <Play className="w-4 h-4 mr-2" />
              Start
            </Button>
          )}
          <Button
            onClick={onStep}
            variant="outline"
            disabled={isRunning}
            data-testid="button-step"
          >
            <StepForward className="w-4 h-4 mr-2" />
            Step
          </Button>
          <Button
            onClick={onReset}
            variant="outline"
            data-testid="button-reset"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset
          </Button>
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="speed-slider">
              Simulation Speed: {config.speed}x
            </Label>
            <Slider
              id="speed-slider"
              min={0.5}
              max={5}
              step={0.5}
              value={[config.speed]}
              onValueChange={(value) => onConfigChange({ speed: value[0] })}
              data-testid="slider-speed"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>0.5x</span>
              <span>1x</span>
              <span>2x</span>
              <span>5x</span>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="packet-loss-slider">
              Packet Loss Rate: {(config.packetLossRate * 100).toFixed(0)}%
            </Label>
            <Slider
              id="packet-loss-slider"
              min={0}
              max={1}
              step={0.05}
              value={[config.packetLossRate]}
              onValueChange={(value) => onConfigChange({ packetLossRate: value[0] })}
              data-testid="slider-packet-loss"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <Label htmlFor="auto-scroll" className="text-sm">
              Auto-scroll Event Log
            </Label>
            <Switch
              id="auto-scroll"
              checked={config.autoScroll}
              onCheckedChange={(checked) => onConfigChange({ autoScroll: checked })}
              data-testid="switch-auto-scroll"
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
