'use client'

import { Message } from '@/types/api'
import { User, Bot, AlertCircle, CheckCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface MessageBubbleProps {
  message: Message
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.type === 'user'
  const isError = message.type === 'error'
  const isSystem = message.type === 'system'
  
  const getIcon = () => {
    if (isUser) return <User className="w-4 h-4" />
    if (isError) return <AlertCircle className="w-4 h-4" />
    if (isSystem) return <CheckCircle className="w-4 h-4" />
    return <Bot className="w-4 h-4" />
  }
  
  const getBubbleClasses = () => {
    if (isUser) {
      return 'bg-primary-600 text-white ml-12'
    }
    if (isError) {
      return 'bg-red-100 text-red-800 border border-red-200 mr-12'
    }
    if (isSystem) {
      return 'bg-green-100 text-green-800 border border-green-200 mr-12'
    }
    return 'bg-gray-100 text-gray-800 mr-12'
  }
  
  const getIconClasses = () => {
    if (isUser) {
      return 'bg-primary-700 text-white'
    }
    if (isError) {
      return 'bg-red-200 text-red-600'
    }
    if (isSystem) {
      return 'bg-green-200 text-green-600'
    }
    return 'bg-gray-200 text-gray-600'
  }
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      {!isUser && (
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${getIconClasses()}`}>
          {getIcon()}
        </div>
      )}
      
      <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${getBubbleClasses()}`}>
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        <p className="text-xs opacity-70 mt-1">
          {formatDistanceToNow(new Date(message.timestamp), { addSuffix: true })}
        </p>
      </div>
      
      {isUser && (
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${getIconClasses()}`}>
          {getIcon()}
        </div>
      )}
    </div>
  )
}
