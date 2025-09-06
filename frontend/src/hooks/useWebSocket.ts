import { useState, useEffect, useRef, useCallback } from 'react';
import { WebSocketMessage, MessageType, ChatMessage, AgentResponse, StatusUpdate, ErrorMessage } from '@/types/api';

interface UseWebSocketOptions {
  url: string;
  onMessage?: (message: WebSocketMessage) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  isProcessing: boolean;
  messages: ChatMessage[];
  sendMessage: (message: WebSocketMessage) => void;
  sendQuery: (query: string) => void;
  clearChat: () => void;
  lastError: string | null;
}

export const useWebSocket = (options: UseWebSocketOptions): UseWebSocketReturn => {
  const {
    url,
    onMessage,
    onOpen,
    onClose,
    onError,
    autoReconnect = true,
    reconnectInterval = 3000
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [lastError, setLastError] = useState<string | null>(null);

  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const messageIdCounter = useRef(0);
  const hasConnectedBefore = useRef(false);

  const generateMessageId = useCallback(() => {
    return `msg_${Date.now()}_${++messageIdCounter.current}`;
  }, []);

  const addChatMessage = useCallback((message: Partial<ChatMessage>) => {
    const chatMessage: ChatMessage = {
      id: generateMessageId(),
      type: message.type || 'agent',
      content: message.content || '',
      timestamp: new Date(),
      ...message
    };
    
    setMessages(prev => [...prev, chatMessage]);
  }, [generateMessageId]);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setIsConnecting(true);
    setLastError(null);

    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        setIsConnected(true);
        setIsConnecting(false);
        setLastError(null);
        if (hasConnectedBefore.current) {
          addChatMessage({
            type: 'status',
            content: 'Reconnected to the server.',
          });
        }
        hasConnectedBefore.current = true;
        onOpen?.();
      };

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          // Clear any previous errors on successful message parsing
          setLastError(null);

          // Clear status messages on new agent response or error
          if (message.type === MessageType.AGENT_RESPONSE || message.type === MessageType.ERROR) {
            setMessages(prev => prev.filter(m => m.type !== 'status'));
          }
          
          // Always clear processing state on any response
          setIsProcessing(false);
          
          // Handle different message types
          switch (message.type) {
            case MessageType.AGENT_RESPONSE:
              const response = (message.content || message.payload) as AgentResponse;
              addChatMessage({
                type: 'agent',
                content: response.response,
                data: response.data,
                ui_resource: response.ui_resource,
                reasoning: response.reasoning
              });
              break;
              
            case MessageType.STATUS_UPDATE:
              // Handle status updates - only show temporary status messages
              const statusContent = (message.content || message.payload) as StatusUpdate;
              const statusText = statusContent.details || statusContent.status;
              
              // Don't show welcome messages or session messages as persistent status
              if (statusText.includes('Welcome to RewardOps') || statusText.includes('New session started')) {
                // These are informational, not persistent status
                break;
              }
              
              // For other status messages, replace existing status
              setMessages(prev => {
                const newMessages = prev.filter(m => m.type !== 'status');
                return [...newMessages, {
                  id: generateMessageId(),
                  type: 'status',
                  content: statusText,
                  timestamp: new Date()
                }];
              });
              break;
              
            case MessageType.ERROR:
              const errorContent = (message.content || message.payload) as ErrorMessage;
              addChatMessage({
                type: 'error',
                content: errorContent.error || 'An error occurred'
              });
              setLastError(errorContent.error);
              break;
              
            default:
              console.log('Received message:', message);
          }

          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
          console.error('Raw message data:', event.data);
          setLastError(`Failed to parse server response: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      };

      ws.current.onclose = () => {
        setIsConnected(false);
        setIsConnecting(false);
        onClose?.();

        if (autoReconnect && reconnectTimeoutRef.current === null) {
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectTimeoutRef.current = null;
            connect();
          }, reconnectInterval);
        }
      };

      ws.current.onerror = (error) => {
        setIsConnecting(false);
        setLastError('WebSocket connection error');
        onError?.(error);
      };

    } catch (error) {
      setIsConnecting(false);
      setLastError('Failed to create WebSocket connection');
      console.error('WebSocket connection error:', error);
    }
  }, [url, onMessage, onOpen, onClose, onError, autoReconnect, reconnectInterval, addChatMessage, generateMessageId]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
  }, []);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      try {
        ws.current.send(JSON.stringify(message));
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
        setLastError('Failed to send message');
      }
    } else {
      setLastError('WebSocket is not connected');
    }
  }, []);

  const sendQuery = useCallback((query: string) => {
    // Add user message to chat
    addChatMessage({
      type: 'user',
      content: query
    });

    // Send query to backend
    const message: WebSocketMessage = {
      type: MessageType.USER_QUERY,
      content: {
        query,
        session_id: 'session_' + Date.now()
      }
    };

    sendMessage(message);
    setIsProcessing(true);
  }, [addChatMessage, sendMessage]);

  const clearChat = useCallback(() => {
    setMessages([]);
    sendMessage({
      type: MessageType.CLEAR_CHAT,
      content: {}
    });
  }, [sendMessage]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return {
    isConnected,
    isConnecting,
    isProcessing,
    messages,
    sendMessage,
    sendQuery,
    clearChat,
    lastError
  };
};