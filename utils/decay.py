import math
from datetime import datetime, timedelta

def calculate_decay_factor(
    created_at: datetime,
    last_accessed: datetime,
    access_count: int,
    importance: float = 1.0,
    half_life_days: float = 30.0,
    recency_half_life: float = 7.0,
    access_bonus_factor: float = 0.2
) -> float:
    """
    计算记忆的衰减因子
    - 时间衰减: exp(-年龄/半衰期)
    - 访问加成: log(访问次数+1) * 系数
    - 最近访问加成: exp(-距上次访问天数/7) * 0.3
    - 重要性系数直接相乘
    """
    now = datetime.now()
    age_days = (now - created_at).total_seconds() / 86400
    time_decay = math.exp(-age_days / half_life_days)

    access_bonus = math.log(access_count + 1) * access_bonus_factor

    if last_accessed:
        recency_days = (now - last_accessed).total_seconds() / 86400
        recency_bonus = math.exp(-recency_days / recency_half_life) * 0.3
    else:
        recency_bonus = 0

    decay = (time_decay + access_bonus + recency_bonus) * importance
    return min(decay, 2.0)   # 上限 2.0，避免无限膨胀

def update_memory_weights(storage_conn):
    """批量更新 SQLite 中所有情节记忆的 decay_factor"""
    import sqlite3
    cursor = storage_conn.cursor()
    cursor.execute("SELECT id, created_at, last_accessed, access_count, importance FROM episodic_memories")
    rows = cursor.fetchall()

    for row in rows:
        mem_id, created_str, accessed_str, count, imp = row
        created = datetime.fromisoformat(created_str)
        accessed = datetime.fromisoformat(accessed_str) if accessed_str else None
        new_decay = calculate_decay_factor(created, accessed, count, imp)
        cursor.execute(
            "UPDATE episodic_memories SET decay_factor = ? WHERE id = ?",
            (new_decay, mem_id)
        )
    storage_conn.commit()