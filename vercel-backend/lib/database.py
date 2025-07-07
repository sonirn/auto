"""Database utilities for Vercel serverless functions with PostgreSQL"""
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
    """Get PostgreSQL database connection (synchronous for Vercel)"""
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
            _connection.autocommit = True  # Enable autocommit for serverless
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
                metadata JSONB DEFAULT '{}'
            )
        """)
        
        # Create video_projects table
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
                sample_video_path TEXT,
                character_image_path TEXT,
                audio_path TEXT,
                video_analysis JSONB,
                generation_plan JSONB,
                selected_model VARCHAR(100),
                generated_video_path TEXT,
                generated_video_url TEXT,
                generation_job_id VARCHAR(255),
                generation_started_at TIMESTAMP WITH TIME ZONE,
                generation_completed_at TIMESTAMP WITH TIME ZONE,
                error_message TEXT,
                chat_history JSONB DEFAULT '[]',
                metadata JSONB DEFAULT '{}'
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_video_projects_user_id 
            ON video_projects(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_video_projects_status 
            ON video_projects(status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_video_projects_created_at 
            ON video_projects(created_at DESC)
        """)
        
        cursor.close()
        logger.info("Database tables initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

# Project operations
class ProjectOperations:
    """Project database operations"""
    
    @staticmethod
    def create_project(user_id: str) -> Dict[str, Any]:
        """Create a new project"""
        cursor = get_cursor()
        try:
            project_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO video_projects (id, user_id, status, created_at, progress, estimated_time_remaining, download_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (
                project_id, user_id, 'uploading', datetime.utcnow(), 
                0.0, 0, 0
            ))
            
            result = cursor.fetchone()
            cursor.close()
            return dict(result) if result else None
        except Exception as e:
            cursor.close()
            raise e
    
    @staticmethod
    def get_project(project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID and user ID"""
        cursor = get_cursor()
        try:
            cursor.execute("""
                SELECT * FROM video_projects 
                WHERE id = %s AND user_id = %s
            """, (project_id, user_id))
            
            result = cursor.fetchone()
            cursor.close()
            return dict(result) if result else None
        except Exception as e:
            cursor.close()
            raise e
    
    @staticmethod
    def get_projects_by_user(user_id: str) -> List[Dict[str, Any]]:
        """Get all projects for a user"""
        cursor = get_cursor()
        try:
            cursor.execute("""
                SELECT * FROM video_projects 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """, (user_id,))
            
            results = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in results]
        except Exception as e:
            cursor.close()
            raise e
    
    @staticmethod
    def update_project(project_id: str, update_data: Dict[str, Any]) -> bool:
        """Update project data"""
        cursor = get_cursor()
        try:
            # Build dynamic UPDATE query
            set_clauses = []
            values = []
            
            for key, value in update_data.items():
                if key in ['video_analysis', 'generation_plan', 'chat_history', 'metadata']:
                    set_clauses.append(f"{key} = %s::jsonb")
                    values.append(json.dumps(value))
                else:
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
            
            # Add updated_at
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            values.append(project_id)
            
            query = f"""
                UPDATE video_projects 
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """
            
            cursor.execute(query, values)
            rows_affected = cursor.rowcount
            cursor.close()
            return rows_affected > 0
        except Exception as e:
            cursor.close()
            raise e
    
    @staticmethod
    def delete_project(project_id: str, user_id: str) -> bool:
        """Delete project"""
        cursor = get_cursor()
        try:
            cursor.execute("""
                DELETE FROM video_projects 
                WHERE id = %s AND user_id = %s
            """, (project_id, user_id))
            
            rows_affected = cursor.rowcount
            cursor.close()
            return rows_affected > 0
        except Exception as e:
            cursor.close()
            raise e

# User operations
class UserOperations:
    """User database operations"""
    
    @staticmethod
    def create_user(email: str, user_id: str = None) -> Dict[str, Any]:
        """Create a new user"""
        cursor = get_cursor()
        try:
            if not user_id:
                user_id = str(uuid.uuid4())
                
            cursor.execute("""
                INSERT INTO users (id, email, created_at, last_login, subscription_status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
            """, (user_id, email, datetime.utcnow(), datetime.utcnow(), 'free'))
            
            result = cursor.fetchone()
            cursor.close()
            return dict(result) if result else None
        except Exception as e:
            cursor.close()
            raise e
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        cursor = get_cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return dict(result) if result else None
        except Exception as e:
            cursor.close()
            raise e
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        cursor = get_cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            result = cursor.fetchone()
            cursor.close()
            return dict(result) if result else None
        except Exception as e:
            cursor.close()
            raise e
    
    @staticmethod
    def update_last_login(user_id: str) -> bool:
        """Update user's last login time"""
        cursor = get_cursor()
        try:
            cursor.execute("""
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (user_id,))
            
            rows_affected = cursor.rowcount
            cursor.close()
            return rows_affected > 0
        except Exception as e:
            cursor.close()
            raise e

# Project status constants
PROJECT_STATUS = {
    "UPLOADING": "uploading",
    "ANALYZING": "analyzing", 
    "PLANNING": "planning",
    "GENERATING": "generating",
    "PROCESSING": "processing",
    "COMPLETED": "completed",
    "FAILED": "failed"
}

# Initialize database on import
try:
    init_database()
except Exception as e:
    logger.warning(f"Database initialization failed: {e}")