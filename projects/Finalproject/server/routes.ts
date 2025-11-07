import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer } from "ws";
import { MatrixOperations } from "./matrix-operations";
import { UDPSimulation } from "./simulation";
import { matrixOperationInputSchema } from "@shared/schema";
import { z } from "zod";

const simulation = new UDPSimulation();

export async function registerRoutes(app: Express): Promise<Server> {
  const httpServer = createServer(app);

  // WebSocket server for real-time simulation
  const wss = new WebSocketServer({ server: httpServer, path: "/ws" });

  wss.on("connection", (ws) => {
    console.log("WebSocket client connected");
    simulation.addClient(ws);

    ws.on("message", (message) => {
      try {
        const data = JSON.parse(message.toString());

        switch (data.type) {
          case "start":
            simulation.start();
            break;
          case "pause":
            simulation.pause();
            break;
          case "step":
            simulation.step();
            break;
          case "reset":
            simulation.reset();
            break;
          case "config":
            simulation.updateConfig(data.payload);
            break;
        }
      } catch (error) {
        console.error("WebSocket message error:", error);
      }
    });

    ws.on("close", () => {
      console.log("WebSocket client disconnected");
      simulation.removeClient(ws);
    });
  });

  // Matrix operation endpoint
  app.post("/api/matrix/execute", async (req, res) => {
    try {
      const validated = matrixOperationInputSchema.parse(req.body);
      const startTime = performance.now();

      let result: any = null;

      switch (validated.operation) {
        case "add":
          if (!validated.matrixB) {
            throw new Error("Matrix B is required for addition");
          }
          result = MatrixOperations.add(validated.matrixA, validated.matrixB);
          break;
        case "subtract":
          if (!validated.matrixB) {
            throw new Error("Matrix B is required for subtraction");
          }
          result = MatrixOperations.subtract(validated.matrixA, validated.matrixB);
          break;
        case "multiply":
          if (!validated.matrixB) {
            throw new Error("Matrix B is required for multiplication");
          }
          result = MatrixOperations.multiply(validated.matrixA, validated.matrixB);
          break;
        case "transpose":
          result = MatrixOperations.transpose(validated.matrixA);
          break;
        case "determinant":
          result = MatrixOperations.determinant(validated.matrixA);
          break;
        case "inverse":
          result = MatrixOperations.inverse(validated.matrixA);
          break;
      }

      const executionTime = performance.now() - startTime;

      res.json({
        result,
        executionTime,
      });
    } catch (error) {
      if (error instanceof z.ZodError) {
        res.status(400).json({
          result: null,
          executionTime: 0,
          error: "Invalid input: " + error.errors.map(e => e.message).join(", "),
        });
      } else if (error instanceof Error) {
        res.status(400).json({
          result: null,
          executionTime: 0,
          error: error.message,
        });
      } else {
        res.status(500).json({
          result: null,
          executionTime: 0,
          error: "An unexpected error occurred",
        });
      }
    }
  });

  // Get event logs
  app.get("/api/events", async (req, res) => {
    try {
      const events = simulation.getEvents();
      res.json(events);
    } catch (error) {
      res.status(500).json({ error: "Failed to retrieve events" });
    }
  });

  return httpServer;
}
