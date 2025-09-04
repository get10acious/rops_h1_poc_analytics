'use client'

import { useState } from 'react'
import { AnalyticsChatbot } from '@/components/AnalyticsChatbot'
import { Header } from '@/components/Header'
import { Sidebar } from '@/components/Sidebar'
import { StatusIndicator } from '@/components/StatusIndicator'

export default function HomePage() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
      
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      
      {/* Main Content */}
      <main className="lg:pl-64">
        <div className="px-4 py-6 sm:px-6 lg:px-8">
          {/* Status Indicator */}
          <div className="mb-6">
            <StatusIndicator />
          </div>
          
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">
              RewardOps Analytics
            </h1>
            <p className="mt-2 text-gray-600">
              Ask questions about your data in natural language and get instant insights
            </p>
          </div>
          
          {/* Analytics Chatbot */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Analytics Assistant</h2>
              <p className="card-description">
                Try asking questions like:
                <br />
                • "Show me the top 10 merchants by redemption volume"
                <br />
                • "What are the most popular redemption categories?"
                <br />
                • "How many users redeemed rewards this month?"
              </p>
            </div>
            <div className="card-content">
              <AnalyticsChatbot />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
