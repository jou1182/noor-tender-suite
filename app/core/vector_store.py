import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from dotenv import load_dotenv

load_dotenv()

import threading
_global_client = None
_client_lock = threading.Lock()

def get_global_client():
    global _global_client
    with _client_lock:
        if _global_client is None:
            qdrant_url = os.getenv("QDRANT_URL", "local")
            if qdrant_url == "local":
                _global_client = QdrantClient(path="qdrant_data")
            elif qdrant_url == ":memory:":
                _global_client = QdrantClient(location=":memory:")
            else:
                _global_client = QdrantClient(url=qdrant_url)
    return _global_client

class VectorStoreAdapter:
    def __init__(self, collection_name: str = "noor_tender_knowledge"):
        self.collection_name = collection_name
        self.client = get_global_client()
        self._initialize_collection()

    def _initialize_collection(self):
        if not self.client.collection_exists(collection_name=self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )

    def get_client(self) -> QdrantClient:
        return self.client
