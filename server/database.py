  1→"""
  2→NovaSSO - 数据库层
  3→SQLite + WAL模式，支持高并发读写
  4→"""
  5→import sqlite3
  6→import threading
  7→import os
  8→from contextlib import contextmanager
  9→from pathlib import Path
 10→
 11→from config import DB_PATH, DEBUG
 12→
 13→_local = threading.local()
 14→
 15→def get_db():
 16→    """获取线程本地数据库连接"""
 17→    if not hasattr(_local, 'conn'):
 18→        # 确保目录存在
 19→        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
 20→        
 21→        _local.conn = sqlite3.connect(
 22→            DB_PATH,
 23→            check_same_thread=False,
 24→            timeout=30
 25→        )
 26→        _local.conn.row_factory = sqlite3.Row
 27→        # WAL模式：读写并发优化
 28→        _local.conn.execute("PRAGMA journal_mode=WAL")
 29→        _local.conn.execute("PRAGMA synchronous=NORMAL")
 30→        _local.conn.execute("PRAGMA busy_timeout=5000")
 31→        _local.conn.execute("PRAGMA foreign_keys=ON")
 32→    return _local.conn
 33→
 34→@contextmanager
 35→def db_cursor():
 36→    """安全的数据库游标上下文管理器"""
 37→    conn = get_db()
 38→    cursor = conn.cursor()
 39→    try:
 40→        yield cursor
 41→        conn.commit()
 42→    except Exception:
 43→        conn.rollback()
 44→        raise
 45→    finally:
 46→        cursor.close()
 47→
 48→def init_db():
 49→    """初始化数据库表结构"""
 50→    with db_cursor() as cur:
 51→        # 用户表
 52→        cur.execute("""
 53→            CREATE TABLE IF NOT EXISTS users (
 54→                id INTEGER PRIMARY KEY AUTOINCREMENT,
 55→                username VARCHAR(64) UNIQUE NOT NULL,
 56→                email VARCHAR(128) UNIQUE,
 57→                password_hash VARCHAR(255) NOT NULL,
 58→                nickname VARCHAR(64),
 59→                avatar VARCHAR(255),
 60→                is_active BOOLEAN DEFAULT 1,
 61→                is_admin BOOLEAN DEFAULT 0,
 62→                email_verified BOOLEAN DEFAULT 0,
 63→                mfa_enabled BOOLEAN DEFAULT 0,
 64→                mfa_secret VARCHAR(64),
 65→                last_login_at TIMESTAMP,
 66→                last_login_ip VARCHAR(64),
 67→                failed_attempts INTEGER DEFAULT 0,
 68→                locked_until TIMESTAMP,
 69→                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 70→                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
 71→            )
 72→        """)
 73→
 74→        # 应用表
 75→        cur.execute("""
 76→            CREATE TABLE IF NOT EXISTS apps (
 77→                id INTEGER PRIMARY KEY AUTOINCREMENT,
 78→                app_id VARCHAR(64) UNIQUE NOT NULL,
 79→                app_name VARCHAR(128) NOT NULL,
 80→                app_description TEXT,
 81→                app_icon VARCHAR(255),
 82→                callback_url VARCHAR(512) NOT NULL,
 83→                logout_url VARCHAR(512),
 84→                app_secret VARCHAR(128) NOT NULL,
 85→                is_active BOOLEAN DEFAULT 1,
 86→                created_by INTEGER,
 87→                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 88→                FOREIGN KEY (created_by) REFERENCES users(id)
 89→            )
 90→        """)
 91→
 92→        # TGT全局会话表
 93→        cur.execute("""
 94→            CREATE TABLE IF NOT EXISTS tgt_sessions (
 95→                tgt_id VARCHAR(128) PRIMARY KEY,
 96→                user_id INTEGER NOT NULL,
 97→                username VARCHAR(64) NOT NULL,
 98→                ip VARCHAR(64),
 99→                user_agent VARCHAR(512),
                device_info TEXT,
                node_id VARCHAR(64),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tgt_user ON tgt_sessions(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tgt_expires ON tgt_sessions(expires_at)")

        # ST服务票据表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS service_tickets (
                st_id VARCHAR(128) PRIMARY KEY,
                tgt_id VARCHAR(128) NOT NULL,
                user_id INTEGER NOT NULL,
                app_id VARCHAR(64) NOT NULL,
                service VARCHAR(512) NOT NULL,
                used BOOLEAN DEFAULT 0,
                used_at TIMESTAMP,
                node_id VARCHAR(64),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_st_expires ON service_tickets(expires_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_st_tgt ON service_tickets(tgt_id)")

        # 审计日志表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username VARCHAR(64),
                action VARCHAR(64) NOT NULL,
                target VARCHAR(128),
                ip VARCHAR(64),
                user_agent VARCHAR(512),
                success BOOLEAN DEFAULT 1,
                detail TEXT,
                node_id VARCHAR(64),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(created_at)")

        # 多中心节点表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cluster_nodes (
                node_id VARCHAR(64) PRIMARY KEY,
                node_name VARCHAR(128),
                node_url VARCHAR(512),
                node_role VARCHAR(16) DEFAULT 'peer',
                status VARCHAR(16) DEFAULT 'online',
                last_heartbeat TIMESTAMP,
                last_sync_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 数据同步记录表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sync_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_type VARCHAR(32) NOT NULL,
                record_id VARCHAR(128) NOT NULL,
                operation VARCHAR(16) NOT NULL,
                node_id VARCHAR(64),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sync_type ON sync_records(sync_type, created_at)")

    if DEBUG:
        print("[NovaSSO] 数据库初始化完成")