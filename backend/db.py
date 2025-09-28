# backend/db.py
import sqlite3
import json
import re
from pathlib import Path

DB_PATH = Path("conversations.db")

def generate_conversation_title(first_message: str) -> str:
    """Generate a meaningful title from the first user message"""
    # Clean up the message
    message = first_message.strip()
    
    # Remove common prefixes
    prefixes_to_remove = [
        r'^(hi|hello|hey|bonjour|salut)\s*,?\s*',
        r'^(can you|could you|please|peux-tu|pourrais-tu)\s+',
        r'^(i need|i want|je veux|j\'ai besoin)\s+',
        r'^(help me|aide-moi|m\'aider)\s+',
    ]
    
    for prefix in prefixes_to_remove:
        message = re.sub(prefix, '', message, flags=re.IGNORECASE)
    
    # Truncate if too long
    if len(message) > 50:
        message = message[:47] + "..."
    
    # Capitalize first letter
    if message:
        message = message[0].upper() + message[1:]
    
    # Fallback if message is too short or empty
    if len(message.strip()) < 3:
        return "New Conversation"
    
    return message.strip()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Check if table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'")
    table_exists = cur.fetchone() is not None
    
    if not table_exists:
        # Create new table with all columns
        cur.execute("""
        CREATE TABLE conversations (
            id TEXT,
            user_id TEXT,
            title TEXT,
            messages TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id, user_id)
        )
        """)
    else:
        # Check which columns exist
        cur.execute("PRAGMA table_info(conversations)")
        existing_columns = [col[1] for col in cur.fetchall()]
        
        # Add missing columns
        if 'title' not in existing_columns:
            try:
                cur.execute("ALTER TABLE conversations ADD COLUMN title TEXT")
                print("Added title column")
            except sqlite3.OperationalError as e:
                print(f"Error adding title column: {e}")
        
        if 'created_at' not in existing_columns:
            try:
                cur.execute("ALTER TABLE conversations ADD COLUMN created_at TIMESTAMP")
                print("Added created_at column")
            except sqlite3.OperationalError as e:
                print(f"Error adding created_at column: {e}")
            
        if 'updated_at' not in existing_columns:
            try:
                cur.execute("ALTER TABLE conversations ADD COLUMN updated_at TIMESTAMP")
                print("Added updated_at column")
            except sqlite3.OperationalError as e:
                print(f"Error adding updated_at column: {e}")
    
    # Update existing records with timestamps if they don't have them
    cur.execute("SELECT id, user_id FROM conversations WHERE created_at IS NULL OR updated_at IS NULL")
    records_to_update = cur.fetchall()
    
    if records_to_update:
        from datetime import datetime
        current_time = datetime.now().isoformat()
        for conv_id, user_id in records_to_update:
            cur.execute("""
            UPDATE conversations 
            SET created_at = ?, updated_at = ? 
            WHERE id = ? AND user_id = ?
            """, (current_time, current_time, conv_id, user_id))
        print(f"Updated {len(records_to_update)} existing records with timestamps")
    
    conn.commit()
    conn.close()

def save_conversation(user_id: str, conv_id: str, messages: list[dict], title: str = None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Generate title from first user message if not provided
    if not title and messages:
        first_user_msg = next((msg for msg in messages if msg.get("role") == "user"), None)
        if first_user_msg:
            title = generate_conversation_title(first_user_msg["content"])
    
    # Check which columns exist
    cur.execute("PRAGMA table_info(conversations)")
    existing_columns = [col[1] for col in cur.fetchall()]
    
    # Build query based on available columns
    if 'title' in existing_columns and 'updated_at' in existing_columns:
        from datetime import datetime
        current_time = datetime.now().isoformat()
        cur.execute("""
        INSERT INTO conversations (id, user_id, title, messages, updated_at) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id, user_id) DO UPDATE SET 
            messages=excluded.messages,
            title=COALESCE(excluded.title, conversations.title),
            updated_at=excluded.updated_at
        """, (conv_id, user_id, title, json.dumps(messages), current_time))
    elif 'title' in existing_columns:
        cur.execute("""
        INSERT INTO conversations (id, user_id, title, messages) VALUES (?, ?, ?, ?)
        ON CONFLICT(id, user_id) DO UPDATE SET 
            messages=excluded.messages,
            title=COALESCE(excluded.title, conversations.title)
        """, (conv_id, user_id, title, json.dumps(messages)))
    else:
        # Fallback for old database structure
        cur.execute("""
        INSERT INTO conversations (id, user_id, messages) VALUES (?, ?, ?)
        ON CONFLICT(id, user_id) DO UPDATE SET messages=excluded.messages
        """, (conv_id, user_id, json.dumps(messages)))
    
    conn.commit()
    conn.close()

def load_conversation(user_id: str, conv_id: str) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT messages FROM conversations WHERE id=? AND user_id=?", (conv_id, user_id))
    row = cur.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return []

def list_conversations(user_id: str) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Check which columns exist
    cur.execute("PRAGMA table_info(conversations)")
    columns = [col[1] for col in cur.fetchall()]
    
    # Build query based on available columns
    if 'title' in columns and 'created_at' in columns and 'updated_at' in columns:
        query = """
        SELECT id, title, messages, created_at, updated_at 
        FROM conversations 
        WHERE user_id=? 
        ORDER BY updated_at DESC
        """
        cur.execute(query, (user_id,))
        rows = cur.fetchall()
        
        conversations = []
        for row in rows:
            conv_id, title, messages_json, created_at, updated_at = row
            messages = json.loads(messages_json) if messages_json else []
            
            # Generate title if missing
            if not title and messages:
                first_user_msg = next((msg for msg in messages if msg.get("role") == "user"), None)
                if first_user_msg:
                    title = generate_conversation_title(first_user_msg["content"])
            
            conversations.append({
                "id": conv_id,
                "title": title or "New Conversation",
                "messages": messages,
                "created_at": created_at,
                "updated_at": updated_at,
                "message_count": len(messages)
            })
    else:
        # Fallback for old database structure
        cur.execute("SELECT id, messages FROM conversations WHERE user_id=?", (user_id,))
        rows = cur.fetchall()
        
        conversations = []
        for row in rows:
            conv_id, messages_json = row
            messages = json.loads(messages_json) if messages_json else []
            
            # Generate title from first message
            title = "New Conversation"
            if messages:
                first_user_msg = next((msg for msg in messages if msg.get("role") == "user"), None)
                if first_user_msg:
                    title = generate_conversation_title(first_user_msg["content"])
            
            conversations.append({
                "id": conv_id,
                "title": title,
                "messages": messages,
                "created_at": None,
                "updated_at": None,
                "message_count": len(messages)
            })
    
    conn.close()
    return conversations
