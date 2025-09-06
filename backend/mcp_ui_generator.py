"""
MCP UI Resource Generator for Natural Language Analytics System
Converts data into UIResource JSON payloads for the frontend.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


def createUIResource(config):
    """
    Create a UIResource according to the MCP-UI specification.
    
    Args:
        config: Dictionary containing:
            - uri: Resource URI (required)
            - content: Content configuration (required)
            - encoding: Content encoding (optional, defaults to 'text')
    
    Returns:
        UIResource object with proper structure
    """
    uri = config.get("uri", "ui://generated/component")
    content = config.get("content", {})
    encoding = config.get("encoding", "text")
    
    # Handle different content types
    content_type = content.get("type", "rawHtml")
    
    if content_type == "rawHtml":
        # Inline HTML content
        html_string = content.get("htmlString", "")
        return {
            "uri": uri,
            "mimeType": "text/html",
            "text": html_string,
            "encoding": encoding
        }
    elif content_type == "externalUrl":
        # External URL for iframe
        iframe_url = content.get("iframeUrl", "")
        html_content = f'<iframe src="{iframe_url}" style="width:100%;height:100%;border:none;"></iframe>'
        return {
            "uri": uri,
            "mimeType": "text/html",
            "text": html_content,
            "encoding": encoding
        }
    else:
        # Default to raw HTML
        return {
            "uri": uri,
            "mimeType": "text/html",
            "text": str(content),
            "encoding": encoding
        }


class MCPUIGenerator:
    """Generator for MCP UI Resources."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_chart_ui_resource(self, chart_config: Dict[str, Any], title: str = "Chart", x_axis: str = None, y_axis: str = None) -> Dict[str, Any]:
        """
        Create a chart UI resource from chart configuration.
        
        Args:
            chart_config: Chart configuration (e.g., Plotly, Vizro config)
            title: Chart title
            
        Returns:
            UIResource for chart visualization
        """
        try:
            # Create a simple chart HTML
            chart_html = self._generate_chart_html(chart_config, title, x_axis, y_axis)
            
            return createUIResource({
                "uri": f"ui://chart/{datetime.now().timestamp()}",
                "content": {
                    "type": "rawHtml",
                    "htmlString": chart_html
                }
            })
            
        except Exception as e:
            self.logger.error(f"Failed to create chart UI resource: {e}")
            return self._create_error_ui_resource(f"Chart generation failed: {e}")
    
    def create_data_table_ui_resource(self, data: List[Dict[str, Any]], columns: List[str], title: str = "Data Table") -> Dict[str, Any]:
        """
        Create a data table UI resource.
        
        Args:
            data: List of dictionaries representing table data
            columns: List of column names
            title: Table title
            
        Returns:
            UIResource for data table
        """
        try:
            # Create a simple table HTML
            table_html = self._generate_table_html(data, columns, title)
            
            return createUIResource({
                "uri": f"ui://table/{datetime.now().timestamp()}",
                "content": {
                    "type": "rawHtml",
                    "htmlString": table_html
                }
            })
            
        except Exception as e:
            self.logger.error(f"Failed to create table UI resource: {e}")
            return self._create_error_ui_resource(f"Table generation failed: {e}")
    
    def _generate_chart_html(self, chart_config: Dict[str, Any], title: str, x_axis: str = None, y_axis: str = None) -> str:
        """Generate HTML for chart visualization."""
        # Simple chart HTML using Chart.js or similar
        chart_id = f"chart_{datetime.now().timestamp()}"
        
        # Extract data for simple bar chart
        data_points = chart_config.get("data", [])
        
        if not data_points:
            return f"<div><h3>{title}</h3><p>No data available for chart</p></div>"
        
        # Fallback to first two keys if x_axis/y_axis not provided
        if not x_axis or not y_axis:
            first_row = data_points[0] if data_points else {}
            keys = list(first_row.keys())
            x_axis = x_axis or (keys[0] if len(keys) > 0 else 'x')
            y_axis = y_axis or (keys[1] if len(keys) > 1 else 'y')
        
        # Simple HTML chart
        html = f"""
        <div style="padding: 20px;">
            <h3>{title}</h3>
            <div id="{chart_id}" style="width: 100%; height: 400px;">
                <canvas id="{chart_id}_canvas"></canvas>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script>
                const ctx = document.getElementById('{chart_id}_canvas').getContext('2d');
                const chartData = {json.dumps(data_points)};
                
                // Simple bar chart
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: chartData.map(item => item['{x_axis}']),
                        datasets: [{{
                            label: '{title}',
                            data: chartData.map(item => item['{y_axis}']),
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        scales: {{
                            y: {{
                                beginAtZero: true
                            }}
                        }}
                    }}
                }});
            </script>
        </div>
        """
        return html
    
    def _generate_table_html(self, data: List[Dict[str, Any]], columns: List[str], title: str) -> str:
        """Generate HTML for data table."""
        if not data:
            return f"<div><h3>{title}</h3><p>No data available</p></div>"
        
        # Create table HTML
        html = f"""
        <div style="padding: 20px;">
            <h3>{title}</h3>
            <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
        """
        
        # Add headers
        for col in columns:
            html += f'<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">{col}</th>'
        
        html += """
                    </tr>
                </thead>
                <tbody>
        """
        
        # Add data rows
        for row in data:
            html += '<tr>'
            for col in columns:
                value = row.get(col, '')
                html += f'<td style="border: 1px solid #ddd; padding: 8px;">{value}</td>'
            html += '</tr>'
        
        html += """
                </tbody>
            </table>
        </div>
        """
        
        return html
    
    def _create_error_ui_resource(self, error_message: str) -> Dict[str, Any]:
        """Create an error UI resource."""
        error_html = f"""
        <div style="padding: 20px; color: red; border: 1px solid red; border-radius: 5px;">
            <h3>Error</h3>
            <p>{error_message}</p>
        </div>
        """
        
        return createUIResource({
            "uri": f"ui://error/{datetime.now().timestamp()}",
            "content": {
                "type": "rawHtml",
                "htmlString": error_html
            }
        })


# Global instance
mcp_ui_generator = MCPUIGenerator()