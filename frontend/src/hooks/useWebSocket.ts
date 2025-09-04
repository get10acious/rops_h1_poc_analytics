import { useState, useEffect, useCallback, useRef } from 'react'
import { WebSocketMessage, WebSocketStatus } from '@/types/api'

interface UseWebSocketOptions {
  url: string
  onMessage?: (message: WebSocketMessage) => void
  onError?: (error: Event) => void
  onOpen?: () => void
  onClose?: () => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
  shouldReconnect?: boolean
}

export const useWebSocket = ({
  url,
  onMessage,
  onError,
  onOpen,
  onClose,
  reconnectInterval = 5000,
  maxReconnectAttempts = 5,
  shouldReconnect = true
}: UseWebSocketOptions) => {
  const [connectionStatus, setConnectionStatus] = useState<WebSocketStatus['status']>('connecting')
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [lastConnected, setLastConnected] = useState<string | undefined>(undefined)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const isManualCloseRef = useRef(false)
  
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }
    
    try {
      setConnectionStatus('connecting')
      const ws = new WebSocket(url)
      wsRef.current = ws
      
      ws.onopen = () => {
        setConnectionStatus('connected')
        setLastConnected(new Date().toISOString())
        setReconnectAttempts(0)
        isManualCloseRef.current = false
        onOpen?.()
      }
      
      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          setLastMessage(message)
          onMessage?.(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
      
      ws.onerror = (error) => {
        setConnectionStatus('error')
        onError?.(error)
      }
      
      ws.onclose = () => {
        setConnectionStatus('disconnected')
        onClose?.()
        
        // Attempt reconnection if not manually closed
        if (!isManualCloseRef.current && shouldReconnect && reconnectAttempts < maxReconnectAttempts) {
          setReconnectAttempts(prev => prev + 1)
          reconnectTimeoutRef.current = setTimeout(() => {
            setConnectionStatus('connecting')
            connect()
          }, reconnectInterval)
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      setConnectionStatus('error')
    }
  }, [url, onMessage, onError, onOpen, onClose, reconnectInterval, maxReconnectAttempts, shouldReconnect, reconnectAttempts])
  
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      throw new Error('WebSocket is not connected')
    }
  }, [])
  
  const disconnect = useCallback(() => {
    isManualCloseRef.current = true
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    wsRef.current?.close()
  }, [])
  
  const reconnect = useCallback(() => {
    disconnect()
    setReconnectAttempts(0)
    setTimeout(connect, 1000)
  }, [disconnect, connect])
  
  useEffect(() => {
    connect()
    
    return () => {
      disconnect()
    }
  }, [connect, disconnect])
  
  return {
    connectionStatus,
    lastMessage,
    lastConnected,
    reconnectAttempts,
    sendMessage,
    disconnect,
    reconnect
  }
}
