from typing import Optional, Annotated
import operator
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage

class OverallState(TypedDict):
    """
    Central state definition for the BabyCare AI LangGraph orchestrator.
    """
    messages: Annotated[list[AnyMessage], operator.add]
    baby_id: Optional[str]
    current_user_id: Optional[str]
    extracted_intent: Optional[str]
    next_step: Optional[str]
    extracted_data: Optional[dict]
    error_message: Optional[str]

from typing import Any, Iterator, Tuple
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions
)
from app.infrastructure.database.connection import get_firestore_db
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

        data = {
            "checkpoint": _safe_serialize(checkpoint),
            "metadata": _safe_serialize(metadata),
            "new_versions": _safe_serialize(new_versions),
            "thread_id": thread_id,
            "checkpoint_ns": checkpoint_ns,
            "checkpoint_id": checkpoint_id,
        }

        doc_id = f"{thread_id}_{checkpoint_ns}_{checkpoint_id}"
        self.db.collection("chat_checkpoints").document(doc_id).set(data)
        return config

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"].get("checkpoint_id")

        col = self.db.collection("chat_checkpoints")
        if checkpoint_id:
            doc_id = f"{thread_id}_{checkpoint_ns}_{checkpoint_id}"
            doc = col.document(doc_id).get()
            if doc.exists:
                d = doc.to_dict()
                return CheckpointTuple(
                    config=config,
                    checkpoint=_safe_deserialize(d["checkpoint"]),
                    metadata=_safe_deserialize(d["metadata"]),
                    parent_config=None,
                )
        else:
            docs = (
                col.where("thread_id", "==", thread_id)
                .where("checkpoint_ns", "==", checkpoint_ns)
                .limit(1)
                .get()
            )
            if docs:
                d = docs[0].to_dict()
                return CheckpointTuple(
                    config={
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": d["checkpoint_id"],
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
        col = self.db.collection("chat_checkpoints")
        query = col
        if config:
            thread_id = config["configurable"]["thread_id"]
            checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
            query = query.where("thread_id", "==", thread_id).where("checkpoint_ns", "==", checkpoint_ns)
            
        docs = query.get()
        for doc in docs:
            d = doc.to_dict()
            yield CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": d["thread_id"],
                        "checkpoint_ns": d["checkpoint_ns"],
                        "checkpoint_id": d["checkpoint_id"],
                    }
                },
                checkpoint=_safe_deserialize(d["checkpoint"]),
                metadata=_safe_deserialize(d["metadata"]),
                parent_config=None,
            )
