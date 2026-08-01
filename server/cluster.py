  1→"""
  2→NovaSSO - 多中心集群同步模块
  3→支持多节点部署，数据自动同步
  4→"""
  5→import threading
  6→import time
  7→import json
  8→import requests
  9→from typing import List, Dict, Optional
 10→from datetime import datetime
 11→
 12→from config import (
 13→    NODE_ID, NODE_NAME, NODE_ROLE, PEER_NODES,
 14→    SYNC_INTERVAL, SYNC_API_KEY
 15→)
 16→from database import db_cursor
 17→import auth
 18→
 19→
 20→class ClusterManager:
 21→    """集群管理器 - 多中心架构核心"""
 22→
 23→    def __init__(self):
 24→        self.running = False
 25→        self.sync_thread = None
 26→        self.heartbeat_thread = None
 27→        self.last_sync_id = 0
 28→        self.node_status = {}  # 节点状态缓存
 29→
 30→    def start(self):
 31→        """启动集群同步"""
 32→        if not PEER_NODES:
 33→            print(f"[NovaSSO] 单节点模式运行（未配置对等节点）")
 34→            self._register_self()
 35→            return
 36→
 37→        self.running = True
 38→        self._register_self()
 39→
 40→        # 启动同步线程
 41→        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
 42→        self.sync_thread.start()
 43→
 44→        # 启用心跳线程
 45→        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
 46→        self.heartbeat_thread.start()
 47→
 48→        print(f"[NovaSSO] 多中心模式启动，当前节点: {NODE_ID} ({NODE_ROLE})")
 49→        print(f"[NovaSSO] 对等节点: {len(PEER_NODES)} 个")
 50→
 51→    def stop(self):
 52→        """停止集群同步"""
 53→        self.running = False
 54→
 55→    def _register_self(self):
 56→        """注册本节点到集群"""
 57→        with db_cursor() as cur:
 58→            cur.execute("""
 59→                INSERT OR REPLACE INTO cluster_nodes
 60→                (node_id, node_name, node_role, status, last_heartbeat)
 61→                VALUES (?, ?, ?, 'online', ?)
 62→            """, (NODE_ID, NODE_NAME, NODE_ROLE, datetime.now()))
 63→
 64→    def _heartbeat_loop(self):
 65→        """心跳循环"""
 66→        while self.running:
 67→            try:
 68→                # 更新自己的心跳
 69→                with db_cursor() as cur:
 70→                    cur.execute("""
 71→                        UPDATE cluster_nodes SET last_heartbeat = ?, status = 'online'
 72→                        WHERE node_id = ?
 73→                    """, (datetime.now(), NODE_ID))
 74→
 75→                # 检测其他节点状态
 76→                self._check_peer_status()
 77→
 78→            except Exception as e:
 79→                print(f"[NovaSSO] 心跳异常: {e}")
 80→
 81→            time.sleep(10)  # 每10秒心跳一次
 82→
 83→    def _sync_loop(self):
 84→        """数据同步循环"""
 85→        while self.running:
 86→            try:
 87→                self._sync_from_peers()
 88→            except Exception as e:
 89→                print(f"[NovaSSO] 同步异常: {e}")
 90→
 91→            time.sleep(SYNC_INTERVAL)
 92→
 93→    def _sync_from_peers(self):
 94→        """从对等节点拉取数据"""
 95→        for peer_url in PEER_NODES:
 96→            if not peer_url:
 97→                continue
 98→            try:
 99→                # 获取对等节点的同步记录
                response = requests.get(
                    f"{peer_url.rstrip('/')}/api/cluster/sync/pull",
                    headers={"X-Sync-Key": SYNC_API_KEY},
                    params={"since_id": self.last_sync_id},
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    records = data.get("records", [])
                    if records:
                        self._apply_sync_records(records)
                        self.last_sync_id = max(
                            self.last_sync_id,
                            data.get("max_id", 0)
                        )
            except requests.RequestException:
                pass  # 网络问题，跳过这个节点

    def _apply_sync_records(self, records: List[Dict]):
        """应用同步记录"""
        for record in records:
            try:
                sync_type = record["sync_type"]
                record_id = record["record_id"]
                operation = record["operation"]

                if sync_type == "user" and operation == "create":
                    # 用户创建同步（需要完整数据）
                    pass  # 需要扩展：拉取完整用户数据
                elif sync_type == "tgt":
                    if operation == "delete":
                        # TGT删除同步（强制下线）
                        auth.delete_tgt(record_id)

            except Exception as e:
                print(f"[NovaSSO] 应用同步记录失败: {e}")

    def _check_peer_status(self):
        """检测对等节点状态"""
        # 标记超过60秒没心跳的节点为offline
        with db_cursor() as cur:
            cur.execute("""
                UPDATE cluster_nodes
                SET status = 'offline'
                WHERE last_heartbeat < datetime('now', '-60 seconds')
                  AND node_id != ?
            """, (NODE_ID,))

    def get_cluster_status(self) -> Dict:
        """获取集群状态"""
        with db_cursor() as cur:
            cur.execute("SELECT * FROM cluster_nodes ORDER BY node_id")
            nodes = [dict(row) for row in cur.fetchall()]

        online_count = sum(1 for n in nodes if n['status'] == 'online')

        return {
            "current_node": NODE_ID,
            "current_role": NODE_ROLE,
            "total_nodes": len(nodes),
            "online_nodes": online_count,
            "nodes": nodes,
            "multi_center": len(PEER_NODES) > 0
        }

    def push_to_peers(self, sync_type: str, record_id: str, operation: str):
        """主动推送变更到对等节点"""
        if not PEER_NODES:
            return

        def _push():
            for peer_url in PEER_NODES:
                if not peer_url:
                    continue
                try:
                    requests.post(
                        f"{peer_url.rstrip('/')}/api/cluster/sync/push",
                        headers={"X-Sync-Key": SYNC_API_KEY},
                        json={
                            "sync_type": sync_type,
                            "record_id": record_id,
                            "operation": operation,
                            "source_node": NODE_ID
                        },
                        timeout=3
                    )
                except requests.RequestException:
                    pass

        # 异步推送，不阻塞主流程
        threading.Thread(target=_push, daemon=True).start()


# 全局集群管理器实例
cluster = ClusterManager()


def init_cluster():
    """初始化集群"""
    cluster.start()


def get_cluster() -> ClusterManager:
    """获取集群管理器"""
    return cluster