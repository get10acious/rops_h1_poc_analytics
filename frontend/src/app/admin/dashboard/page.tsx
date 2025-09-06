'use client';

import React, { useState } from 'react';
import { AnalyticsChatbot } from '@/components/AnalyticsChatbot';
import { BarChart3, TrendingUp, Clock, X, ChevronLeft, ChevronRight, MessageSquare } from 'lucide-react';

interface DashboardModal {
  isOpen: boolean;
  type: 'performance' | 'passage' | null;
}

interface ChatSession {
  id: string;
  title: string;
  timestamp: Date;
  lastMessage: string;
}

export default function AdminDashboard() {
  const [modal, setModal] = useState<DashboardModal>({ isOpen: false, type: null });
  const [isHistoryPanelOpen, setIsHistoryPanelOpen] = useState(false);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([
    {
      id: '1',
      title: 'Merchant Analysis',
      timestamp: new Date('2024-01-15T10:30:00'),
      lastMessage: 'Show me the top 10 merchants by sales volume'
    },
    {
      id: '2', 
      title: 'User Analytics',
      timestamp: new Date('2024-01-14T15:45:00'),
      lastMessage: 'What are the user engagement trends?'
    },
    {
      id: '3',
      title: 'Revenue Report',
      timestamp: new Date('2024-01-13T09:15:00'),
      lastMessage: 'Generate monthly revenue report'
    },
    {
      id: '4',
      title: 'Performance Metrics',
      timestamp: new Date('2024-01-12T14:20:00'),
      lastMessage: 'Show performance metrics dashboard'
    }
  ]);

  const openDashboard = (type: 'performance' | 'passage') => {
    setModal({ isOpen: true, type });
  };

  const closeDashboard = () => {
    setModal({ isOpen: false, type: null });
  };

  return (
    <div className="h-screen bg-gray-50 flex">
      {/* Left Sidebar - Fixed */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <h1 className="text-3xl font-semibold text-gray-900">LoyaltyAnalytics AI</h1>
          <p className="text-lg text-gray-500 mt-1">Analytics Dashboard</p>
        </div>

        {/* Dashboard Metrics */}
        <div className="flex-1 p-6 space-y-6">
          <div>
            <h2 className="text-lg font-medium text-gray-700 mb-4">Dashboard Metrics</h2>
            
            {/* Basic Metrics */}
            <div className="space-y-3 mb-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-1">Total Merchants</h3>
                <p className="text-4xl font-bold text-gray-900">10</p>
                <p className="text-sm text-gray-500">Active accounts</p>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-1">Total Users</h3>
                <p className="text-4xl font-bold text-gray-900">10</p>
                <p className="text-sm text-gray-500">Registered users</p>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-1">Redemptions</h3>
                <p className="text-4xl font-bold text-gray-900">200</p>
                <p className="text-sm text-gray-500">Last 30 days</p>
              </div>
            </div>

            {/* Performance Triggers - Clickable */}
            <div className="mb-6">
              <button 
                onClick={() => openDashboard('performance')}
                className="w-full bg-white rounded-lg p-4 border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all text-left group"
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-medium text-gray-700 flex items-center">
                    <BarChart3 className="w-6 h-6 mr-2 text-blue-500" />
                    PERFORMANCE TRIGGERS
                  </h3>
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                    <BarChart3 className="w-6 h-6 text-gray-400" />
                  </div>
                </div>
                <div className="text-5xl font-bold text-gray-900">55</div>
                <div className="text-sm text-gray-500 mt-1">Avg Clarity: 4.8/5</div>
                <div className="flex items-center mt-2">
                  <span className="text-sm text-green-600 font-medium bg-green-50 px-2 py-1 rounded">↗ 7%</span>
                </div>
              </button>
            </div>

            {/* Passage Time Analytics - Clickable */}
            <div className="mb-6">
              <button 
                onClick={() => openDashboard('passage')}
                className="w-full bg-white rounded-lg p-4 border border-gray-200 hover:border-green-300 hover:shadow-md transition-all text-left group"
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-medium text-gray-700 flex items-center">
                    <Clock className="w-6 h-6 mr-2 text-green-500" />
                    PASSAGE TIME ANALYTICS
                  </h3>
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                    <TrendingUp className="w-6 h-6 text-gray-400" />
                  </div>
                </div>
                <div className="text-5xl font-bold text-gray-900">84</div>
                <div className="text-sm text-gray-500 mt-1">Avg Turns: 4.5</div>
                <div className="flex items-center mt-2">
                  <span className="text-sm text-green-600 font-medium bg-green-50 px-2 py-1 rounded">↗ 225%</span>
                </div>
              </button>
            </div>
          </div>

          {/* Bottom section */}
          <div className="mt-auto pt-6 border-t border-gray-200">
            <button className="w-full text-lg text-gray-600 hover:text-gray-900 transition-colors py-2">
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* History Panel - Collapsible */}
      <div className={`${isHistoryPanelOpen ? 'w-80' : 'w-0'} transition-all duration-300 bg-white border-r border-gray-200 flex flex-col overflow-hidden`}>
        {isHistoryPanelOpen && (
          <>
            {/* History Header */}
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <MessageSquare className="w-6 h-6 text-blue-600" />
                <h2 className="text-2xl font-semibold text-gray-900">History</h2>
              </div>
              <button
                onClick={() => setIsHistoryPanelOpen(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ChevronLeft className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* New Chat Button */}
            <div className="p-4 border-b border-gray-200">
              <button className="w-full bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 transition-colors text-lg font-medium">
                New Chat
              </button>
            </div>

            {/* Chat Sessions */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {chatSessions.map((session) => (
                <div
                  key={session.id}
                  className="p-4 bg-gray-50 hover:bg-gray-100 rounded-lg cursor-pointer transition-colors border"
                >
                  <h3 className="text-lg font-medium text-gray-900 mb-2">{session.title}</h3>
                  <p className="text-sm text-gray-600 mb-2 line-clamp-2">{session.lastMessage}</p>
                  <p className="text-xs text-gray-400">{session.timestamp.toLocaleDateString()}</p>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Right Side - Chat Interface (Full Height) */}
      <div className="flex-1 flex flex-col h-screen relative">
        {/* Toggle History Button */}
        {!isHistoryPanelOpen && (
          <button
            onClick={() => setIsHistoryPanelOpen(true)}
            className="absolute top-6 left-6 z-10 p-2 bg-blue-600 text-white rounded-lg shadow-lg hover:bg-blue-700 transition-all"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        )}
        <AnalyticsChatbot className="h-full" />
      </div>

      {/* Dashboard Modal Overlay */}
      {modal.isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-6xl h-full max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-3xl font-semibold text-gray-900">
                {modal.type === 'performance' ? 'Performance Analytics Dashboard' : 'Passage Time Analytics Dashboard'}
              </h2>
              <div className="flex items-center gap-4">
                <button className="text-lg text-blue-600 hover:text-blue-800 flex items-center gap-2">
                  <TrendingUp className="w-6 h-6" />
                  Refresh
                </button>
                <button className="text-lg text-blue-600 hover:text-blue-800 flex items-center gap-2">
                  <BarChart3 className="w-6 h-6" />
                  Export CSV
                </button>
                <button 
                  onClick={closeDashboard}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="flex-1 p-6 overflow-y-auto">
              {modal.type === 'performance' ? (
                <div className="space-y-6">
                  <div className="text-sm text-gray-600 mb-6">
                    Real-time insights and performance metrics
                  </div>

                  {/* Filters */}
                  <div className="flex items-center gap-4 mb-6">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-700">Filters:</span>
                      <select className="text-sm border border-gray-300 rounded px-3 py-1">
                        <option>All Users</option>
                        <option>Active Users</option>
                        <option>Power Users</option>
                      </select>
                    </div>
                    <div className="flex items-center gap-2">
                      <input type="checkbox" className="w-4 h-4" />
                      <span className="text-sm text-gray-600">Custom Range</span>
                      <select className="text-sm border border-gray-300 rounded px-3 py-1">
                        <option>Last 3 Weeks</option>
                        <option>Last Month</option>
                        <option>Last 3 Months</option>
                      </select>
                    </div>
                  </div>

                  {/* Dashboard Content Grid */}
                  <div className="grid grid-cols-2 gap-6">
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <h3 className="text-2xl font-semibold text-gray-900 mb-4">Performance Categories</h3>
                      <div className="h-64 bg-gray-50 rounded flex items-center justify-center">
                        <span className="text-xl text-gray-500">Pie Chart Placeholder</span>
                      </div>
                    </div>
                    
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <h3 className="text-2xl font-semibold text-gray-900 mb-4">Prompt Clarity Score Trends</h3>
                      <div className="h-64 bg-gray-50 rounded flex items-center justify-center">
                        <span className="text-xl text-gray-500">Line Chart Placeholder</span>
                      </div>
                    </div>
                    
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Task Intent Patterns</h3>
                      <div className="h-64 bg-gray-50 rounded flex items-center justify-center">
                        <span className="text-gray-500">Bar Chart Placeholder</span>
                      </div>
                    </div>
                    
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <h3 className="text-2xl font-semibold text-gray-900 mb-4">Performance Ratings</h3>
                      <div className="h-64 bg-gray-50 rounded flex items-center justify-center">
                        <span className="text-xl text-gray-500">Horizontal Bar Chart Placeholder</span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="text-lg text-gray-600 mb-6">
                    Real-time insights and performance metrics
                  </div>

                  {/* Filters */}
                  <div className="flex items-center gap-4 mb-6">
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-medium text-gray-700">Filters:</span>
                      <select className="text-lg border border-gray-300 rounded px-4 py-2">
                        <option>All Users</option>
                        <option>Active Users</option>
                        <option>Power Users</option>
                      </select>
                    </div>
                    <div className="flex items-center gap-2">
                      <input type="checkbox" className="w-6 h-6" />
                      <span className="text-lg text-gray-600">Custom Range</span>
                      <select className="text-lg border border-gray-300 rounded px-4 py-2">
                        <option>Last 3 Weeks</option>
                        <option>Last Month</option>
                        <option>Last 3 Months</option>
                      </select>
                    </div>
                  </div>

                  {/* Understanding Value Badge */}
                  <div className="mb-6">
                    <div className="inline-block bg-gray-800 text-white px-6 py-3 rounded-lg">
                      <div className="text-lg text-gray-300">understanding</div>
                      <div className="text-2xl font-semibold">Value: 32</div>
                    </div>
                  </div>

                  {/* Dashboard Content Grid */}
                  <div className="grid grid-cols-2 gap-6">
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <h3 className="text-2xl font-semibold text-gray-900 mb-4">Task Intent Patterns</h3>
                      <div className="h-64 bg-gray-50 rounded flex items-center justify-center">
                        <span className="text-xl text-gray-500">Bar Chart Placeholder</span>
                      </div>
                    </div>
                    
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <h3 className="text-2xl font-semibold text-gray-900 mb-4">Top Competencies</h3>
                      <div className="h-64 bg-gray-50 rounded flex items-center justify-center">
                        <span className="text-xl text-gray-500">Horizontal Bar Chart Placeholder</span>
                      </div>
                    </div>
                    
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <h3 className="text-2xl font-semibold text-gray-900 mb-4">Average Turn Count Trends</h3>
                      <div className="h-64 bg-gray-50 rounded flex items-center justify-center">
                        <span className="text-xl text-gray-500">Area Chart Placeholder</span>
                      </div>
                    </div>
                    
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <h3 className="text-2xl font-semibold text-gray-900 mb-4">Instruction Clarity Scores</h3>
                      <div className="h-64 bg-gray-50 rounded flex items-center justify-center">
                        <span className="text-xl text-gray-500">Pie Chart Placeholder</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}