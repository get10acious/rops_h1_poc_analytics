// API types for RewardOps Analytics POC

export interface WebSocketMessage {
  type: 'QUERY' | 'RESPONSE' | 'ERROR' | 'STATUS_UPDATE' | 'PING' | 'PONG'
  payload: Record<string, any>
  timestamp: string
  message_id: string
}

export interface QueryMessage extends WebSocketMessage {
  type: 'QUERY'
  payload: {
    query: string
    userId: string
  }
}

export interface ResponseMessage extends WebSocketMessage {
  type: 'RESPONSE'
  payload: {
    result: any[]
    visualization?: VizroConfig
    query: string
    queryId: string
    processingTime: number
  }
}

export interface ErrorMessage extends WebSocketMessage {
  type: 'ERROR'
  payload: {
    error: string
    query?: string
    userId?: string
  }
}

export interface StatusUpdateMessage extends WebSocketMessage {
  type: 'STATUS_UPDATE'
  payload: {
    status: string
    message?: string
    timestamp?: string
  }
}

export interface VizroConfig {
  title: string
  chart_type: 'bar' | 'line' | 'pie' | 'scatter' | 'area' | 'heatmap'
  data: Record<string, any>[]
  x_column?: string
  y_column?: string
  width?: number
  height?: number
  theme?: 'default' | 'dark' | 'light'
}

export interface UIResource {
  uri: string
  mimeType: string
  text: string
  encoding: string
}

export interface Message {
  id: string
  content: string
  type: 'user' | 'assistant' | 'error' | 'system'
  timestamp: string
  visualization?: VizroConfig
  uiResource?: UIResource
}

export interface WebSocketStatus {
  status: 'connecting' | 'connected' | 'disconnected' | 'error'
  lastConnected?: string
  reconnectAttempts: number
}

export interface ConnectionInfo {
  clientId: string
  connectedAt: string
  lastActivity: string
  userId?: string
  status: WebSocketStatus['status']
}

export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  mcpServers: {
    database: {
      connected: boolean
      tools: string[]
    }
    vizro: {
      connected: boolean
      tools: string[]
    }
  }
  websocketConnections: number
  timestamp: string
}

// Business domain types
export interface Merchant {
  id: number
  name: string
  category?: string
  description?: string
  website_url?: string
  logo_url?: string
  created_at: string
  updated_at: string
  is_active: boolean
}

export interface User {
  id: number
  email: string
  first_name?: string
  last_name?: string
  phone?: string
  date_of_birth?: string
  created_at: string
  updated_at: string
  is_active: boolean
  total_points: number
  tier: 'bronze' | 'silver' | 'gold' | 'platinum'
}

export interface Redemption {
  id: number
  user_id: number
  merchant_id: number
  amount: number
  points_used: number
  redemption_date: string
  status: 'completed' | 'pending' | 'cancelled'
  transaction_id?: string
  notes?: string
  created_at: string
}

export interface Campaign {
  id: number
  name: string
  description?: string
  start_date?: string
  end_date?: string
  is_active: boolean
  created_at: string
}

// Analytics types
export interface AnalyticsQuery {
  query: string
  userId: string
  context?: Record<string, any>
}

export interface AnalyticsResult {
  status: 'success' | 'error'
  data: Record<string, any>[]
  visualization?: VizroConfig
  query: string
  queryId: string
  processingTime: number
  timestamp: string
  error?: string
}

// Chart types
export interface ChartData {
  name: string
  value: number
  [key: string]: any
}

export interface ChartConfig {
  title: string
  type: 'bar' | 'line' | 'pie' | 'scatter' | 'area'
  data: ChartData[]
  xAxisKey: string
  yAxisKey: string
  width?: number
  height?: number
}

// Error types
export interface ApiError {
  error: string
  detail?: string
  timestamp: string
  requestId?: string
}

export interface ValidationError {
  field: string
  message: string
  value: any
}

// Rate limiting types
export interface RateLimitInfo {
  userId: string
  requestsMade: number
  requestsAllowed: number
  windowStart: string
  windowEnd: string
  resetTime: string
}

export interface RateLimitResponse {
  allowed: boolean
  remaining: number
  resetTime: string
  retryAfter?: number
}

// MCP types
export interface MCPTool {
  name: string
  description: string
  inputSchema: Record<string, any>
  outputSchema: Record<string, any>
}

export interface MCPToolCall {
  toolName: string
  arguments: Record<string, any>
  callId?: string
}

export interface MCPToolResult {
  toolName: string
  result: Record<string, any>
  callId?: string
  success: boolean
  error?: string
}

// Agent types
export interface AgentState {
  query: string
  reasoning?: string
  action?: string
  observation?: string
  result?: Record<string, any>
  error?: string
  stepCount: number
  maxSteps: number
}

export interface AgentStep {
  stepType: 'reason' | 'act' | 'observe'
  content: string
  timestamp: string
  stepNumber: number
}

export interface AgentExecution {
  query: string
  userId: string
  steps: AgentStep[]
  finalResult?: Record<string, any>
  success: boolean
  executionTime: number
  timestamp: string
}

// Database types
export interface SQLQuery {
  query: string
  parameters?: Record<string, any>
  timeout: number
}

export interface QueryResult {
  data: Record<string, any>[]
  rowCount: number
  executionTime: number
  columns: string[]
}

// Connection types
export interface ConnectionStats {
  totalConnections: number
  activeConnections: number
  totalMessages: number
  averageResponseTime: number
}

// Health check types
export interface HealthCheckResponse {
  status: string
  timestamp: string
  version: string
  mcpServers?: Record<string, any>
}

export interface StatusResponse {
  status: string
  mcpServers: Record<string, any>
  websocketConnections: number
  timestamp: string
}

// Test types
export interface TestQueryRequest {
  query: string
  userId: string
}

export interface TestQueryResponse {
  status: string
  result: Record<string, any>
  timestamp: string
}
