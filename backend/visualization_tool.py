"""
Visualization Tool for LangGraph Agent
Provides tools for creating charts and visualizations using the MCP UI generator.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal

from langchain_core.tools import BaseTool
from mcp_ui_generator import mcp_ui_generator

logger = logging.getLogger(__name__)


def ensure_json_serializable(obj: Any) -> Any:
    """Recursively ensure all objects are JSON serializable."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: ensure_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [ensure_json_serializable(item) for item in obj]
    elif hasattr(obj, 'isoformat'):  # datetime objects
        return obj.isoformat()
    else:
        return obj


class CreateChartInput(BaseModel):
    """Input for creating a chart visualization."""
    title: str = Field(description="Title of the chart")
    chart_type: str = Field(description="Type of chart: bar, line, pie, histogram")
    data: List[Dict[str, Any]] = Field(description="Data to visualize as a list of dictionaries")
    x_axis: str = Field(description="Field name to use for x-axis")
    y_axis: str = Field(description="Field name to use for y-axis")
    description: Optional[str] = Field(default=None, description="Optional description of the chart")


class CreateTableInput(BaseModel):
    """Input for creating a data table visualization."""
    title: str = Field(description="Title of the table")
    data: List[Dict[str, Any]] = Field(description="Data to display in the table")
    columns: Optional[List[str]] = Field(default=None, description="Column names to display (if not provided, will use all keys from first data row)")
    description: Optional[str] = Field(default=None, description="Optional description of the table")


class CreateHistogramInput(BaseModel):
    """Input for creating a histogram visualization."""
    title: str = Field(description="Title of the histogram")
    data: List[Dict[str, Any]] = Field(description="Data to create histogram from")
    value_field: str = Field(description="Field name containing the values to create histogram from")
    bin_count: Optional[int] = Field(default=10, description="Number of bins for the histogram")
    description: Optional[str] = Field(default=None, description="Optional description of the histogram")


class CreateChartTool(BaseTool):
    """Tool for creating chart visualizations with UIResource generation."""
    
    name: str = "create_chart"
    description: str = """
    DEPRECATED: Use create_chart_from_data instead.
    Create a chart visualization from data and generate a UIResource.
    This tool requires pre-fetched data and should NOT be used directly.
    
    Use create_chart_from_data for all chart creation needs.
    """
    args_schema: type[BaseModel] = CreateChartInput
    
    def _run(self, title: str, chart_type: str, data: List[Dict[str, Any]], 
             x_axis: str, y_axis: str, description: Optional[str] = None) -> str:
        """Create a chart visualization."""
        try:
            logger.info(f"Creating chart: {title} (type: {chart_type})")
            
            if not data:
                return json.dumps({"error": "No data provided for chart"}, indent=2)
            
            # Ensure data is JSON serializable
            safe_data = ensure_json_serializable(data)
            
            # Create chart configuration
            vizro_config = {
                "title": title,
                "chart_type": chart_type,
                "data": safe_data,
                "x_axis": x_axis,
                "y_axis": y_axis
            }
            
            # Generate UI resource
            ui_resource = mcp_ui_generator.create_chart_ui_resource(vizro_config, title)
            
            # Return the result
            result = {
                "type": "ui_resource",
                "ui_resource": ui_resource,
                "message": f"Created {chart_type} chart: {title}",
                "data_points": len(data),
                "chart_type": chart_type
            }
            
            logger.info(f"Successfully created chart UI resource: {ui_resource.get('uri', 'unknown')}")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_msg = f"Chart creation failed: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg}, indent=2)


class CreateTableTool(BaseTool):
    """Tool for creating data table visualizations with UIResource generation."""
    
    name: str = "create_table"
    description: str = """
    DEPRECATED: Use create_table_from_data instead.
    Create a data table visualization from data and generate a UIResource.
    This tool requires pre-fetched data and should NOT be used directly.
    
    Use create_table_from_data for all table creation needs.
    """
    args_schema: type[BaseModel] = CreateTableInput
    
    def _run(self, title: str, data: List[Dict[str, Any]], 
             columns: Optional[List[str]] = None, description: Optional[str] = None) -> str:
        """Create a data table visualization."""
        try:
            logger.info(f"Creating table: {title}")
            
            if not data:
                return json.dumps({"error": "No data provided for table"}, indent=2)
            
            # Determine columns if not provided
            if not columns and data:
                columns = list(data[0].keys())
            
            # Ensure data is JSON serializable
            safe_data = ensure_json_serializable(data)
            
            # Generate UI resource
            ui_resource = mcp_ui_generator.create_data_table_ui_resource(safe_data, columns, title)
            
            # Return the result
            result = {
                "type": "ui_resource",
                "ui_resource": ui_resource,
                "message": f"Created data table: {title}",
                "data_points": len(data),
                "columns": columns
            }
            
            logger.info(f"Successfully created table UI resource: {ui_resource.get('uri', 'unknown')}")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_msg = f"Table creation failed: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg}, indent=2)


class CreateHistogramTool(BaseTool):
    """Tool for creating histogram visualizations with UIResource generation."""
    
    name: str = "create_histogram"
    description: str = """
    DEPRECATED: Use create_histogram_from_data instead.
    Create a histogram visualization from data and generate a UIResource.
    This tool requires pre-fetched data and should NOT be used directly.
    
    Use create_histogram_from_data for all histogram creation needs.
    """
    args_schema: type[BaseModel] = CreateHistogramInput
    
    def _run(self, title: str, data: List[Dict[str, Any]], value_field: str, 
             bin_count: int = 10, description: Optional[str] = None) -> str:
        """Create a histogram visualization."""
        try:
            logger.info(f"Creating histogram: {title}")
            
            if not data:
                return json.dumps({"error": "No data provided for histogram"}, indent=2)
            
            # Extract values for histogram
            values = []
            for item in data:
                if value_field in item:
                    try:
                        values.append(float(item[value_field]))
                    except (ValueError, TypeError):
                        continue
            
            if not values:
                return json.dumps({"error": f"No valid numeric values found in field '{value_field}'"}, indent=2)
            
            # Create histogram bins
            min_val = min(values)
            max_val = max(values)
            bin_width = (max_val - min_val) / bin_count
            
            bins = []
            for i in range(bin_count):
                bin_start = min_val + i * bin_width
                bin_end = bin_start + bin_width
                bin_count_val = sum(1 for v in values if bin_start <= v < bin_end)
                bins.append({
                    "bin": f"{bin_start:.2f}-{bin_end:.2f}",
                    "count": bin_count_val
                })
            
            # Create chart configuration for histogram
            vizro_config = {
                "title": title,
                "chart_type": "bar",
                "data": bins,
                "x_axis": "bin",
                "y_axis": "count"
            }
            
            # Generate UI resource
            ui_resource = mcp_ui_generator.create_chart_ui_resource(vizro_config, title)
            
            # Return the result
            result = {
                "type": "ui_resource",
                "ui_resource": ui_resource,
                "message": f"Created histogram: {title}",
                "data_points": len(values),
                "bins": bin_count,
                "value_field": value_field
            }
            
            logger.info(f"Successfully created histogram UI resource: {ui_resource.get('uri', 'unknown')}")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_msg = f"Histogram creation failed: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg}, indent=2)


def get_visualization_tools() -> List[BaseTool]:
    """Get all visualization tools."""
    return [
        CreateChartTool(),
        CreateTableTool(),
        CreateHistogramTool()
    ]