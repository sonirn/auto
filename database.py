"""Database utilities with PostgreSQL for Vercel deployment"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import Optional, Dict, Any, List
import json
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Global database connection
_connection: Optional[psycopg2.extensions.connection] = None

def get_connection():
    """Get PostgreSQL database connection"""
    global _connection
    
    if _connection is None or _connection.closed:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise Exception("DATABASE_URL environment variable not set")
        
        try:
            _connection = psycopg2.connect(
                database_url,
                cursor_factory=RealDictCursor
            )
            _connection.autocommit = True
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    return _connection

def get_cursor():
    """Get database cursor"""
    conn = get_connection()
    return conn.cursor()

# Initialize database tables
def init_database():
    """Initialize database tables if they don't exist"""
    try:
        cursor = get_cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                subscription_status VARCHAR(50) DEFAULT 'free',
                projects JSONB DEFAULT '[]',
                metadata JSONB DEFAULT '{}'
            )
        """)
        
        # Create video_projects table with comprehensive schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_projects (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                status VARCHAR(50) NOT NULL DEFAULT 'uploading',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP + INTERVAL '7 days',
                progress DECIMAL(5,2) DEFAULT 0.0,
                estimated_time_remaining INTEGER DEFAULT 0,
                download_count INTEGER DEFAULT 0,
                
                -- File paths
                sample_video_path TEXT,
                character_image_path TEXT,
                audio_path TEXT,
                generated_video_path TEXT,
                generated_video_url TEXT,
                
                -- AI Analysis and Plans
                video_analysis JSONB,
                generation_plan JSONB,
                chat_history JSONB DEFAULT '[]',
                
                -- Generation info
                selected_model VARCHAR(100),
                generation_job_id VARCHAR(255),
                generation_started_at TIMESTAMP WITH TIME ZONE,
                generation_completed_at TIMESTAMP WITH TIME ZONE,
                
                -- Error handling
                error_message TEXT,
                metadata JSONB DEFAULT '{}'
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_projects_user_id ON video_projects(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_projects_status ON video_projects(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_projects_created_at ON video_projects(created_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        
        cursor.close()
        logger.info("Database tables initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

# MongoDB-like interface for compatibility with existing code
class MongoCollection:
    """PostgreSQL collection that mimics MongoDB interface"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
    
    def insert_one(self, document: dict):
        """Insert a document"""
        cursor = get_cursor()
        try:
            if self.table_name == 'video_projects':
                # Handle video projects
                doc_id = document.get('id', str(uuid.uuid4()))
                cursor.execute("""
                    INSERT INTO video_projects (
                        id, user_id, status, created_at, progress, estimated_time_remaining,
                        download_count, sample_video_path, character_image_path, audio_path,
                        video_analysis, generation_plan, selected_model, expires_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
                """, (
                    doc_id, document.get('user_id'), document.get('status', 'uploading'),
                    document.get('created_at', datetime.utcnow()), document.get('progress', 0.0),
                    document.get('estimated_time_remaining', 0), document.get('download_count', 0),
                    document.get('sample_video_path'), document.get('character_image_path'),
                    document.get('audio_path'), 
                    json.dumps(document.get('video_analysis')) if document.get('video_analysis') else None,
                    json.dumps(document.get('generation_plan')) if document.get('generation_plan') else None,
                    document.get('selected_model'),
                    document.get('expires_at', datetime.utcnow())
                ))
            elif self.table_name == 'users':
                # Handle users
                doc_id = document.get('id', str(uuid.uuid4()))
                cursor.execute("""
                    INSERT INTO users (id, email, created_at, last_login, subscription_status, projects)
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                """, (
                    doc_id, document.get('email'), document.get('created_at', datetime.utcnow()),
                    document.get('last_login', datetime.utcnow()), 
                    document.get('subscription_status', 'free'),
                    json.dumps(document.get('projects', []))
                ))
            cursor.close()
        except Exception as e:
            cursor.close()
            raise e
    
    def find_one(self, query: dict):
        """Find one document"""
        cursor = get_cursor()
        try:
            if self.table_name == 'video_projects':
                if 'id' in query and 'user_id' in query:
                    cursor.execute("SELECT * FROM video_projects WHERE id = %s AND user_id = %s", 
                                 (query['id'], query['user_id']))
                elif 'id' in query:
                    cursor.execute("SELECT * FROM video_projects WHERE id = %s", (query['id'],))
                else:
                    cursor.execute("SELECT * FROM video_projects WHERE user_id = %s LIMIT 1", 
                                 (query.get('user_id'),))
            elif self.table_name == 'users':
                if 'id' in query:
                    cursor.execute("SELECT * FROM users WHERE id = %s", (query['id'],))
                elif 'email' in query:
                    cursor.execute("SELECT * FROM users WHERE email = %s", (query['email'],))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                # Convert back to dict and handle UUIDs
                doc = dict(result)
                doc['_id'] = str(doc['id'])  # MongoDB compatibility
                if doc.get('id'):
                    doc['id'] = str(doc['id'])
                if doc.get('user_id'):
                    doc['user_id'] = str(doc['user_id'])
                return doc
            return None
        except Exception as e:
            cursor.close()
            raise e
    
    def find(self, query: dict):
        """Find multiple documents"""
        cursor = get_cursor()
        try:
            if self.table_name == 'video_projects':
                cursor.execute("SELECT * FROM video_projects WHERE user_id = %s ORDER BY created_at DESC", 
                             (query.get('user_id'),))
            elif self.table_name == 'users':
                cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            
            results = cursor.fetchall()
            cursor.close()
            
            # Convert results
            docs = []
            for result in results:
                doc = dict(result)
                doc['_id'] = str(doc['id'])  # MongoDB compatibility
                if doc.get('id'):
                    doc['id'] = str(doc['id'])
                if doc.get('user_id'):
                    doc['user_id'] = str(doc['user_id'])
                docs.append(doc)
            
            return MockAsyncList(docs)
        except Exception as e:
            cursor.close()
            raise e
    
    def update_one(self, query: dict, update: dict):
        """Update one document"""
        cursor = get_cursor()
        try:
            set_data = update.get('$set', {})
            inc_data = update.get('$inc', {})
            
            # Build update query
            set_clauses = []
            values = []
            
            for key, value in set_data.items():
                if key in ['video_analysis', 'generation_plan', 'chat_history', 'metadata', 'projects']:
                    set_clauses.append(f"{key} = %s::jsonb")
                    values.append(json.dumps(value))
                else:
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
            
            for key, value in inc_data.items():
                set_clauses.append(f"{key} = {key} + %s")
                values.append(value)
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            
            if self.table_name == 'video_projects':
                if 'id' in query and 'user_id' in query:
                    values.extend([query['id'], query['user_id']])
                    where_clause = "id = %s AND user_id = %s"
                elif 'id' in query:
                    values.append(query['id'])
                    where_clause = "id = %s"
                else:
                    values.append(query.get('_id'))
                    where_clause = "id = %s"
            elif self.table_name == 'users':
                values.append(query.get('id'))
                where_clause = "id = %s"
            
            query_sql = f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE {where_clause}"
            cursor.execute(query_sql, values)
            
            cursor.close()
            return MockUpdateResult(cursor.rowcount)
        except Exception as e:
            cursor.close()
            raise e
    
    def delete_one(self, query: dict):
        """Delete one document"""
        cursor = get_cursor()
        try:
            if self.table_name == 'video_projects':
                cursor.execute("DELETE FROM video_projects WHERE id = %s AND user_id = %s", 
                             (query.get('id'), query.get('user_id')))
            elif self.table_name == 'users':
                cursor.execute("DELETE FROM users WHERE id = %s", (query.get('id'),))
            
            cursor.close()
            return MockDeleteResult(cursor.rowcount)
        except Exception as e:
            cursor.close()
            raise e

class MockAsyncList:
    """Mock async list for MongoDB compatibility"""
    def __init__(self, items):
        self.items = items
    
    async def to_list(self, length):
        return self.items

class MockUpdateResult:
    """Mock update result for MongoDB compatibility"""
    def __init__(self, count):
        self.matched_count = count
        self.modified_count = count

class MockDeleteResult:
    """Mock delete result for MongoDB compatibility"""
    def __init__(self, count):
        self.deleted_count = count

class MockDatabase:
    """Mock database for MongoDB compatibility"""
    def __getitem__(self, collection_name):
        return MongoCollection(collection_name)
    
    @property
    def video_projects(self):
        return MongoCollection('video_projects')
    
    @property
    def users(self):
        return MongoCollection('users')

# Initialize database and create mock client for compatibility
# Note: Database initialization is now handled in server.py startup event
# try:
#     init_database()
# except Exception as e:
#     logger.warning(f"Database initialization failed: {e}")

# Create mock MongoDB-compatible interface
db = MockDatabase()