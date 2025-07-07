"""Database utilities for Vercel serverless functions with PostgreSQL"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import Optional, Dict, Any, List
import json

logger = logging.getLogger(__name__)

# Global database connection
_connection: Optional[psycopg2.extensions.connection] = None

def get_connection():
    """Get PostgreSQL database connection (synchronous for Vercel)"""
    global _connection
    
    if _connection is None or _connection.closed:
        database_url = os.environ.get('DATABASE_URL', 'postgres://localhost:5432/video_generation_db')
        
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

def close_connection():
    """Close database connection"""
    global _connection
    if _connection and not _connection.closed:
        _connection.close()
        _connection = None
        logger.info("Database connection closed")

# Initialize database tables
def init_database():
    """Initialize database tables if they don't exist"""
    try:
        cursor = get_cursor()
        
        # Create video_projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_projects (
                id UUID PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'uploading',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                progress DECIMAL(5,2) DEFAULT 0.0,
                estimated_time_remaining INTEGER DEFAULT 0,
                download_count INTEGER DEFAULT 0,
                sample_video_path TEXT,
                character_image_path TEXT,
                audio_path TEXT,
                video_analysis JSONB,
                generation_plan JSONB,
                ai_model VARCHAR(100),
                generated_video_path TEXT,
                generated_video_url TEXT,
                generation_job_id VARCHAR(255),
                generation_started_at TIMESTAMP WITH TIME ZONE,
                generation_completed_at TIMESTAMP WITH TIME ZONE,
                error_message TEXT,
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
            ON video_projects(created_at)
        """)
        
        # Create chat_messages table for AI chat history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id UUID NOT NULL REFERENCES video_projects(id) ON DELETE CASCADE,
                user_id VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                response TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB DEFAULT '{}'
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_messages_project_id 
            ON chat_messages(project_id)
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
    def create_project(project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project"""
        cursor = get_cursor()
        try:
            cursor.execute("""
                INSERT INTO video_projects (
                    id, user_id, status, created_at, progress, 
                    estimated_time_remaining, download_count
                ) VALUES (
                    %(id)s, %(user_id)s, %(status)s, %(created_at)s::timestamp,
                    %(progress)s, %(estimated_time_remaining)s, %(download_count)s
                ) RETURNING *
            """, project_data)
            
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
                if key == 'video_analysis' or key == 'generation_plan':
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

# Chat operations
class ChatOperations:
    """Chat database operations"""
    
    @staticmethod
    def save_chat_message(project_id: str, user_id: str, message: str, response: str) -> Dict[str, Any]:
        """Save chat message and response"""
        cursor = get_cursor()
        try:
            cursor.execute("""
                INSERT INTO chat_messages (project_id, user_id, message, response)
                VALUES (%s, %s, %s, %s)
                RETURNING *
            """, (project_id, user_id, message, response))
            
            result = cursor.fetchone()
            cursor.close()
            return dict(result) if result else None
        except Exception as e:
            cursor.close()
            raise e
    
    @staticmethod
    def get_chat_history(project_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history for a project"""
        cursor = get_cursor()
        try:
            cursor.execute("""
                SELECT * FROM chat_messages 
                WHERE project_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (project_id, limit))
            
            results = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in results]
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