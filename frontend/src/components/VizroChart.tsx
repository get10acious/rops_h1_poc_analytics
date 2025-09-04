'use client'

import { VizroConfig } from '@/types/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, AreaChart, Area } from 'recharts'

interface VizroChartProps {
  config: VizroConfig
  className?: string
}

const COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#84cc16', '#f97316']

export const VizroChart: React.FC<VizroChartProps> = ({ config, className = '' }) => {
  const { title, chart_type, data, x_column, y_column, width = 800, height = 400 } = config
  
  const renderChart = () => {
    if (!data || data.length === 0) {
      return (
        <div className="flex items-center justify-center h-64 text-gray-500">
          <p>No data available for visualization</p>
        </div>
      )
    }
    
    const xKey = x_column || Object.keys(data[0])[0]
    const yKey = y_column || Object.keys(data[0])[1]
    
    switch (chart_type) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xKey} />
              <YAxis />
              <Tooltip />
              <Bar dataKey={yKey} fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        )
        
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xKey} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey={yKey} stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        )
        
      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey={yKey}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        )
        
      case 'area':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xKey} />
              <YAxis />
              <Tooltip />
              <Area type="monotone" dataKey={yKey} stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        )
        
      case 'scatter':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xKey} />
              <YAxis />
              <Tooltip />
              <Bar dataKey={yKey} fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        )
        
      default:
        return (
          <div className="flex items-center justify-center h-64 text-gray-500">
            <p>Unsupported chart type: {chart_type}</p>
          </div>
        )
    }
  }
  
  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
      <h4 className="text-lg font-semibold text-gray-900 mb-4">{title}</h4>
      <div className="chart-container">
        {renderChart()}
      </div>
      
      {/* Data summary */}
      {data && data.length > 0 && (
        <div className="mt-4 text-sm text-gray-600">
          <p>Data points: {data.length}</p>
          {x_column && y_column && (
            <p>Showing {x_column} vs {y_column}</p>
          )}
        </div>
      )}
    </div>
  )
}
