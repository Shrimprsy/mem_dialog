import os
import sqlite3
import json
import uuid
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Any
import chromadb
from config_memory import SQLITE_DB_PATH, CHROMA_PERSIST_PATH

class MemoryStorage:
    def __init__(self):
        # 确保目录存在
        os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
        os.makedirs(CHROMA_PERSIST_PATH, exist_ok=True)

        self.conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        self._init_sqlite_tables()

        self.chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)
        self.episodic_collection = self.chroma_client.get_or_create_collection(
            name="episodic_memories",
            metadata={"hnsw:space": "cosine"}
        )

    def _init_sqlite_tables(self):
        cursor = self.conn.cursor()

        # 用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 情节记忆表 (L2)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS episodic_memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT,
                created_at TIMESTAMP,
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                importance REAL DEFAULT 1.0,
                decay_factor REAL DEFAULT 1.0,
                metadata_json TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        # 语义记忆表 (L3)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS semantic_memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                source_ids TEXT,
                metadata_json TEXT,
                UNIQUE(user_id, memory_type, key),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        # 标签索引表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_tags (
                memory_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                tag_type TEXT NOT NULL,
                tag_value TEXT NOT NULL,
                PRIMARY KEY (memory_id, tag_type, tag_value),
                FOREIGN KEY(memory_id) REFERENCES episodic_memories(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        # 工作记忆表 (L1)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS working_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        # 用户状态表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_state (
                user_id TEXT PRIMARY KEY,
                compressed_rounds INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        self.conn.commit()

    # ========== 用户管理 ==========
    def create_user(self, username: str, password: str) -> Optional[str]:
        user_id = str(uuid.uuid4())
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
                (user_id, username, password_hash)
            )
            self.conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        cursor = self.conn.cursor()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute(
            "SELECT id FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        row = cursor.fetchone()
        return row[0] if row else None

    # ========== 工作记忆 ==========
    def save_working_memory(self, user_id: str, messages: List[Dict]):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM working_memory WHERE user_id = ?", (user_id,))
        for msg in messages:
            cursor.execute(
                "INSERT INTO working_memory (user_id, role, content) VALUES (?, ?, ?)",
                (user_id, msg["role"], msg["content"])
            )
        self.conn.commit()

    def load_working_memory(self, user_id: str) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT role, content FROM working_memory WHERE user_id = ? ORDER BY id ASC",
            (user_id,)
        )
        rows = cursor.fetchall()
        return [{"role": row[0], "content": row[1]} for row in rows]

    # ========== 情节记忆 ==========
    def add_episodic(self, user_id: str, mem_id: str, content: str, summary: str,
                     embedding: List[float], metadata: Dict) -> bool:
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO episodic_memories
            (id, user_id, content, summary, created_at, last_accessed, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (mem_id, user_id, content, summary, now, now, json.dumps(metadata)))

        if "tags" in metadata:
            for tag_type, tag_value in metadata["tags"].items():
                if isinstance(tag_value, list):
                    for v in tag_value:
                        cursor.execute(
                            "INSERT OR IGNORE INTO memory_tags VALUES (?, ?, ?, ?)",
                            (mem_id, user_id, tag_type, v)
                        )
                else:
                    cursor.execute(
                        "INSERT OR IGNORE INTO memory_tags VALUES (?, ?, ?, ?)",
                        (mem_id, user_id, tag_type, tag_value)
                    )
        self.conn.commit()

        self.episodic_collection.add(
            ids=[mem_id],
            embeddings=[embedding],
            metadatas=[{
                "user_id": user_id,
                "summary": summary,
                "created_at": now,
                "importance": metadata.get("importance", 1.0)
            }],
            documents=[content]
        )
        return True

    def get_episodic_by_id(self, user_id: str, mem_id: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, content, summary, created_at, last_accessed, access_count, importance, decay_factor, metadata_json FROM episodic_memories WHERE id = ? AND user_id = ?",
            (mem_id, user_id)
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0], "content": row[1], "summary": row[2],
                "created_at": row[3], "last_accessed": row[4],
                "access_count": row[5], "importance": row[6],
                "decay_factor": row[7], "metadata": json.loads(row[8])
            }
        return None

    def get_candidates_by_tags(self, user_id: str, filter_tags: Dict[str, str]) -> List[str]:
        if not filter_tags:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT id FROM episodic_memories WHERE user_id = ?", (user_id,))
            return [row[0] for row in cursor.fetchall()]

        conditions = ["user_id = ?"]
        params = [user_id]
        for tag_type, tag_value in filter_tags.items():
            conditions.append("(tag_type = ? AND tag_value = ?)")
            params.extend([tag_type, tag_value])

        query = f"""
            SELECT memory_id FROM memory_tags
            WHERE {' OR '.join(conditions)}
            GROUP BY memory_id
            HAVING COUNT(DISTINCT tag_type) = ?
        """
        params.append(len(filter_tags))
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return [row[0] for row in cursor.fetchall()]

    def update_access_stats(self, user_id: str, mem_ids: List[str]):
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        for mid in mem_ids:
            cursor.execute(
                "UPDATE episodic_memories SET last_accessed = ?, access_count = access_count + 1 WHERE id = ? AND user_id = ?",
                (now, mid, user_id)
            )
        self.conn.commit()

    # ========== 语义记忆 ==========
    def upsert_semantic(self, user_id: str, mem_type: str, key: str, value: str,
                        confidence: float = 1.0, source_id: str = None) -> str:
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            "SELECT id, confidence, source_ids FROM semantic_memories WHERE user_id = ? AND key = ? AND memory_type = ?",
            (user_id, key, mem_type)
        )
        row = cursor.fetchone()

        if row:
            mem_id, old_conf, old_sources = row
            new_conf = (old_conf + confidence) / 2
            sources = set(old_sources.split(',')) if old_sources else set()
            if source_id:
                sources.add(source_id)
            new_sources = ','.join(sources)

            cursor.execute("""
                UPDATE semantic_memories
                SET confidence = ?, updated_at = ?, source_ids = ?
                WHERE id = ?
            """, (new_conf, now, new_sources, mem_id))
        else:
            mem_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO semantic_memories
                (id, user_id, memory_type, key, value, confidence, created_at, updated_at, source_ids)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (mem_id, user_id, mem_type, key, value, confidence, now, now, source_id or ""))

        self.conn.commit()
        return mem_id

    def get_all_semantic(self, user_id: str) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT memory_type, key, value, confidence FROM semantic_memories WHERE user_id = ? ORDER BY memory_type, key",
            (user_id,)
        )
        rows = cursor.fetchall()
        return [{"type": r[0], "key": r[1], "value": r[2], "confidence": r[3]} for r in rows]

    # ========== 用户状态 ==========
    def get_compressed_rounds(self, user_id: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT compressed_rounds FROM user_state WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else 0

    def set_compressed_rounds(self, user_id: str, rounds: int):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO user_state (user_id, compressed_rounds, updated_at) VALUES (?, ?, ?)",
            (user_id, rounds, datetime.now().isoformat())
        )
        self.conn.commit()

    def close(self):
        self.conn.close()