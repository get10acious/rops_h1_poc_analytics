"""
Visualization operations for RewardOps Analytics POC.

This module provides visualization operations using the Vizro MCP
for creating charts and dashboards.
"""

import logging
from typing import List, Dict, Any, Optional
from mcp_multi_client import mcp_manager

logger = logging.getLogger(__name__)

class VisualizationError(Exception):
    """Visualization operation error."""
    pass

class VisualizationOperations:
    """Visualization operations using Vizro MCP."""
    
    def __init__(self):
        self.server_name = "vizro"
    
    async def create_dashboard(
        self,
        title: str,
        data: List[Dict[str, Any]],
        chart_type: str = "bar",
        x_column: Optional[str] = None,
        y_column: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a dashboard using Vizro MCP.
        
        Args:
            title: Dashboard title
            data: Data to visualize
            chart_type: Type of chart (bar, line, pie, etc.)
            x_column: Column to use for x-axis
            y_column: Column to use for y-axis
            
        Returns:
            Vizro dashboard configuration
        """
        try:
            if not data:
                raise ValueError("Data cannot be empty")
            
            # Auto-detect columns if not provided
            if not x_column and data:
                x_column = list(data[0].keys())[0]
            if not y_column and data:
                y_column = list(data[0].keys())[1] if len(data[0].keys()) > 1 else x_column
            
            arguments = {
                "title": title,
                "data": data,
                "chart_type": chart_type,
                "x_column": x_column,
                "y_column": y_column
            }
            
            logger.debug(f"Creating dashboard with Vizro MCP: {title}")
            result = await mcp_manager.call_tool(self.server_name, "vizro-mcp:create_dashboard", arguments)
            
            # Extract result from MCP response
            if "content" in result and result["content"]:
                content = result["content"][0]
                if "text" in content:
                    import json
                    return json.loads(content["text"])
            
            return {}
            
        except Exception as e:
            logger.error(f"Dashboard creation failed: {e}")
            raise VisualizationError(f"Dashboard generation failed: {e}")
    
    async def create_chart(
        self,
        title: str,
        data: List[Dict[str, Any]],
        chart_type: str = "bar",
        x_column: Optional[str] = None,
        y_column: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a single chart using Vizro MCP.
        
        Args:
            title: Chart title
            data: Data to visualize
            chart_type: Type of chart (bar, line, pie, etc.)
            x_column: Column to use for x-axis
            y_column: Column to use for y-axis
            
        Returns:
            Vizro chart configuration
        """
        try:
            if not data:
                raise ValueError("Data cannot be empty")
            
            # Auto-detect columns if not provided
            if not x_column and data:
                x_column = list(data[0].keys())[0]
            if not y_column and data:
                y_column = list(data[0].keys())[1] if len(data[0].keys()) > 1 else x_column
            
            arguments = {
                "title": title,
                "data": data,
                "chart_type": chart_type,
                "x_column": x_column,
                "y_column": y_column
            }
            
            logger.debug(f"Creating chart with Vizro MCP: {title}")
            result = await mcp_manager.call_tool(self.server_name, "vizro-mcp:create_chart", arguments)
            
            # Extract result from MCP response
            if "content" in result and result["content"]:
                content = result["content"][0]
                if "text" in content:
                    import json
                    return json.loads(content["text"])
            
            return {}
            
        except Exception as e:
            logger.error(f"Chart creation failed: {e}")
            raise VisualizationError(f"Chart generation failed: {e}")
    
    async def get_available_chart_types(self) -> List[str]:
        """
        Get available chart types from Vizro MCP.
        
        Returns:
            List of available chart types
        """
        try:
            result = await mcp_manager.call_tool(self.server_name, "vizro-mcp:get_chart_types", {})
            
            if "content" in result and result["content"]:
                content = result["content"][0]
                if "text" in content:
                    import json
                    chart_types = json.loads(content["text"])
                    return chart_types if isinstance(chart_types, list) else [chart_types]
            
            # Return default chart types if MCP call fails
            return ["bar", "line", "pie", "scatter", "area"]
            
        except Exception as e:
            logger.error(f"Failed to get chart types: {e}")
            # Return default chart types if MCP call fails
            return ["bar", "line", "pie", "scatter", "area"]
    
    async def create_merchants_chart(
        self,
        data: List[Dict[str, Any]],
        chart_type: str = "bar"
    ) -> Dict[str, Any]:
        """Create a chart specifically for merchant data."""
        try:
            if not data:
                return {}
            
            # Determine the best columns for merchant data
            first_row = data[0]
            columns = list(first_row.keys())
            
            x_column = "name"
            y_column = "total_volume"
            
            # Find appropriate columns
            for col in columns:
                if col in ["name", "merchant_name"]:
                    x_column = col
                elif col in ["total_volume", "amount", "redemption_count"]:
                    y_column = col
            
            title = f"Top Merchants by {y_column.replace('_', ' ').title()}"
            
            return await self.create_chart(
                title=title,
                data=data,
                chart_type=chart_type,
                x_column=x_column,
                y_column=y_column
            )
            
        except Exception as e:
            logger.error(f"Error creating merchants chart: {e}")
            raise VisualizationError(f"Failed to create merchants chart: {e}")
    
    async def create_trends_chart(
        self,
        data: List[Dict[str, Any]],
        chart_type: str = "line"
    ) -> Dict[str, Any]:
        """Create a chart specifically for trend data."""
        try:
            if not data:
                return {}
            
            # Determine the best columns for trend data
            first_row = data[0]
            columns = list(first_row.keys())
            
            x_column = "period"
            y_column = "total_volume"
            
            # Find appropriate columns
            for col in columns:
                if col in ["period", "date", "time"]:
                    x_column = col
                elif col in ["total_volume", "redemption_count", "amount"]:
                    y_column = col
            
            title = f"Trends: {y_column.replace('_', ' ').title()} Over Time"
            
            return await self.create_chart(
                title=title,
                data=data,
                chart_type=chart_type,
                x_column=x_column,
                y_column=y_column
            )
            
        except Exception as e:
            logger.error(f"Error creating trends chart: {e}")
            raise VisualizationError(f"Failed to create trends chart: {e}")
    
    async def create_category_chart(
        self,
        data: List[Dict[str, Any]],
        chart_type: str = "pie"
    ) -> Dict[str, Any]:
        """Create a chart specifically for category data."""
        try:
            if not data:
                return {}
            
            # Determine the best columns for category data
            first_row = data[0]
            columns = list(first_row.keys())
            
            x_column = "category"
            y_column = "merchant_count"
            
            # Find appropriate columns
            for col in columns:
                if col in ["category", "type", "group"]:
                    x_column = col
                elif col in ["merchant_count", "count", "total_volume"]:
                    y_column = col
            
            title = f"Distribution by {x_column.replace('_', ' ').title()}"
            
            return await self.create_chart(
                title=title,
                data=data,
                chart_type=chart_type,
                x_column=x_column,
                y_column=y_column
            )
            
        except Exception as e:
            logger.error(f"Error creating category chart: {e}")
            raise VisualizationError(f"Failed to create category chart: {e}")
    
    async def create_multi_chart_dashboard(
        self,
        charts: List[Dict[str, Any]],
        title: str = "Analytics Dashboard"
    ) -> Dict[str, Any]:
        """Create a dashboard with multiple charts."""
        try:
            if not charts:
                raise ValueError("Charts list cannot be empty")
            
            arguments = {
                "title": title,
                "charts": charts,
                "layout": "grid"
            }
            
            logger.debug(f"Creating multi-chart dashboard: {title}")
            result = await mcp_manager.call_tool(self.server_name, "vizro-mcp:create_dashboard", arguments)
            
            # Extract result from MCP response
            if "content" in result and result["content"]:
                content = result["content"][0]
                if "text" in content:
                    import json
                    return json.loads(content["text"])
            
            return {}
            
        except Exception as e:
            logger.error(f"Multi-chart dashboard creation failed: {e}")
            raise VisualizationError(f"Multi-chart dashboard generation failed: {e}")
    
    def determine_chart_type(self, data: List[Dict[str, Any]], query: str) -> str:
        """Determine the best chart type based on data and query."""
        if not data:
            return "bar"
        
        query_lower = query.lower()
        
        # Time-based queries -> line chart
        if any(word in query_lower for word in ["trend", "over time", "month", "week", "day", "growth"]):
            return "line"
        
        # Category/distribution queries -> pie chart
        if any(word in query_lower for word in ["category", "distribution", "breakdown", "percentage"]):
            return "pie"
        
        # Comparison queries -> bar chart
        if any(word in query_lower for word in ["top", "best", "highest", "lowest", "compare"]):
            return "bar"
        
        # Correlation queries -> scatter plot
        if any(word in query_lower for word in ["correlation", "relationship", "scatter"]):
            return "scatter"
        
        # Default to bar chart
        return "bar"
    
    def format_data_for_visualization(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format data for better visualization."""
        if not data:
            return data
        
        formatted_data = []
        
        for row in data:
            formatted_row = {}
            for key, value in row.items():
                # Format numeric values
                if isinstance(value, (int, float)):
                    if key.endswith("_count") or key.endswith("_volume"):
                        formatted_row[key] = round(value, 2)
                    else:
                        formatted_row[key] = value
                else:
                    formatted_row[key] = value
            
            formatted_data.append(formatted_row)
        
        return formatted_data

# Global visualization operations instance
viz_ops = VisualizationOperations()
