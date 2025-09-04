'use client'

import { useState, useEffect } from 'react'
import { CheckCircle, AlertCircle, Loader2, WifiOff } from 'lucide-react'

interface StatusIndicatorProps {
  className?: string
}

interface SystemStatus {
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

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({ className = '' }) => {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/status')
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        const data = await response.json()
        setStatus(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch status')
        setStatus(null)
      } finally {
        setIsLoading(false)
      }
    }
    
    fetchStatus()
    
    // Refresh status every 30 seconds
    const interval = setInterval(fetchStatus, 30000)
    
    return () => clearInterval(interval)
  }, [])
  
  if (isLoading) {
    return (
      <div className={`flex items-center space-x-2 text-sm text-gray-500 ${className}`}>
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>Checking status...</span>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className={`flex items-center space-x-2 text-sm text-red-500 ${className}`}>
        <AlertCircle className="w-4 h-4" />
        <span>Status unavailable</span>
      </div>
    )
  }
  
  if (!status) {
    return (
      <div className={`flex items-center space-x-2 text-sm text-gray-500 ${className}`}>
        <WifiOff className="w-4 h-4" />
        <span>No status data</span>
      </div>
    )
  }
  
  const getStatusIcon = () => {
    switch (status.status) {
      case 'healthy':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'degraded':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />
      case 'unhealthy':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return <WifiOff className="w-4 h-4 text-gray-400" />
    }
  }
  
  const getStatusText = () => {
    switch (status.status) {
      case 'healthy':
        return 'All systems operational'
      case 'degraded':
        return 'Some services degraded'
      case 'unhealthy':
        return 'System issues detected'
      default:
        return 'Status unknown'
    }
  }
  
  const getStatusColor = () => {
    switch (status.status) {
      case 'healthy':
        return 'text-green-600'
      case 'degraded':
        return 'text-yellow-600'
      case 'unhealthy':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }
  
  return (
    <div className={`flex items-center space-x-2 text-sm ${getStatusColor()} ${className}`}>
      {getStatusIcon()}
      <span>{getStatusText()}</span>
      
      {/* MCP Server Status */}
      <div className="flex items-center space-x-1 ml-2">
        <span className="text-xs text-gray-500">MCP:</span>
        <div className="flex space-x-1">
          <div className={`w-2 h-2 rounded-full ${status.mcpServers.database.connected ? 'bg-green-500' : 'bg-red-500'}`} title="Database MCP" />
          <div className={`w-2 h-2 rounded-full ${status.mcpServers.vizro.connected ? 'bg-green-500' : 'bg-red-500'}`} title="Vizro MCP" />
        </div>
      </div>
      
      {/* WebSocket Connections */}
      <div className="flex items-center space-x-1 ml-2">
        <span className="text-xs text-gray-500">WS:</span>
        <span className="text-xs font-medium">{status.websocketConnections}</span>
      </div>
    </div>
  )
}
