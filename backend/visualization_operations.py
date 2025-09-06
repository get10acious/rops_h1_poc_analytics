"""
Visualization operations module for MCP UI Chat Analytics POC.

This module provides visualization operations using the MCP UI Generator
and integrates with the analytics pipeline.
"""

import logging
from typing import List, Dict, Any, Optional
from mcp_ui_generator import mcp_ui_generator

logger = logging.getLogger(__name__)


class VisualizationError(Exception):
    """Custom exception for visualization errors."""
    pass


class VisualizationOperations:
    """Visualization operations using MCP UI Generator."""
    
    def __init__(self):
        self.ui_generator = mcp_ui_generator
        self.logger = logging.getLogger(__name__)
    
    async def create_dashboard(
        self,
        title: str,
        metrics: List[Dict[str, Any]],
        charts: List[Dict[str, Any]],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a dashboard using MCP UI Generator.
        
        Args:
            title: Dashboard title
            metrics: List of metrics to display
            charts: List of chart configurations
            description: Optional dashboard description
            
        Returns:
            UI Resource for dashboard
        """
        try:
            self.logger.debug(f"Creating dashboard with UI Generator: {title}")
            result = self.ui_generator.create_dashboard_ui_resource(metrics, charts, title)
            
            if result:
                self.logger.info(f"Dashboard created successfully: {title}")
                return result
            else:
                raise VisualizationError("Dashboard creation returned empty result")
            
        except Exception as e:
            self.logger.error(f"Dashboard creation failed: {e}")
            raise VisualizationError(f"Dashboard generation failed: {e}")
    
    async def create_chart(
        self,
        chart_type: str,
        data: List[Dict[str, Any]],
        title: str,
        x_axis: str,
        y_axis: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a single chart using MCP UI Generator.
        
        Args:
            chart_type: Type of chart (bar, line, pie, etc.)
            data: Chart data
            title: Chart title
            x_axis: X-axis field name
            y_axis: Y-axis field name
            description: Optional chart description
            
        Returns:
            UI Resource for chart
        """
        try:
            ui_config = {
                "chart_type": chart_type,
                "data": data,
                "title": title,
                "x_axis": x_axis,
                "y_axis": y_axis,
                "description": description
            }
            
            self.logger.debug(f"Creating chart with UI Generator: {title}")
            result = self.ui_generator.create_chart_ui_resource(ui_config, title)
            
            if result:
                self.logger.info(f"Chart created successfully: {title}")
                return result
            else:
                raise VisualizationError("Chart creation returned empty result")
            
        except Exception as e:
            self.logger.error(f"Chart creation failed: {e}")
            raise VisualizationError(f"Chart generation failed: {e}")
    
    async def get_available_chart_types(self) -> List[str]:
        """
        Get available chart types from UI config.
        
        Returns:
            List of available chart types
        """
        try:
            # Return predefined chart types from UI config
            chart_types = ["bar", "line", "pie", "scatter", "area", "heatmap"]
            self.logger.debug(f"Available chart types: {chart_types}")
            return chart_types
            
        except Exception as e:
            self.logger.error(f"Failed to get chart types: {e}")
            raise VisualizationError(f"Chart types retrieval failed: {e}")
    
    async def create_data_table(
        self,
        data: List[Dict[str, Any]],
        columns: List[str],
        title: str = "Data Table"
    ) -> Dict[str, Any]:
        """
        Create a data table visualization.
        
        Args:
            data: Table data
            columns: Column names
            title: Table title
            
        Returns:
            UI Resource for data table
        """
        try:
            self.logger.debug(f"Creating data table with UI Generator: {title}")
            result = self.ui_generator.create_data_table_ui_resource(data, columns, title)
            
            if result:
                self.logger.info(f"Data table created successfully: {title}")
                return result
            else:
                raise VisualizationError("Data table creation returned empty result")
            
        except Exception as e:
            self.logger.error(f"Data table creation failed: {e}")
            raise VisualizationError(f"Data table generation failed: {e}")
    
    async def create_form(
        self,
        form_config: Dict[str, Any],
        title: str = "Data Input Form"
    ) -> Dict[str, Any]:
        """
        Create a data input form.
        
        Args:
            form_config: Form configuration
            title: Form title
            
        Returns:
            UI Resource for form
        """
        try:
            self.logger.debug(f"Creating form with UI Generator: {title}")
            result = self.ui_generator.create_form_ui_resource(form_config, title)
            
            if result:
                self.logger.info(f"Form created successfully: {title}")
                return result
            else:
                raise VisualizationError("Form creation returned empty result")
            
        except Exception as e:
            self.logger.error(f"Form creation failed: {e}")
            raise VisualizationError(f"Form generation failed: {e}")
    
    def validate_chart_data(self, data: List[Dict[str, Any]], x_axis: str, y_axis: str) -> bool:
        """
        Validate chart data structure.
        
        Args:
            data: Chart data to validate
            x_axis: X-axis field name
            y_axis: Y-axis field name
            
        Returns:
            True if data is valid
        """
        try:
            if not data:
                return False
            
            for row in data:
                if not isinstance(row, dict):
                    return False
                if x_axis not in row or y_axis not in row:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Data validation failed: {e}")
            return False
    
    async def create_analytics_dashboard_with_data(
        self,
        title: str,
        query_results: List[Dict[str, Any]],
        chart_configs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a complete analytics dashboard with processed data.
        
        Args:
            title: Dashboard title
            query_results: Raw query results
            chart_configs: Chart configuration specifications
            
        Returns:
            Complete dashboard UI Resource
        """
        try:
            # Process metrics from query results
            processed_metrics = []
            if query_results:
                total_records = len(query_results)
                processed_metrics.append({
                    "label": "Total Records",
                    "value": str(total_records),
                    "description": "Total number of records"
                })
            
            # Process charts
            processed_charts = []
            for config in chart_configs:
                if self.validate_chart_data(query_results, 
                                          config.get("x_axis", ""), 
                                          config.get("y_axis", "")):
                    chart_result = await self.create_chart(
                        chart_type=config.get("chart_type", "bar"),
                        data=query_results,
                        title=config.get("title", "Chart"),
                        x_axis=config.get("x_axis"),
                        y_axis=config.get("y_axis"),
                        description=config.get("description")
                    )
                    processed_charts.append(chart_result)
            
            # Create dashboard
            result = self.ui_generator.create_dashboard_ui_resource(processed_metrics, processed_charts, title)
            
            if result:
                self.logger.info(f"Analytics dashboard created successfully: {title}")
                return result
            else:
                raise VisualizationError("Analytics dashboard creation returned empty result")
            
        except Exception as e:
            self.logger.error(f"Analytics dashboard creation failed: {e}")
            raise VisualizationError(f"Analytics dashboard generation failed: {e}")


# Global visualization operations instance
visualization_ops = VisualizationOperations()