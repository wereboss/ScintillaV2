import sqlite3
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid
import json
from config.settings import settings
class DatabaseManager:
    """
    Manages all interactions with the SQLite database.
    Handles table creation and CRUD operations.
    Supports both scratchpad and content schemas.
    """
    def __init__(self, db_path: str, schema_name: str = "ideas"):
        self.db_path = db_path
        self.schema_name = schema_name
        self.conn = None
        self.cursor = None

    def _connect(self):
        """Establishes a connection to the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def _disconnect(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()

    def create_tables(self):
        """
        Creates the necessary tables if they do not exist, based on schema_name.
        """
        self._connect()
        try:
            if self.schema_name == "ideas":
                self.cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ideas (
                        id TEXT PRIMARY KEY,
                        idea_text TEXT NOT NULL,
                        context_urls TEXT,
                        status TEXT NOT NULL,
                        timestamp TEXT NOT NULL
                    );
                    """
                )
            elif self.schema_name == "content":
                self.cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS content (
                        id TEXT PRIMARY KEY,
                        idea_id TEXT NOT NULL,
                        project_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        category_tags TEXT,
                        next_actions TEXT,
                        next_reading TEXT,
                        status TEXT NOT NULL,
                        timestamp TEXT NOT NULL
                    );
                    """
                )
            self.conn.commit()
            if settings.is_debug_mode:
                print(f"[{datetime.now().isoformat()}] Tables created successfully in {self.db_path}")
        except sqlite3.Error as e:
            print(f"[{datetime.now().isoformat()}] An error occurred: {e}")
        finally:
            self._disconnect()

    def add_idea(self, idea_text: str, context_urls: str) -> str:
        """Adds a new idea to the scratchpad queue."""
        self._connect()
        idea_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        status = "in queue"
        
        try:
            self.cursor.execute(
                "INSERT INTO ideas (id, idea_text, context_urls, status, timestamp) VALUES (?, ?, ?, ?, ?)",
                (idea_id, idea_text, context_urls, status, timestamp),
            )
            self.conn.commit()
            return idea_id
        except sqlite3.Error as e:
            print(f"[{datetime.now().isoformat()}] An error occurred: {e}")
            return None
        finally:
            self._disconnect()

    def add_content(self, idea_id: str, project_type: str, title: str, content: str, category_tags: List[str], next_actions: Optional[List[Dict]] = [], next_reading: Optional[List[str]] = []) -> str:
        """Adds new processed content to the content database."""
        self._connect()
        content_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        status = "awaiting review"
        
        try:
            # We must serialize the lists to JSON strings before saving to SQLite
            category_tags_str = json.dumps(category_tags)
            next_actions_str = json.dumps(next_actions) if next_actions else json.dumps([])
            next_reading_str = json.dumps(next_reading) if next_reading else json.dumps([])
            
            self.cursor.execute(
                "INSERT INTO content (id, idea_id, project_type, title, content, category_tags, next_actions, next_reading, status, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (content_id, idea_id, project_type, title, content, category_tags_str, next_actions_str, next_reading_str, status, timestamp),
            )
            self.conn.commit()
            return content_id
        except sqlite3.Error as e:
            print(f"[{datetime.now().isoformat()}] An error occurred: {e}")
            return None
        finally:
            self._disconnect()

    def get_all_ideas(self) -> List[Dict]:
        """Retrieves all ideas from the scratchpad, ordered by timestamp (FIFO)."""
        self._connect()
        try:
            self.cursor.execute("SELECT * FROM ideas ORDER BY timestamp ASC")
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[{datetime.now().isoformat()}] An error occurred: {e}")
            return []
        finally:
            self._disconnect()

    def get_pending_ideas(self) -> List[Dict]:
        """Retrieves ideas in the queue that have not been processed."""
        self._connect()
        try:
            self.cursor.execute("SELECT * FROM ideas WHERE status = 'in queue' ORDER BY timestamp ASC")
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[{datetime.now().isoformat()}] An error occurred: {e}")
            return []
        finally:
            self._disconnect()

    def get_idea(self, idea_id: str) -> Optional[Dict]:
        """Retrieves a single idea by its ID."""
        self._connect()
        try:
            self.cursor.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"[{datetime.now().isoformat()}] An error occurred: {e}")
            return None
        finally:
            self._disconnect()

    def update_idea_status(self, idea_id: str, status: str) -> bool:
        """Updates the status of an idea in the scratchpad."""
        self._connect()
        try:
            self.cursor.execute("UPDATE ideas SET status = ? WHERE id = ?", (status, idea_id))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"[{datetime.now().isoformat()}] An error occurred: {e}")
            return False
        finally:
            self._disconnect()

    def delete_idea(self, idea_id: str) -> bool:
        """Deletes an idea from the scratchpad."""
        self._connect()
        try:
            self.cursor.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"[{datetime.now().isoformat()}] An error occurred: {e}")
            return False
        finally:
            self._disconnect()

    def get_all_content(self) -> List[Dict]:
        """Retrieves all processed content from the content database."""
        self._connect()
        try:
            self.cursor.execute("SELECT * FROM content ORDER BY timestamp ASC")
            rows = self.cursor.fetchall()
            
            # Deserialize JSON strings back to lists
            content_list = []
            for row in rows:
                item = dict(row)
                try:
                    item['category_tags'] = json.loads(item['category_tags']) if item['category_tags'] else []
                except (json.JSONDecodeError, TypeError):
                    item['category_tags'] = item['category_tags'].split(',') if item['category_tags'] else []
                
                try:
                    item['next_actions'] = json.loads(item['next_actions'])
                except (json.JSONDecodeError, TypeError):
                    # Fallback for old data: convert simple string list to list of dicts
                    if isinstance(item['next_actions'], str):
                        item['next_actions'] = [{'name': s.strip(), 'priority': 'low'} for s in item['next_actions'].split('\n')]
                    else:
                        item['next_actions'] = []
                
                try:
                    item['next_reading'] = json.loads(item['next_reading'])
                except (json.JSONDecodeError, TypeError):
                    item['next_reading'] = item['next_reading'].split('\n') if item['next_reading'] else []

                content_list.append(item)
            return content_list

        except sqlite3.Error as e:
            print(f"[{datetime.now().isoformat()}] An error occurred: {e}")
            return []
        finally:
            self._disconnect()

    def get_content_by_id(self, content_id: str) -> Optional[Dict]:
        """Retrieves a single processed content item by its ID."""
        self._connect()
        try:
            self.cursor.execute("SELECT * FROM content WHERE id = ?", (content_id,))
            row = self.cursor.fetchone()
            if row:
                item = dict(row)
                # Deserialize JSON strings back to lists
                try:
                    item['category_tags'] = json.loads(item['category_tags'])
                except (json.JSONDecodeError, TypeError):
                    item['category_tags'] = item['category_tags'].split(',') if item['category_tags'] else []
                
                try:
                    item['next_actions'] = json.loads(item['next_actions'])
                except (json.JSONDecodeError, TypeError):
                    # Fallback for old data: convert simple string list to list of dicts
                    if isinstance(item['next_actions'], str):
                        item['next_actions'] = [{'name': s.strip(), 'priority': 'low'} for s in item['next_actions'].split('\n')]
                    else:
                        item['next_actions'] = []
                
                try:
                    item['next_reading'] = json.loads(item['next_reading'])
                except (json.JSONDecodeError, TypeError):
                    item['next_reading'] = item['next_reading'].split('\n') if item['next_reading'] else []
                
                return item
            return None
        except sqlite3.Error as e:
            print(f"[{datetime.now().isoformat()}] An error occurred: {e}")
            return None
        finally:
            self._disconnect()

    def delete_content(self, content_id: str) -> bool:
        """D eletes a content item from the content database."""
        self._connect()
        try:
            self.cursor.execute("DELETE FROM content WHERE id = ?", (content_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"[{datetime.now().isoformat()}] An error occurred: {e}")
            return False
        finally:
            self._disconnect()
