'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, MessageCircle, Database, Loader2, AlertCircle, BarChart3, PlusSquare } from 'lucide-react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { UIResourceRenderer } from './UIResourceRenderer';
import { ChatMessage } from '@/types/api';

interface AnalyticsChatbotProps {
  className?: string;
}

const sampleQueries = [
  "Show me the top 10 merchants by redemption volume",
  "What's the total redemption amount by category?",
  "Which users have the highest redemption activity?",
  "Show redemption trends over the last 30 days",
  "What's the average redemption amount per merchant?"
];

export const AnalyticsChatbot: React.FC<AnalyticsChatbotProps> = ({ className = '' }) => {
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [hasInteracted, setHasInteracted] = useState(false);
  const [notifications, setNotifications] = useState<Array<{id: number, message: string, type: string}>>([]);

  const {
    isConnected,
    isConnecting,
    isProcessing,
    messages,
    sendQuery,
    clearChat,
    lastError
  } = useWebSocket({
    url: 'ws://localhost:8000/ws',
    autoReconnect: true
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Set hasInteracted to true if there are actual user messages
    const hasUserMessages = messages.some(m => m.type === 'user' && m.content && m.content.trim());
    setHasInteracted(hasUserMessages);
  }, [messages]);

  const handleSendMessage = () => {
    if (inputMessage.trim() && isConnected) {
      sendQuery(inputMessage.trim());
      setInputMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSampleQuery = (query: string) => {
    if (isConnected) {
      sendQuery(query);
    }
  };

  const handleUIAction = (action: { 
    type: string; 
    payload?: { 
      data?: Record<string, unknown>; 
      filename?: string; 
      action?: string; 
      rowCount?: number; 
      toolName?: string; 
      message?: string; 
      level?: string; 
    }; 
    componentId?: string; 
    timestamp?: string; 
  }) => {
    console.log('UI Action received:', action);
    
    let notificationMessage = '';
    let notificationType = 'info';
    
    // Handle MCP-UI compliant message structure
    const { type, payload, componentId } = action;
    
    switch (type) {
      case 'form-submit':
        notificationMessage = `Form submitted: ${JSON.stringify(payload?.data || {})}`;
        notificationType = 'success';
        break;
      case 'dashboard-refresh':
        notificationMessage = `Dashboard refreshed: ${componentId || 'unknown'}`;
        notificationType = 'info';
        break;
      case 'chart-export':
        notificationMessage = `Chart exported: ${payload?.filename || 'unknown'}`;
        notificationType = 'success';
        break;
      case 'chart-refresh':
        notificationMessage = `Chart refresh requested: ${componentId || 'unknown'}`;
        notificationType = 'info';
        break;
      case 'chart-fullscreen':
        notificationMessage = `Chart ${payload?.action === 'enter_fullscreen' ? 'entered' : 'exited'} fullscreen`;
        notificationType = 'info';
        break;
      case 'table-export':
        notificationMessage = `Table exported: ${payload?.filename || 'unknown'} (${payload?.rowCount || 0} rows)`;
        notificationType = 'success';
        break;
      case 'table-sort':
        notificationMessage = `Table sorted: ${payload?.action || 'unknown'}`;
        notificationType = 'info';
        break;
      case 'table-refresh':
        notificationMessage = `Table refresh requested: ${componentId || 'unknown'}`;
        notificationType = 'info';
        break;
      case 'notify':
        notificationMessage = payload?.message || 'Notification';
        notificationType = payload?.level || 'info';
        break;
      case 'tool':
        notificationMessage = `Tool called: ${payload?.toolName || 'unknown'}`;
        notificationType = 'info';
        break;
      default:
        notificationMessage = `Action: ${type}`;
        notificationType = 'info';
    }
    
    if (notificationMessage) {
      const newNotification = {
        id: Date.now(),
        message: notificationMessage,
        type: notificationType
      };
      
      setNotifications(prev => [...prev, newNotification]);
      
      // Remove notification after 5 seconds
      setTimeout(() => {
        setNotifications(prev => prev.filter(n => n.id !== newNotification.id));
      }, 5000);
    }
  };

  const renderMessage = (message: ChatMessage) => {
    const isUser = message.type === 'user';
    const isError = message.type === 'error';
    const isStatus = message.type === 'status';

    if (isStatus && isProcessing) {
      return null; // Don't render status messages while processing, we'll show a global indicator
    }

    return (
      <div key={`${message.id}-${message.timestamp.getTime()}`} className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 w-full`}>
        <div className={`${
          isUser 
            ? 'max-w-xs lg:max-w-md bg-blue-600 text-white' 
            : isError 
            ? 'w-full max-w-full bg-red-50 text-red-900 border border-red-200'
            : isStatus
            ? 'w-full max-w-full bg-gray-50 text-gray-700'
            : 'w-full max-w-full bg-gray-50 text-gray-800'
        } px-4 py-3 rounded-lg`}>
          <div className="flex items-start gap-3">
            {!isUser && (
              <div className="flex-shrink-0 mt-1">
                {isError ? (
                  <AlertCircle className="w-4 h-4 text-red-500" />
                ) : isStatus ? (
                  <Loader2 className="w-4 h-4 text-gray-500 animate-spin" />
                ) : message.ui_resource ? (
                  <BarChart3 className="w-4 h-4 text-blue-500" />
                ) : (
                  <MessageCircle className="w-4 h-4 text-gray-500" />
                )}
              </div>
            )}
            <div className="flex-1 w-full">
              {/* Render basic text content */}
                <p className="whitespace-pre-wrap text-xl">{message.content}</p>
              
              {message.reasoning && (
                <details className="mt-3 text-lg opacity-80">
                  <summary className="cursor-pointer font-medium">Show reasoning</summary>
                  <p className="mt-2 italic bg-gray-100 p-3 rounded text-lg">{message.reasoning}</p>
                </details>
              )}
              
              {/* Render UI Resource if present - INSIDE the message bubble */}
              {message.ui_resource && (
                <div className="mt-3 w-full">
                  <UIResourceRenderer
                    resource={message.ui_resource}
                    onUIAction={handleUIAction}
                    className="w-full"
                  />
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Render data table if present (and no UI Resource) */}
        {message.data && !message.ui_resource && (
          <div className="mt-3 w-full max-w-none overflow-x-auto">
            <div className="bg-white border rounded-lg p-4 shadow-sm w-full">
              <h4 className="text-xl font-semibold mb-3 text-gray-700">Query Results</h4>
              {message.data.length > 0 ? (
                <table className="min-w-full text-lg">
                  <thead className="bg-gray-50">
                    <tr className="border-b">
                      {Object.keys(message.data[0]).map((key) => (
                        <th key={key} className="text-left p-3 font-semibold text-gray-600">
                          {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {message.data.slice(0, 10).map((row, index) => (
                      <tr key={index} className="border-b last:border-b-0 hover:bg-gray-50">
                        {Object.values(row).map((value, cellIndex) => (
                          <td key={cellIndex} className="p-3 text-gray-800">
                            {String(value)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-xl text-gray-500">No data returned</p>
              )}
              {message.data.length > 10 && (
                <p className="text-lg text-gray-500 mt-3">
                  Showing first 10 of {message.data.length} results
                </p>
              )}
            </div>
          </div>
        )}
        
              <div className={`text-sm text-gray-400 mt-2 px-3 ${isUser ? 'text-right' : 'text-left'} w-full`}>
                {message.timestamp.toLocaleTimeString()}
              </div>
      </div>
    );
  };

  const WelcomeScreen = () => (
    <div className="text-center text-gray-500 my-auto px-4">
      <Database className="w-16 h-16 mx-auto mb-4 opacity-40" />
      <p className="text-4xl font-semibold text-gray-700">Welcome to AI Analytics!</p>
      <p className="text-2xl mt-3 mb-10">Ask me anything about your data using natural language.</p>
      
      {/* Sample Queries - Always visible in welcome screen */}
      <div className="bg-white rounded-lg p-6 shadow-sm border max-w-2xl mx-auto">
        <h3 className="text-2xl font-semibold text-gray-800 mb-6">💡 Try these sample queries:</h3>
        <div className="grid grid-cols-1 gap-4">
          {sampleQueries.map((query, index) => (
            <button
              key={index}
              onClick={() => handleSampleQuery(query)}
              disabled={!isConnected || isProcessing}
              className="text-lg bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 text-blue-800 px-6 py-4 rounded-lg font-medium transition-all duration-200 ease-in-out transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed border border-blue-200 hover:border-blue-300 text-left"
            >
              {query}
            </button>
          ))}
        </div>
        <p className="text-lg text-gray-500 mt-4">Click any query above to get started, or type your own question below.</p>
      </div>
    </div>
  );

  return (
    <div className={`flex flex-col h-full bg-white rounded-lg shadow border ${className}`}>
      {/* Simple Header */}
      <div className="flex items-center justify-between p-4 border-b bg-white rounded-t-lg">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
            <Database className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-semibold text-gray-900">AI Analytics Assistant</h2>
            <div className="flex items-center gap-2 text-lg">
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-gray-500">{isConnected ? 'Connected' : isConnecting ? 'Connecting...' : 'Disconnected'}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Removed New Chat button */}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="p-3 bg-gray-50 border-b">
        <div className="flex items-center gap-2 overflow-x-auto">
          <span className="text-lg font-medium text-gray-600 whitespace-nowrap">Quick:</span>
          {sampleQueries.slice(0, 3).map((query, index) => (
            <button
              key={index}
              onClick={() => handleSampleQuery(query)}
              disabled={!isConnected || isProcessing}
              className="text-sm bg-white hover:bg-blue-50 text-blue-700 px-3 py-2 rounded-full font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed border border-gray-200 hover:border-blue-300 whitespace-nowrap"
            >
              {query.length > 30 ? query.substring(0, 30) + '...' : query}
            </button>
          ))}
        </div>
      </div>

      {/* Error Banner */}
      {lastError && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-700 font-medium">{lastError}</p>
            </div>
          </div>
        </div>
      )}

      {/* Notifications */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {notifications.map((notification) => (
          <div
            key={notification.id}
            className={`px-4 py-3 rounded-lg shadow-lg max-w-sm transform transition-all duration-300 ${
              notification.type === 'success' 
                ? 'bg-green-500 text-white' 
                : notification.type === 'error'
                ? 'bg-red-500 text-white'
                : 'bg-blue-500 text-white'
            }`}
          >
            <p className="text-sm font-medium">{notification.message}</p>
          </div>
        ))}
      </div>

      {/* Messages Container */}
      <div 
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-2 min-h-0"
      >
        {messages.length === 0 || (!hasInteracted && messages.every(m => m.type === 'status' || m.type === 'error')) ? (
          <WelcomeScreen />
        ) : (
          messages.map(renderMessage)
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t bg-white rounded-b-lg">
        <div className="flex gap-3 items-end">
          <div className="flex-1 relative">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me about your data..."
              className="w-full px-6 py-4 pr-16 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow text-xl"
              rows={1}
              disabled={!isConnected || isProcessing}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || !isConnected || isProcessing}
              className="absolute right-4 top-1/2 -translate-y-1/2 p-3 text-blue-500 hover:bg-blue-100 rounded-lg transition-colors disabled:text-gray-400 disabled:cursor-not-allowed"
            >
              {isProcessing ? <Loader2 className="w-6 h-6 animate-spin" /> : <Send className="w-6 h-6" />}
            </button>
          </div>
        </div>
        <div className="flex justify-between items-center mt-3 text-lg text-gray-500">
          <span><strong>Enter</strong> to send, <strong>Shift+Enter</strong> for new line</span>
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="font-medium text-blue-600 hover:text-blue-800 transition-colors text-xl"
            >
              Clear chat
            </button>
          )}
        </div>
      </div>
    </div>
  );
};