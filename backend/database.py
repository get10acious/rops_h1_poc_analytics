import asyncpg
from typing import List, Dict, Any, Optional
from config import settings
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL database connections and operations."""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self) -> None:
        """Initialize database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                settings.database_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    def _convert_decimal_to_float(self, obj: Any) -> Any:
        """Recursively convert Decimal objects to float for JSON serialization."""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {key: self._convert_decimal_to_float(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimal_to_float(item) for item in obj]
        else:
            return obj
    
    async def execute_query(self, query: str, params: List[Any] = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        try:
            async with self.pool.acquire() as conn:
                if params:
                    rows = await conn.fetch(query, *params)
                else:
                    rows = await conn.fetch(query)
                
                # Convert records to dictionaries and handle datetime serialization
                result = []
                for row in rows:
                    row_dict = dict(row)
                    # Convert datetime objects to ISO format strings for JSON serialization
                    for key, value in row_dict.items():
                        if hasattr(value, 'isoformat'):  # Check if it's a datetime-like object
                            row_dict[key] = value.isoformat()
                    result.append(row_dict)
                
                # Convert Decimal objects to float for JSON serialization
                result = self._convert_decimal_to_float(result)
                return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def execute_non_query(self, query: str, params: List[Any] = None) -> str:
        """Execute an INSERT, UPDATE, or DELETE query."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        try:
            async with self.pool.acquire() as connection:
                if params:
                    result = await connection.execute(query, *params)
                else:
                    result = await connection.execute(query)
                
                return result
        except Exception as e:
            logger.error(f"Non-query execution failed: {e}")
            raise
    
    async def get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information."""
        schema_query = """
        SELECT 
            table_name,
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
        """
        
        try:
            columns = await self.execute_query(schema_query)
            
            # Group by table
            schema = {}
            for col in columns:
                table_name = col['table_name']
                if table_name not in schema:
                    schema[table_name] = []
                schema[table_name].append({
                    'name': col['column_name'],
                    'type': col['data_type'],
                    'nullable': col['is_nullable'] == 'YES',
                    'default': col['column_default']
                })
            
            return schema
        except Exception as e:
            logger.error(f"Failed to get schema info: {e}")
            raise


# Global database manager instance
db_manager = DatabaseManager()
