'use client'

import { X, BarChart3, Users, ShoppingBag, Gift, TrendingUp, Settings, HelpCircle } from 'lucide-react'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const menuItems = [
    { icon: BarChart3, label: 'Analytics', href: '/', active: true },
    { icon: Users, label: 'Users', href: '/users' },
    { icon: ShoppingBag, label: 'Merchants', href: '/merchants' },
    { icon: Gift, label: 'Redemptions', href: '/redemptions' },
    { icon: TrendingUp, label: 'Campaigns', href: '/campaigns' },
    { icon: Settings, label: 'Settings', href: '/settings' },
    { icon: HelpCircle, label: 'Help', href: '/help' }
  ]
  
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Navigation</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500 lg:hidden"
          >
            <X className="h-6 w-6" />
          </button>
        </div>
        
        <nav className="mt-8 px-4">
          <ul className="space-y-2">
            {menuItems.map((item) => {
              const Icon = item.icon
              return (
                <li key={item.label}>
                  <a
                    href={item.href}
                    className={`flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                      item.active
                        ? 'bg-primary-100 text-primary-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="mr-3 h-5 w-5" />
                    {item.label}
                  </a>
                </li>
              )
            })}
          </ul>
        </nav>
        
        {/* Quick stats */}
        <div className="mt-8 px-4">
          <h3 className="text-sm font-medium text-gray-900 mb-4">Quick Stats</h3>
          <div className="space-y-3">
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500">Total Users</p>
              <p className="text-lg font-semibold text-gray-900">12,345</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500">Active Merchants</p>
              <p className="text-lg font-semibold text-gray-900">1,234</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500">This Month's Redemptions</p>
              <p className="text-lg font-semibold text-gray-900">5,678</p>
            </div>
          </div>
        </div>
        
        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
          <div className="text-xs text-gray-500">
            <p>RewardOps Analytics POC</p>
            <p>Version 1.0.0</p>
          </div>
        </div>
      </div>
    </>
  )
}
