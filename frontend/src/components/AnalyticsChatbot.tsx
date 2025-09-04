'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { Send, Loader2, AlertCircle, CheckCircle, Wifi, WifiOff } from 'lucide-react'
import { useWebSocket } from '@/hooks/useWebSocket'
import { Message, WebSocketMessage, VizroConfig } from '@/types/api'
import { VizroChart } from './VizroChart'
import { MessageBubble } from './MessageBubble'
import { StatusIndicator } from './StatusIndicator'

interface AnalyticsChatbotProps {
  userId?: string
  className?: string
}

export const AnalyticsChatbot: React.FC<AnalyticsChatbotProps> = ({
  userId = 'anonymous',
  className = ''
}) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])
  
  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])
  
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'RESPONSE':
        setIsLoading(false)
        const responseMessage: Message = {
          id: message.message_id,
          content: `Query processed in ${message.payload.processingTime?.toFixed(2)}s`,
          type: 'assistant',
          timestamp: message.timestamp,
          visualization: message.payload.visualization
        }
        setMessages(prev => [...prev, responseMessage])
        break
        
      case 'ERROR':
        setIsLoading(false)
        const errorMessage: Message = {
          id: message.message_id,
          content: `Error: ${message.payload.error}`,
          type: 'error',
          timestamp: message.timestamp
        }
        setMessages(prev => [...prev, errorMessage])
        break
        
      case 'STATUS_UPDATE':
        if (message.payload.status === 'processing') {
          setIsLoading(true)
        }
        break
        
      default:
        break
    }
  }, [])
  
  const { connectionStatus, sendMessage } = useWebSocket({
    url: 'ws://localhost:8000/ws',
    onMessage: handleWebSocketMessage,
    onError: (error) => {
      console.error('WebSocket error:', error)
      setIsLoading(false)
    },
    onOpen: () => {
      console.log('WebSocket connected')
    },
    onClose: () => {
      console.log('WebSocket disconnected')
      setIsLoading(false)
    }
  })
  
  const handleSendMessage = useCallback(async () => {
    if (!inputValue.trim() || isLoading || connectionStatus !== 'connected') {
      return
    }
    
    const query = inputValue.trim()
    setInputValue('')
    
    // Add user message
    const userMessage: Message = {
      id: `user_${Date.now()}`,
      content: query,
      type: 'user',
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])
    
    // Send query to backend
    try {
      sendMessage({
        type: 'QUERY',
        payload: {
          query,
          userId
        },
        timestamp: new Date().toISOString(),
        message_id: `query_${Date.now()}`
      })
    } catch (error) {
      console.error('Failed to send message:', error)
      const errorMessage: Message = {
        id: `error_${Date.now()}`,
        content: 'Failed to send message. Please try again.',
        type: 'error',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }, [inputValue, isLoading, connectionStatus, sendMessage, userId])
  
  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }, [handleSendMessage])
  
  const canSendMessage = inputValue.trim().length > 0 && 
                        connectionStatus === 'connected' && 
                        !isLoading
  
  return (
    <div className={`flex flex-col h-[600px] ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <h3 className="text-lg font-semibold text-gray-900">Analytics Assistant</h3>
          <StatusIndicator />
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          {connectionStatus === 'connected' && <CheckCircle className="w-4 h-4 text-green-500" />}
          {connectionStatus === 'connecting' && <Loader2 className="w-4 h-4 text-yellow-500 animate-spin" />}
          {connectionStatus === 'error' && <AlertCircle className="w-4 h-4 text-red-500" />}
          {connectionStatus === 'disconnected' && <WifiOff className="w-4 h-4 text-gray-400" />}
          <span className="capitalize">{connectionStatus}</span>
        </div>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 chat-scrollbar">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p className="text-lg font-medium mb-2">Welcome to RewardOps Analytics!</p>
            <p className="text-sm">
              Ask questions about your data in natural language. Try:
            </p>
            <div className="mt-4 space-y-2 text-sm">
              <p>• "Show me the top 10 merchants by redemption volume"</p>
              <p>• "What are the most popular redemption categories?"</p>
              <p>• "How many users redeemed rewards this month?"</p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id}>
              <MessageBubble message={message} />
              {message.visualization && (
                <div className="mt-4 ml-12">
                  <VizroChart config={message.visualization} />
                </div>
              )}
            </div>
          ))
        )}
        
        {isLoading && (
          <div className="flex items-center space-x-2 text-gray-500">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Processing your query...</span>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about your data..."
            className="flex-1 input"
            disabled={connectionStatus !== 'connected' || isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!canSendMessage}
            className="btn btn-primary btn-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
        
        {connectionStatus !== 'connected' && (
          <p className="text-sm text-red-500 mt-2">
            {connectionStatus === 'connecting' && 'Connecting to analytics service...'}
            {connectionStatus === 'error' && 'Connection error. Please refresh the page.'}
            {connectionStatus === 'disconnected' && 'Disconnected. Attempting to reconnect...'}
          </p>
        )}
      </div>
    </div>
  )
}
