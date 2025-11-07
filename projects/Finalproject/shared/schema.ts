import { sql } from "drizzle-orm";
import { pgTable, text, varchar, integer, real, boolean, jsonb, timestamp } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// User table (from template)
export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

// Matrix Operations table for storing operation history
export const matrixOperations = pgTable("matrix_operations", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  operation: varchar("operation", { length: 50 }).notNull(),
  matrixARows: integer("matrix_a_rows").notNull(),
  matrixACols: integer("matrix_a_cols").notNull(),
  matrixAData: jsonb("matrix_a_data").notNull(),
  matrixBRows: integer("matrix_b_rows"),
  matrixBCols: integer("matrix_b_cols"),
  matrixBData: jsonb("matrix_b_data"),
  resultData: jsonb("result_data"),
  executionTime: real("execution_time").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const insertMatrixOperationSchema = createInsertSchema(matrixOperations).omit({
  id: true,
  createdAt: true,
});

export type InsertMatrixOperation = z.infer<typeof insertMatrixOperationSchema>;
export type MatrixOperation = typeof matrixOperations.$inferSelect;

// Network Events table for storing event logs
export const networkEvents = pgTable("network_events", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  timestamp: timestamp("timestamp").defaultNow().notNull(),
  type: varchar("type", { length: 50 }).notNull(),
  description: text("description").notNull(),
  details: jsonb("details"),
  packetId: varchar("packet_id", { length: 100 }),
});

export const insertNetworkEventSchema = createInsertSchema(networkEvents).omit({
  id: true,
  timestamp: true,
});

export type InsertNetworkEvent = z.infer<typeof insertNetworkEventSchema>;
export type NetworkEvent = typeof networkEvents.$inferSelect;

// Zod schemas for runtime validation (not stored in database)
export const matrixSchema = z.object({
  rows: z.number().int().min(1).max(700),
  cols: z.number().int().min(1).max(700),
  data: z.array(z.array(z.number())),
});

export const matrixOperationInputSchema = z.object({
  operation: z.enum(['add', 'subtract', 'multiply', 'transpose', 'determinant', 'inverse']),
  matrixA: matrixSchema,
  matrixB: matrixSchema.optional(),
});

export type Matrix = z.infer<typeof matrixSchema>;
export type MatrixOperationInput = z.infer<typeof matrixOperationInputSchema>;

export interface MatrixOperationResult {
  result: Matrix | number | null;
  executionTime: number;
  error?: string;
}

// Network Node Schema (runtime only, not persisted)
export const nodeTypeSchema = z.enum(['client', 'server', 'moderator']);

export const networkNodeSchema = z.object({
  id: z.string(),
  type: nodeTypeSchema,
  label: z.string(),
  x: z.number().optional(),
  y: z.number().optional(),
});

export type NodeType = z.infer<typeof nodeTypeSchema>;
export type NetworkNode = z.infer<typeof networkNodeSchema>;

// Packet Schema (runtime only, not persisted)
export const packetTypeSchema = z.enum(['REQ', 'ACK', 'NACK', 'DATA']);

export const packetSchema = z.object({
  id: z.string(),
  type: packetTypeSchema,
  sequenceNumber: z.number().int(),
  senderId: z.string(),
  receiverId: z.string(),
  payload: z.string(),
  checksum: z.string(),
  timestamp: z.number(),
  chunks: z.number().int().optional(),
  encrypted: z.boolean().default(false),
});

export type PacketType = z.infer<typeof packetTypeSchema>;
export type Packet = z.infer<typeof packetSchema>;

// Event Log Schema (maps to NetworkEvent)
export const eventTypeSchema = z.enum([
  'packet_sent',
  'packet_received',
  'packet_dropped',
  'retransmission',
  'timeout',
  'checksum_error',
  'ack_received',
  'nack_received'
]);

export const eventLogSchema = z.object({
  id: z.string(),
  timestamp: z.number(),
  type: eventTypeSchema,
  description: z.string(),
  details: z.record(z.any()).optional(),
  packetId: z.string().optional(),
});

export type EventType = z.infer<typeof eventTypeSchema>;
export type EventLog = z.infer<typeof eventLogSchema>;

// Statistics Schema (runtime only)
export interface NetworkStatistics {
  packetsSent: number;
  packetsReceived: number;
  packetsDropped: number;
  retransmissions: number;
  timeouts: number;
  checksumErrors: number;
  successRate: number;
}

// Simulation Config Schema (runtime only)
export const simulationConfigSchema = z.object({
  speed: z.number().min(0.1).max(10).default(1),
  packetLossRate: z.number().min(0).max(1).default(0),
  autoScroll: z.boolean().default(true),
});

export type SimulationConfig = z.infer<typeof simulationConfigSchema>;

// Performance Metrics Schema
export interface PerformanceMetric {
  id: string;
  operation: string;
  matrixSize: string;
  rows: number;
  cols: number;
  executionTime: number;
  timestamp: number;
}

// WebSocket Message Types
export interface WSMessage {
  type: 'packet_sent' | 'packet_received' | 'packet_dropped' | 'statistics_update' | 'simulation_state' | 'event_log';
  payload: any;
}
