import { Network } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";

export function Header() {
  return (
    <header className="border-b bg-background sticky top-0 z-50">
      <div className="max-w-screen-2xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Network className="w-6 h-6 text-primary" />
          <h1 className="text-xl font-bold">UDP Network Simulator</h1>
        </div>
        <ThemeToggle />
      </div>
    </header>
  );
}
