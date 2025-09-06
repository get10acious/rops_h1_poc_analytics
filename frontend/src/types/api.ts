export enum MessageType {
  QUERY = "QUERY",
  USER_QUERY = "user_query", // Legacy support
  RESPONSE = "RESPONSE", 
  AGENT_RESPONSE = "agent_response",
  STATUS_UPDATE = "STATUS_UPDATE",
  ERROR = "ERROR",
  VISUALIZATION = "visualization",
  CLEAR_CHAT = "clear_chat",
  PING = "PING",
  PONG = "PONG"
}

export interface WebSocketMessage {
  type: MessageType;
  payload: AgentResponse | StatusUpdate | ErrorMessage | Record<string, unknown>;
  timestamp: string;
  message_id: string;
}

export interface UserQuery {
  query: string;
  session_id?: string;
}

export interface UIResource {
  uri: string;
  mimeType: string;
  text: string;
  encoding?: string;
}

export interface AgentResponse {
  type: "text" | "data" | "visualization" | "ui_resource" | "error";
  response: string;
  reasoning?: string;
  data?: Record<string, unknown>[];
  ui_resource?: UIResource;
  sql_query?: string;
}

export interface StatusUpdate {
  status: string;
  details?: string;
}

export interface ErrorMessage {
  error: string;
  code?: string;
  details?: string;
}

export interface ChatMessage {
  id: string;
  type: "user" | "agent" | "status" | "error";
  content: string;
  timestamp: Date;
  data?: Record<string, unknown>[];
  ui_resource?: UIResource;
  reasoning?: string;
}