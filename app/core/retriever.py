from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.core.vector_store import VectorStoreAdapter

class HybridRetriever:
    def __init__(self, collection_name: str = "engineering_standards"):
        self.adapter = VectorStoreAdapter(collection_name=collection_name)
        self.client = self.adapter.get_client()
        self.collection_name = collection_name

    def retrieve(self, query_vector: list, standard_code: str = None, top_k: int = 3, score_threshold: float = 0.5):
        """
        Executes a hybrid search using vector similarity and metadata filtering.
        """
        query_filter = None
        if standard_code:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="standard_code",
                        match=MatchValue(value=standard_code)
                    )
                ]
            )

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
            score_threshold=score_threshold
        )
        
        return [{"score": r.score, "payload": r.payload} for r in results.points]
