from typing import Optional, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class OverallState(TypedDict):
    """
    Central state definition for the BabyCare AI LangGraph orchestrator.
    """
    # add_messages (không phải operator.add) - RouterGraph nhúng các subgraph (chat_graph,
    # health_graph...) trực tiếp làm node và dùng CHUNG schema OverallState. Khi subgraph chạy,
    # nó nhận toàn bộ "messages" hiện tại của parent làm state khởi đầu, tự cộng dồn thêm tin nhắn
    # mới của riêng nó, rồi trả nguyên state đó về cho parent - nếu parent lại cộng dồn (operator.add)
    # thêm một lần nữa thì toàn bộ lịch sử cũ bị nhân đôi mỗi lượt chat. add_messages so khớp theo
    # message.id, tin nhắn đã có id trùng sẽ được ghi đè thay vì nối thêm nên tránh nhân đôi.
    messages: Annotated[list[AnyMessage], add_messages]
    baby_id: Optional[str]
    current_user_id: Optional[str]
    extracted_intent: Optional[str]
    next_step: Optional[str]
    extracted_data: Optional[dict]
    error_message: Optional[str]
    # Out-of-scope web search fields
    web_search_results: Optional[list[dict]]   # Raw results from WebSearchTool
    is_out_of_scope: Optional[bool]            # Flag set when intent = "out_of_scope"


from typing import Any, Iterator, Tuple
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions
)
from google.cloud.firestore import FieldFilter, Query
from app.infrastructure.database.connection import get_firestore_db
from app.AI_agents.core.constant import CHECKPOINT_COLLECTION
import pickle
import json
import base64

def _safe_serialize(obj: Any) -> str:
    """Serialize using pickle → base64 encoded string (safer than raw pickle storage)."""
    return base64.b64encode(pickle.dumps(obj)).decode("utf-8")

def _safe_deserialize(data: str) -> Any:
    """Deserialize from base64 encoded pickle string."""
    return pickle.loads(base64.b64decode(data.encode("utf-8")))

class FirestoreCheckpointer(BaseCheckpointSaver):
    def __init__(self):
        super().__init__()
        self._db = None

    @property
    def db(self):
        if self._db is None:
            self._db = get_firestore_db()
        return self._db

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = checkpoint["id"]
        user_id = config["configurable"].get("user_id")

        data = {
            "checkpoint": _safe_serialize(checkpoint),
            "metadata": _safe_serialize(metadata),
            "new_versions": _safe_serialize(new_versions),
            "thread_id": thread_id,
            "checkpoint_ns": checkpoint_ns,
            "checkpoint_id": checkpoint_id,
            "user_id": user_id,
        }

        doc_id = f"{thread_id}_{checkpoint_ns}_{checkpoint_id}"
        self.db.collection(CHECKPOINT_COLLECTION).document(doc_id).set(data)
        return config

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"].get("checkpoint_id")
        user_id = config["configurable"].get("user_id")

        col = self.db.collection(CHECKPOINT_COLLECTION)
        if checkpoint_id:
            doc_id = f"{thread_id}_{checkpoint_ns}_{checkpoint_id}"
            doc = col.document(doc_id).get()
            if doc.exists:
                d = doc.to_dict()
                if d.get("user_id") and user_id and d.get("user_id") != user_id:
                    raise PermissionError("Access denied: You do not have permission to access this chat thread.")
                return CheckpointTuple(
                    config=config,
                    checkpoint=_safe_deserialize(d["checkpoint"]),
                    metadata=_safe_deserialize(d["metadata"]),
                    parent_config=None,
                )
        else:
            # Không có checkpoint_id cụ thể nghĩa là caller muốn checkpoint MỚI NHẤT (vd. aget_state
            # khi load lại trang) - phải order_by checkpoint_id giảm dần trước khi limit(1), nếu
            # không Firestore trả về bất kỳ document nào khớp filter (thứ tự không xác định), có thể
            # trúng một checkpoint cũ/rỗng từ đầu phiên thay vì checkpoint chứa đủ lịch sử chat mới
            # nhất - đây là lý do lịch sử chat biến mất ngẫu nhiên sau khi reload trang.
            docs = (
                col.where(filter=FieldFilter("thread_id", "==", thread_id))
                .where(filter=FieldFilter("checkpoint_ns", "==", checkpoint_ns))
                .order_by("checkpoint_id", direction=Query.DESCENDING)
                .limit(1)
                .get()
            )
            if docs:
                d = docs[0].to_dict()
                if d.get("user_id") and user_id and d.get("user_id") != user_id:
                    raise PermissionError("Access denied: You do not have permission to access this chat thread.")
                return CheckpointTuple(
                    config={
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": d["checkpoint_id"],
                            "user_id": user_id,
                        }
                    },
                    checkpoint=_safe_deserialize(d["checkpoint"]),
                    metadata=_safe_deserialize(d["metadata"]),
                    parent_config=None,
                )
        return None

    def list(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        col = self.db.collection(CHECKPOINT_COLLECTION)
        query = col
        user_id = config["configurable"].get("user_id") if config else None

        if config:
            thread_id = config["configurable"]["thread_id"]
            checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
            query = query.where(filter=FieldFilter("thread_id", "==", thread_id)).where(filter=FieldFilter("checkpoint_ns", "==", checkpoint_ns))

        docs = query.get()
        for doc in docs:
            d = doc.to_dict()
            if d.get("user_id") and user_id and d.get("user_id") != user_id:
                continue
            yield CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": d["thread_id"],
                        "checkpoint_ns": d["checkpoint_ns"],
                        "checkpoint_id": d["checkpoint_id"],
                        "user_id": user_id,
                    }
                },
                checkpoint=_safe_deserialize(d["checkpoint"]),
                metadata=_safe_deserialize(d["metadata"]),
                parent_config=None,
            )

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        return self.get_tuple(config)

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        return self.put(config, checkpoint, metadata, new_versions)

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Any,
        task_id: str,
    ) -> None:
        pass

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Any,
        task_id: str,
    ) -> None:
        pass



    async def alist(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ):
        for checkpoint_tuple in self.list(config, filter=filter, before=before, limit=limit):
            yield checkpoint_tuple

