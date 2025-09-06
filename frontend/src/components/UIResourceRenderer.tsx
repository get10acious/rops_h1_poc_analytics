'use client';

import React, { useEffect, useCallback, useState } from 'react';
import { UIResource } from '@/types/api';

interface UIResourceRendererProps {
  resource: UIResource;
  onUIAction?: (action: { type: string; payload?: Record<string, unknown>; componentId?: string }) => void;
  className?: string;
}

export const UIResourceRenderer: React.FC<UIResourceRendererProps> = ({ 
  resource, 
  onUIAction,
  className = '' 
}) => {
  const [iframeHeight, setIframeHeight] = useState(600);
  const [isLoading, setIsLoading] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleMessage = useCallback((event: MessageEvent) => {
    if (event.data && event.data.source === 'mcp-ui-component') {
      console.log('MCP UI Action:', event.data);
      
      // Handle height adjustment messages
      if (event.data.type === 'resize' && event.data.payload?.height) {
        setIframeHeight(event.data.payload.height);
      }
      
      // Handle loading state
      if (event.data.type === 'loaded') {
        setIsLoading(false);
      }
      
      onUIAction?.(event.data);
    }
  }, [onUIAction]);

  useEffect(() => {
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [handleMessage]);

  const handleIframeLoad = () => {
    setIsLoading(false);
  };

  if (resource.mimeType === 'text/html') {
    return (
      <>
        <div className={`ui-resource-container ${className}`}>
          {isLoading && (
            <div className="flex items-center justify-center p-4 bg-gray-50 rounded-t-lg border-b">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              <span className="ml-2 text-sm text-gray-600">Loading visualization...</span>
            </div>
          )}
          
          <iframe
            srcDoc={resource.text}
            style={{
              width: '100%',
              height: `${iframeHeight}px`,
              border: 'none',
              borderRadius: isLoading ? '0 0 12px 12px' : '12px',
              backgroundColor: 'transparent',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
              transition: 'height 0.3s ease-in-out'
            }}
            title="MCP-UI Resource"
            sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
            onLoad={handleIframeLoad}
          />
          
          {/* Fullscreen Button */}
          <div className="mt-2 flex justify-center">
            <button
              onClick={() => setIsFullscreen(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
              Fullscreen
            </button>
          </div>
          
          {/* Resource Info */}
          <div className="mt-2 text-xs text-gray-500 text-center">
            <span>UI Resource: {resource.uri}</span>
            {resource.encoding && <span className="ml-2">• Encoding: {resource.encoding}</span>}
          </div>
        </div>

        {/* Fullscreen Popup */}
        {isFullscreen && (
          <div className="fixed inset-0 z-50 bg-black bg-opacity-75 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg shadow-2xl w-full max-w-6xl h-[1000px] flex flex-col">
              {/* Fullscreen Header */}
              <div className="flex items-center justify-between p-4 border-b bg-gray-50 rounded-t-lg">
                <h3 className="text-lg font-semibold text-gray-800">Fullscreen View</h3>
                <button
                  onClick={() => setIsFullscreen(false)}
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  title="Close fullscreen view"
                  aria-label="Close fullscreen view"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              {/* Fullscreen Content */}
              <div className="flex-1 p-4 overflow-hidden">
                <iframe
                  srcDoc={resource.text}
                  className="w-full h-full border-0 rounded-lg"
                  title="MCP-UI Resource - Fullscreen"
                  sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
                />
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  if (resource.mimeType === 'application/json') {
    try {
      const jsonData = JSON.parse(resource.text);
      return (
        <div className={`ui-resource-container ${className}`}>
          <div className="bg-gray-50 p-4 rounded-lg border">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">JSON Data</h4>
            <pre className="text-xs text-gray-600 overflow-x-auto">
              {JSON.stringify(jsonData, null, 2)}
            </pre>
          </div>
        </div>
      );
    } catch {
      return (
        <div className={`ui-resource-error ${className}`}>
          <p className="text-red-500">Invalid JSON in resource</p>
        </div>
      );
    }
  }

  if (resource.mimeType?.startsWith('image/')) {
    return (
      <div className={`ui-resource-container ${className}`}>
        <img
          src={`data:${resource.mimeType};base64,${resource.text}`}
          alt="Resource content"
          className="w-full h-auto rounded-lg shadow-md"
        />
      </div>
    );
  }

  if (resource.mimeType === 'text/plain') {
    return (
      <div className={`ui-resource-container ${className}`}>
        <div className="bg-gray-50 p-4 rounded-lg border">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Text Content</h4>
          <pre className="text-sm text-gray-600 whitespace-pre-wrap">{resource.text}</pre>
        </div>
      </div>
    );
  }

  return (
    <div className={`ui-resource-error ${className}`}>
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700 font-medium">Unsupported Resource Type</p>
        <p className="text-red-600 text-sm mt-1">
          MIME Type: {resource.mimeType || 'Unknown'}
        </p>
        <p className="text-red-600 text-sm">
          URI: {resource.uri}
        </p>
      </div>
    </div>
  );
};
