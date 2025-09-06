#!/usr/bin/env python3
"""
Database initialization script for RewardOps AI Fluency system.

This script:
1. Creates the 'rewardops' database if it doesn't exist
2. Creates the required tables (merchants, users, redemptions)
3. Inserts sample data for testing
4. Sets up proper indexes and constraints
"""

import asyncio
import asyncpg
import logging
from typing import Optional
import random
from datetime import datetime, timedelta

# Import settings from config
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection settings from environment variables
DB_HOST = settings.postgres_host
DB_PORT = settings.postgres_port
DB_USER = settings.postgres_user
DB_PASSWORD = settings.postgres_password
DB_NAME = settings.postgres_database
ADMIN_DB = "postgres"  # Default database to connect to initially

# Sample data
MERCHANT_CATEGORIES = [
    "Electronics", "Clothing", "Food & Beverage", "Home & Garden",
    "Sports & Outdoors", "Beauty & Health", "Books & Media", "Automotive",
    "Travel", "Entertainment", "Fashion", "Technology"
]

SAMPLE_MERCHANTS = [
    ("Amazon", "Electronics"),
    ("Nike", "Sports & Outdoors"),
    ("Starbucks", "Food & Beverage"),
    ("Home Depot", "Home & Garden"),
    ("Sephora", "Beauty & Health"),
    ("Barnes & Noble", "Books & Media"),
    ("Target", "Fashion"),
    ("Best Buy", "Technology"),
    ("Walmart", "Fashion"),
    ("Costco", "Food & Beverage"),
    ("Apple Store", "Technology"),
    ("Macy's", "Fashion"),
    ("REI", "Sports & Outdoors"),
    ("Whole Foods", "Food & Beverage"),
    ("IKEA", "Home & Garden")
]

SAMPLE_NAMES = [
    ("John", "Smith"), ("Emma", "Johnson"), ("Michael", "Williams"),
    ("Sarah", "Brown"), ("David", "Jones"), ("Lisa", "Garcia"),
    ("James", "Miller"), ("Jennifer", "Davis"), ("Robert", "Rodriguez"),
    ("Mary", "Martinez"), ("William", "Hernandez"), ("Linda", "Lopez"),
    ("Richard", "Gonzalez"), ("Barbara", "Wilson"), ("Joseph", "Anderson"),
    ("Elizabeth", "Thomas"), ("Christopher", "Taylor"), ("Jessica", "Moore"),
    ("Daniel", "Jackson"), ("Ashley", "Martin"), ("Matthew", "Lee"),
    ("Amanda", "Perez"), ("Anthony", "Thompson"), ("Stephanie", "White"),
    ("Mark", "Harris"), ("Nicole", "Sanchez"), ("Donald", "Clark"),
    ("Helen", "Ramirez"), ("Steven", "Lewis"), ("Laura", "Robinson")
]


async def create_database():
    """Create the rewardops database if it doesn't exist."""
    try:
        # Connect to default postgres database
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=ADMIN_DB
        )
        
        # Check if database exists
        db_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", DB_NAME
        )
        
        if not db_exists:
            logger.info(f"Creating database '{DB_NAME}'...")
            await conn.execute(f'CREATE DATABASE "{DB_NAME}"')
            logger.info(f"Database '{DB_NAME}' created successfully!")
        else:
            logger.info(f"Database '{DB_NAME}' already exists.")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        return False


async def create_tables():
    """Create the required tables in the rewardops database."""
    try:
        # Connect to rewardops database
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        # Create merchants table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS merchants (
                id SERIAL PRIMARY KEY,
                merchant_name VARCHAR(255) NOT NULL,
                category VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) DEFAULT 'active'
            )
        """)
        
        # Create users table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) DEFAULT 'active'
            )
        """)
        
        # Create redemptions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS redemptions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                merchant_id INTEGER REFERENCES merchants(id),
                amount DECIMAL(10,2) NOT NULL,
                points_used INTEGER NOT NULL,
                redemption_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) DEFAULT 'completed'
            )
        """)
        
        # Create indexes for better performance
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_merchants_category ON merchants(category);
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_redemptions_user_id ON redemptions(user_id);
            CREATE INDEX IF NOT EXISTS idx_redemptions_merchant_id ON redemptions(merchant_id);
            CREATE INDEX IF NOT EXISTS idx_redemptions_date ON redemptions(redemption_date);
        """)
        
        logger.info("Tables created successfully!")
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False


async def insert_sample_data():
    """Insert sample data into the tables."""
    try:
        # Connect to rewardops database
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        # Check if data already exists
        merchant_count = await conn.fetchval("SELECT COUNT(*) FROM merchants")
        if merchant_count > 0:
            logger.info("Sample data already exists. Skipping insertion.")
            await conn.close()
            return True
        
        # Insert merchants
        logger.info("Inserting sample merchants...")
        merchant_ids = []
        for merchant_name, category in SAMPLE_MERCHANTS:
            merchant_id = await conn.fetchval("""
                INSERT INTO merchants (merchant_name, category, status)
                VALUES ($1, $2, 'active')
                RETURNING id
            """, merchant_name, category)
            merchant_ids.append(merchant_id)
        
        # Insert users
        logger.info("Inserting sample users...")
        user_ids = []
        for first_name, last_name in SAMPLE_NAMES:
            email = f"{first_name.lower()}.{last_name.lower()}@example.com"
            user_id = await conn.fetchval("""
                INSERT INTO users (email, first_name, last_name, status)
                VALUES ($1, $2, $3, 'active')
                RETURNING id
            """, email, first_name, last_name)
            user_ids.append(user_id)
        
        # Insert redemptions (200+ sample transactions)
        logger.info("Inserting sample redemptions...")
        redemption_count = 0
        for _ in range(250):  # Create 250 sample redemptions
            user_id = random.choice(user_ids)
            merchant_id = random.choice(merchant_ids)
            
            # Generate realistic amounts and points
            amount = round(random.uniform(10.0, 500.0), 2)
            points_used = int(amount * random.uniform(0.8, 1.2))
            
            # Generate dates within the last 6 months
            days_ago = random.randint(0, 180)
            redemption_date = datetime.now() - timedelta(days=days_ago)
            
            await conn.execute("""
                INSERT INTO redemptions (user_id, merchant_id, amount, points_used, redemption_date, status)
                VALUES ($1, $2, $3, $4, $5, 'completed')
            """, user_id, merchant_id, amount, points_used, redemption_date)
            redemption_count += 1
        
        logger.info(f"Sample data inserted successfully!")
        logger.info(f"  - {len(merchant_ids)} merchants")
        logger.info(f"  - {len(user_ids)} users")
        logger.info(f"  - {redemption_count} redemptions")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to insert sample data: {e}")
        return False


async def verify_database():
    """Verify that the database is properly set up."""
    try:
        # Connect to rewardops database
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        # Check table counts
        merchant_count = await conn.fetchval("SELECT COUNT(*) FROM merchants")
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        redemption_count = await conn.fetchval("SELECT COUNT(*) FROM redemptions")
        
        logger.info("Database verification:")
        logger.info(f"  - Merchants: {merchant_count}")
        logger.info(f"  - Users: {user_count}")
        logger.info(f"  - Redemptions: {redemption_count}")
        
        # Test a sample query
        sample_query = await conn.fetch("""
            SELECT 
                m.merchant_name,
                m.category,
                COUNT(r.id) as redemption_count,
                SUM(r.amount) as total_amount
            FROM merchants m
            LEFT JOIN redemptions r ON m.id = r.merchant_id
            GROUP BY m.id, m.merchant_name, m.category
            ORDER BY total_amount DESC
            LIMIT 5
        """)
        
        logger.info("Sample query test successful!")
        logger.info("Top 5 merchants by redemption amount:")
        for row in sample_query:
            logger.info(f"  - {row['merchant_name']} ({row['category']}): ${row['total_amount'] or 0:.2f}")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return False


async def main():
    """Main initialization function."""
    logger.info("Starting database initialization...")
    
    try:
        # Step 1: Create database
        if not await create_database():
            logger.error("Failed to create database. Exiting.")
            return
        
        # Step 2: Create tables
        if not await create_tables():
            logger.error("Failed to create tables. Exiting.")
            return
        
        # Step 3: Insert sample data
        if not await insert_sample_data():
            logger.error("Failed to insert sample data. Exiting.")
            return
        
        # Step 4: Verify database
        if not await verify_database():
            logger.error("Database verification failed. Exiting.")
            return
        
        logger.info("✅ Database initialization completed successfully!")
        logger.info(f"Database '{DB_NAME}' is ready for use.")
        logger.info("You can now start the backend server with: make start-backend")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
