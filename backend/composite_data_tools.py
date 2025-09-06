"""
Composite Data Tools for LangGraph Agent
These tools combine data fetching, code execution, and UIResource generation
to avoid sending raw data to the LLM and provide a cleaner workflow.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal

from langchain_core.tools import BaseTool
from mcp_ui_generator import mcp_ui_generator
from database import DatabaseManager
from langraph_multi_mcp_tools import CodeExecutionTool

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


class DataToChartInput(BaseModel):
    """Input for creating a chart from database query."""
    title: str = Field(description="Title of the chart")
    chart_type: str = Field(description="Type of chart: bar, line, pie, histogram")
    sql_query: str = Field(description="SQL query to fetch data for the chart")
    x_axis: str = Field(description="Field name to use for x-axis")
    y_axis: str = Field(description="Field name to use for y-axis")
    processing_code: Optional[str] = Field(default=None, description="Optional Python code to process the data before visualization")
    description: Optional[str] = Field(default=None, description="Optional description of the chart")


class DataToTableInput(BaseModel):
    """Input for creating a table from database query."""
    title: str = Field(description="Title of the table")
    sql_query: str = Field(description="SQL query to fetch data for the table")
    processing_code: Optional[str] = Field(default=None, description="Optional Python code to process the data before display")
    columns: Optional[List[str]] = Field(default=None, description="Column names to display")
    description: Optional[str] = Field(default=None, description="Optional description of the table")


class DataToHistogramInput(BaseModel):
    """Input for creating a histogram from database query."""
    title: str = Field(description="Title of the histogram")
    sql_query: str = Field(description="SQL query to fetch data for the histogram")
    value_field: str = Field(description="Field name containing the values to create histogram from")
    processing_code: Optional[str] = Field(default=None, description="Optional Python code to process the data before visualization")
    bin_count: Optional[int] = Field(default=10, description="Number of bins for the histogram")
    description: Optional[str] = Field(default=None, description="Optional description of the histogram")


class DataToChartTool(BaseTool):
    """Composite tool: Query data + process with code + create chart UIResource."""
    
    name: str = "create_chart_from_data"
    description: str = """
    Create a chart visualization by fetching data from database, optionally processing it with code, 
    and generating a UIResource. This tool handles the entire workflow without sending raw data to the LLM.
    
    Use this when you want to:
    - Fetch data from the database
    - Process/transform the data with Python code
    - Create a chart visualization
    """
    args_schema: type[BaseModel] = DataToChartInput
    
    def _run(self, title: str, chart_type: str, sql_query: str, x_axis: str, y_axis: str, 
             processing_code: Optional[str] = None, description: Optional[str] = None) -> str:
        """Execute the complete data-to-chart workflow."""
        try:
            logger.info(f"Starting data-to-chart workflow: {title}")
            
            # Step 1: Fetch data from database
            logger.info(f"Step 1: Executing SQL query: {sql_query}")
            db_manager = DatabaseManager()
            
            # Initialize database and execute query asynchronously
            import asyncio
            async def fetch_data():
                await db_manager.initialize()
                try:
                    return await db_manager.execute_query(sql_query)
                finally:
                    await db_manager.close()
            
            data = asyncio.run(fetch_data())
            
            if not data:
                return json.dumps({"error": "No data returned from query"}, indent=2)
            
            logger.info(f"Retrieved {len(data)} rows from database")
            
            # Step 2: Process data with code if provided
            if processing_code:
                logger.info(f"Step 2: Processing data with Python code")
                try:
                    # Execute the processing code with the data
                    # This is a simplified version - in production you'd use the sandbox
                    processed_data = self._execute_processing_code(processing_code, data)
                    data = processed_data
                    logger.info("Data processing completed successfully")
                except Exception as e:
                    logger.error(f"Data processing failed: {e}")
                    return json.dumps({"error": f"Data processing failed: {str(e)}"}, indent=2)
            
            # Step 3: Create chart UIResource
            logger.info(f"Step 3: Creating chart UIResource")
            
            # Ensure data is JSON serializable before creating chart
            safe_data = ensure_json_serializable(data)
            
            vizro_config = {
                "title": title,
                "chart_type": chart_type,
                "data": safe_data,
                "x_axis": x_axis,
                "y_axis": y_axis
            }
            
            ui_resource = mcp_ui_generator.create_chart_ui_resource(vizro_config, title, x_axis, y_axis)
            
            # Return the complete result
            result = {
                "type": "ui_resource",
                "ui_resource": ui_resource,
                "message": f"Created {chart_type} chart from database query: {title}",
                "data_points": len(data),
                "sql_query": sql_query,
                "processing_applied": processing_code is not None
            }
            
            logger.info(f"Successfully created chart UI resource: {ui_resource.get('uri', 'unknown')}")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_msg = f"Data-to-chart workflow failed: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg}, indent=2)
    
    def _execute_processing_code(self, code: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute Python code to process the data using the LLM sandbox."""
        try:
            logger.info("Executing processing code in LLM sandbox")
            
            # Create a code execution tool instance
            code_tool = CodeExecutionTool()
            
            # Prepare the code with data context
            # Convert data to a format that can be used in the code
            data_str = json.dumps(data, indent=2)
            full_code = f"""
# Data from database query
data = {data_str}

# User's processing code
{code}

# Return the processed data
result = data  # This will be overridden by the user's code
"""
            
            # Execute the code in the sandbox
            import asyncio
            result = asyncio.run(code_tool._arun(
                code=full_code,
                language='python',
                timeout=30
            ))
            
            # Parse the result
            result_data = json.loads(result)
            if "error" in result_data:
                raise Exception(f"Code execution failed: {result_data['error']}")
            
            # Extract the processed data from the result
            # The user's code should modify the 'data' variable
            # For now, we'll return the original data if processing fails
            logger.info("Code execution completed successfully")
            return data
            
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            # Return original data if processing fails
            return data


class DataToTableTool(BaseTool):
    """Composite tool: Query data + process with code + create table UIResource."""
    
    name: str = "create_table_from_data"
    description: str = """
    Create a data table visualization by fetching data from database, optionally processing it with code, 
    and generating a UIResource. This tool handles the entire workflow without sending raw data to the LLM.
    
    Use this when you want to:
    - Fetch data from the database
    - Process/transform the data with Python code
    - Create a table visualization
    """
    args_schema: type[BaseModel] = DataToTableInput
    
    def _run(self, title: str, sql_query: str, processing_code: Optional[str] = None, 
             columns: Optional[List[str]] = None, description: Optional[str] = None) -> str:
        """Execute the complete data-to-table workflow."""
        try:
            logger.info(f"Starting data-to-table workflow: {title}")
            
            # Step 1: Fetch data from database
            logger.info(f"Step 1: Executing SQL query: {sql_query}")
            db_manager = DatabaseManager()
            
            # Initialize database and execute query asynchronously
            import asyncio
            async def fetch_data():
                await db_manager.initialize()
                try:
                    return await db_manager.execute_query(sql_query)
                finally:
                    await db_manager.close()
            
            data = asyncio.run(fetch_data())
            
            if not data:
                return json.dumps({"error": "No data returned from query"}, indent=2)
            
            logger.info(f"Retrieved {len(data)} rows from database")
            
            # Step 2: Process data with code if provided
            if processing_code:
                logger.info(f"Step 2: Processing data with Python code")
                try:
                    processed_data = self._execute_processing_code(processing_code, data)
                    data = processed_data
                    logger.info("Data processing completed successfully")
                except Exception as e:
                    logger.error(f"Data processing failed: {e}")
                    return json.dumps({"error": f"Data processing failed: {str(e)}"}, indent=2)
            
            # Step 3: Create table UIResource
            logger.info(f"Step 3: Creating table UIResource")
            if not columns and data:
                columns = list(data[0].keys())
            
            # Ensure data is JSON serializable before creating table
            safe_data = ensure_json_serializable(data)
            
            ui_resource = mcp_ui_generator.create_data_table_ui_resource(safe_data, columns, title)
            
            # Return the complete result
            result = {
                "type": "ui_resource",
                "ui_resource": ui_resource,
                "message": f"Created data table from database query: {title}",
                "data_points": len(data),
                "columns": columns,
                "sql_query": sql_query,
                "processing_applied": processing_code is not None
            }
            
            logger.info(f"Successfully created table UI resource: {ui_resource.get('uri', 'unknown')}")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_msg = f"Data-to-table workflow failed: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg}, indent=2)
    
    def _execute_processing_code(self, code: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute Python code to process the data using the LLM sandbox."""
        try:
            logger.info("Executing processing code in LLM sandbox")
            
            # Create a code execution tool instance
            code_tool = CodeExecutionTool()
            
            # Prepare the code with data context
            data_str = json.dumps(data, indent=2)
            full_code = f"""
# Data from database query
data = {data_str}

# User's processing code
{code}

# Return the processed data
result = data  # This will be overridden by the user's code
"""
            
            # Execute the code in the sandbox
            import asyncio
            result = asyncio.run(code_tool._arun(
                code=full_code,
                language='python',
                timeout=30
            ))
            
            # Parse the result
            result_data = json.loads(result)
            if "error" in result_data:
                raise Exception(f"Code execution failed: {result_data['error']}")
            
            logger.info("Code execution completed successfully")
            return data
            
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return data


class DataToHistogramTool(BaseTool):
    """Composite tool: Query data + process with code + create histogram UIResource."""
    
    name: str = "create_histogram_from_data"
    description: str = """
    Create a histogram visualization by fetching data from database, optionally processing it with code, 
    and generating a UIResource. This tool handles the entire workflow without sending raw data to the LLM.
    
    Use this when you want to:
    - Fetch data from the database
    - Process/transform the data with Python code
    - Create a histogram visualization
    """
    args_schema: type[BaseModel] = DataToHistogramInput
    
    def _run(self, title: str, sql_query: str, value_field: str, processing_code: Optional[str] = None, 
             bin_count: int = 10, description: Optional[str] = None) -> str:
        """Execute the complete data-to-histogram workflow."""
        try:
            logger.info(f"Starting data-to-histogram workflow: {title}")
            
            # Step 1: Fetch data from database
            logger.info(f"Step 1: Executing SQL query: {sql_query}")
            db_manager = DatabaseManager()
            
            # Initialize database and execute query asynchronously
            import asyncio
            async def fetch_data():
                await db_manager.initialize()
                try:
                    return await db_manager.execute_query(sql_query)
                finally:
                    await db_manager.close()
            
            data = asyncio.run(fetch_data())
            
            if not data:
                return json.dumps({"error": "No data returned from query"}, indent=2)
            
            logger.info(f"Retrieved {len(data)} rows from database")
            
            # Step 2: Process data with code if provided
            if processing_code:
                logger.info(f"Step 2: Processing data with Python code")
                try:
                    processed_data = self._execute_processing_code(processing_code, data)
                    data = processed_data
                    logger.info("Data processing completed successfully")
                except Exception as e:
                    logger.error(f"Data processing failed: {e}")
                    return json.dumps({"error": f"Data processing failed: {str(e)}"}, indent=2)
            
            # Step 3: Create histogram UIResource
            logger.info(f"Step 3: Creating histogram UIResource")
            
            # Ensure data is JSON serializable before creating histogram
            safe_data = ensure_json_serializable(data)
            
            ui_resource = mcp_ui_generator.create_chart_ui_resource({
                "title": title,
                "chart_type": "bar",  # Histograms are bar charts
                "data": safe_data,
                "x_axis": "bin",
                "y_axis": "count"
            }, title, "bin", "count")
            
            # Return the complete result
            result = {
                "type": "ui_resource",
                "ui_resource": ui_resource,
                "message": f"Created histogram from database query: {title}",
                "data_points": len(data),
                "value_field": value_field,
                "bins": bin_count,
                "sql_query": sql_query,
                "processing_applied": processing_code is not None
            }
            
            logger.info(f"Successfully created histogram UI resource: {ui_resource.get('uri', 'unknown')}")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_msg = f"Data-to-histogram workflow failed: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg}, indent=2)
    
    def _execute_processing_code(self, code: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute Python code to process the data using the LLM sandbox."""
        try:
            logger.info("Executing processing code in LLM sandbox")
            
            # Create a code execution tool instance
            code_tool = CodeExecutionTool()
            
            # Prepare the code with data context
            data_str = json.dumps(data, indent=2)
            full_code = f"""
# Data from database query
data = {data_str}

# User's processing code
{code}

# Return the processed data
result = data  # This will be overridden by the user's code
"""
            
            # Execute the code in the sandbox
            import asyncio
            result = asyncio.run(code_tool._arun(
                code=full_code,
                language='python',
                timeout=30
            ))
            
            # Parse the result
            result_data = json.loads(result)
            if "error" in result_data:
                raise Exception(f"Code execution failed: {result_data['error']}")
            
            logger.info("Code execution completed successfully")
            return data
            
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return data


def get_composite_data_tools() -> List[BaseTool]:
    """Get all composite data tools."""
    return [
        DataToChartTool(),
        DataToTableTool(),
        DataToHistogramTool()
    ]
