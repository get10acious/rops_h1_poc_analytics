"""
Database operations for RewardOps Analytics POC.

This module provides database operations using the MCP Database Toolbox
for executing SQL queries and retrieving data.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from mcp_multi_client import mcp_manager

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Database operation error."""
    pass

class DatabaseOperations:
    """Database operations using MCP Database Toolbox."""
    
    def __init__(self):
        self.server_name = "database"
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query using the Database Toolbox MCP.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            List of result dictionaries
            
        Raises:
            DatabaseError: If query execution fails
        """
        try:
            logger.debug(f"Executing query: {query}")
            
            arguments = {"query": query}
            if params:
                arguments["params"] = params
            
            result = await mcp_manager.call_tool(self.server_name, "db-toolbox:query", arguments)
            
            # Extract data from MCP response
            if "content" in result and result["content"]:
                content = result["content"][0]
                if "text" in content:
                    # Parse the text content as JSON
                    import json
                    data = json.loads(content["text"])
                    return data if isinstance(data, list) else [data]
            
            return []
            
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise DatabaseError(f"Query execution failed: {e}")
    
    async def get_schema(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get database schema information.
        
        Args:
            table_name: Optional specific table name
            
        Returns:
            Schema information dictionary
        """
        try:
            arguments = {}
            if table_name:
                arguments["table"] = table_name
            
            result = await mcp_manager.call_tool(self.server_name, "db-toolbox:get_schema", arguments)
            
            if "content" in result and result["content"]:
                content = result["content"][0]
                if "text" in content:
                    import json
                    return json.loads(content["text"])
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get schema: {e}")
            raise DatabaseError(f"Schema retrieval failed: {e}")
    
    async def list_tables(self) -> List[str]:
        """
        List all tables in the database.
        
        Returns:
            List of table names
        """
        try:
            result = await mcp_manager.call_tool(self.server_name, "db-toolbox:list_tables", {})
            
            if "content" in result and result["content"]:
                content = result["content"][0]
                if "text" in content:
                    import json
                    tables = json.loads(content["text"])
                    return tables if isinstance(tables, list) else [tables]
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            raise DatabaseError(f"Table listing failed: {e}")
    
    async def get_merchants_by_redemption_volume(
        self, 
        limit: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get top merchants by redemption volume."""
        try:
            query = """
            SELECT 
                m.id,
                m.name,
                m.category,
                COUNT(r.id) as redemption_count,
                COALESCE(SUM(r.amount), 0) as total_volume,
                COALESCE(AVG(r.amount), 0) as avg_redemption_value
            FROM merchants m
            LEFT JOIN redemptions r ON m.id = r.merchant_id
            WHERE m.is_active = true
            """
            
            params = {}
            if start_date:
                query += " AND r.redemption_date >= %(start_date)s"
                params["start_date"] = start_date
            if end_date:
                query += " AND r.redemption_date <= %(end_date)s"
                params["end_date"] = end_date
                
            query += """
            GROUP BY m.id, m.name, m.category
            ORDER BY total_volume DESC NULLS LAST
            LIMIT %(limit)s
            """
            params["limit"] = limit
            
            return await self.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Error getting merchants by redemption volume: {e}")
            raise DatabaseError(f"Failed to get merchants by redemption volume: {e}")
    
    async def get_users_by_redemption_activity(
        self,
        limit: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get top users by redemption activity."""
        try:
            query = """
            SELECT 
                u.id,
                u.email,
                u.first_name,
                u.last_name,
                u.tier,
                COUNT(r.id) as redemption_count,
                COALESCE(SUM(r.amount), 0) as total_spent,
                COALESCE(SUM(r.points_used), 0) as total_points_used
            FROM users u
            LEFT JOIN redemptions r ON u.id = r.user_id
            WHERE u.is_active = true
            """
            
            params = {}
            if start_date:
                query += " AND r.redemption_date >= %(start_date)s"
                params["start_date"] = start_date
            if end_date:
                query += " AND r.redemption_date <= %(end_date)s"
                params["end_date"] = end_date
                
            query += """
            GROUP BY u.id, u.email, u.first_name, u.last_name, u.tier
            ORDER BY total_spent DESC NULLS LAST
            LIMIT %(limit)s
            """
            params["limit"] = limit
            
            return await self.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Error getting users by redemption activity: {e}")
            raise DatabaseError(f"Failed to get users by redemption activity: {e}")
    
    async def get_redemption_trends(
        self,
        days: int = 30,
        group_by: str = "day"
    ) -> List[Dict[str, Any]]:
        """Get redemption trends over time."""
        try:
            if group_by == "day":
                date_format = "DATE(r.redemption_date)"
            elif group_by == "week":
                date_format = "DATE_TRUNC('week', r.redemption_date)"
            elif group_by == "month":
                date_format = "DATE_TRUNC('month', r.redemption_date)"
            else:
                date_format = "DATE(r.redemption_date)"
            
            query = f"""
            SELECT 
                {date_format} as period,
                COUNT(r.id) as redemption_count,
                COALESCE(SUM(r.amount), 0) as total_volume,
                COALESCE(AVG(r.amount), 0) as avg_redemption_value
            FROM redemptions r
            WHERE r.redemption_date >= CURRENT_DATE - INTERVAL '{days} days'
            AND r.status = 'completed'
            GROUP BY {date_format}
            ORDER BY period ASC
            """
            
            return await self.execute_query(query)
            
        except Exception as e:
            logger.error(f"Error getting redemption trends: {e}")
            raise DatabaseError(f"Failed to get redemption trends: {e}")
    
    async def get_campaign_performance(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get campaign performance data."""
        try:
            query = """
            SELECT 
                c.id,
                c.name,
                c.description,
                c.start_date,
                c.end_date,
                COUNT(uc.id) as participant_count,
                COALESCE(SUM(uc.points_earned), 0) as total_points_earned
            FROM campaigns c
            LEFT JOIN user_campaigns uc ON c.id = uc.campaign_id
            WHERE c.is_active = true
            GROUP BY c.id, c.name, c.description, c.start_date, c.end_date
            ORDER BY participant_count DESC
            LIMIT %(limit)s
            """
            
            return await self.execute_query(query, {"limit": limit})
            
        except Exception as e:
            logger.error(f"Error getting campaign performance: {e}")
            raise DatabaseError(f"Failed to get campaign performance: {e}")
    
    async def get_merchant_categories(self) -> List[Dict[str, Any]]:
        """Get merchant categories with statistics."""
        try:
            query = """
            SELECT 
                m.category,
                COUNT(m.id) as merchant_count,
                COUNT(r.id) as redemption_count,
                COALESCE(SUM(r.amount), 0) as total_volume,
                COALESCE(AVG(r.amount), 0) as avg_redemption_value
            FROM merchants m
            LEFT JOIN redemptions r ON m.id = r.merchant_id
            WHERE m.is_active = true AND m.category IS NOT NULL
            GROUP BY m.category
            ORDER BY total_volume DESC
            """
            
            return await self.execute_query(query)
            
        except Exception as e:
            logger.error(f"Error getting merchant categories: {e}")
            raise DatabaseError(f"Failed to get merchant categories: {e}")
    
    async def get_user_tier_distribution(self) -> List[Dict[str, Any]]:
        """Get user tier distribution."""
        try:
            query = """
            SELECT 
                u.tier,
                COUNT(u.id) as user_count,
                COALESCE(SUM(r.amount), 0) as total_spent,
                COALESCE(AVG(r.amount), 0) as avg_spent_per_user
            FROM users u
            LEFT JOIN redemptions r ON u.id = r.user_id
            WHERE u.is_active = true
            GROUP BY u.tier
            ORDER BY 
                CASE u.tier 
                    WHEN 'platinum' THEN 4
                    WHEN 'gold' THEN 3
                    WHEN 'silver' THEN 2
                    WHEN 'bronze' THEN 1
                    ELSE 0
                END DESC
            """
            
            return await self.execute_query(query)
            
        except Exception as e:
            logger.error(f"Error getting user tier distribution: {e}")
            raise DatabaseError(f"Failed to get user tier distribution: {e}")
    
    async def get_recent_redemptions(
        self,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recent redemptions with user and merchant details."""
        try:
            query = """
            SELECT 
                r.id,
                r.amount,
                r.points_used,
                r.redemption_date,
                r.status,
                u.email as user_email,
                u.first_name,
                u.last_name,
                m.name as merchant_name,
                m.category as merchant_category
            FROM redemptions r
            JOIN users u ON r.user_id = u.id
            JOIN merchants m ON r.merchant_id = m.id
            ORDER BY r.redemption_date DESC
            LIMIT %(limit)s
            """
            
            return await self.execute_query(query, {"limit": limit})
            
        except Exception as e:
            logger.error(f"Error getting recent redemptions: {e}")
            raise DatabaseError(f"Failed to get recent redemptions: {e}")
    
    async def test_connection(self) -> bool:
        """Test database connection."""
        try:
            result = await self.execute_query("SELECT 1 as test")
            return len(result) > 0 and result[0].get("test") == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

# Global database operations instance
db_ops = DatabaseOperations()
