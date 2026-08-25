import uuid
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

class FeedbackEngine:
    def __init__(self, use_memory=True):
        # Local embedded vector memory for frictionless integration and isolated testing
        self.client = QdrantClient(location=":memory:") if use_memory else QdrantClient(host="localhost", port=6333)
        self.collection_name = "tender_lessons_learned"
        
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )

    def mock_embedding(self, text: str) -> List[float]:
        """Mock 384-dimensional embedding array."""
        return [0.1] * 384

    def record_outcome(self, tender_id: str, client_name: str, outcome: str, debrief_notes: str) -> bool:
        """
        Indexes a post-award bid debrief into the Qdrant vector database.
        """
        vector = self.mock_embedding(debrief_notes)
        
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "tender_id": tender_id,
                "client_name": client_name.lower(),
                "outcome": outcome,
                "debrief_notes": debrief_notes
            }
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        return True

    def retrieve_historical_risks(self, client_name: str) -> List[Dict[str, Any]]:
        """
        Retrieves institutional 'Lessons Learned' focusing strictly on past negative outcomes 
        (Lost/Disqualified) for a specific client to serve as proactive guardrails.
        """
        records, _ = self.client.scroll(
            collection_name=self.collection_name,
            limit=100
        )
        
        risks = []
        for record in records:
            payload = record.payload
            if payload.get("client_name") == client_name.lower() and payload.get("outcome") in ["Lost", "Disqualified"]:
                risks.append({
                    "tender_id": payload.get("tender_id"),
                    "outcome": payload.get("outcome"),
                    "lesson_learned": payload.get("debrief_notes")
                })
        return risks
