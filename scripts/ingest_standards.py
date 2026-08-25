import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.vector_store import VectorStoreAdapter
from qdrant_client.models import PointStruct, VectorParams, Distance

def ingest_standards():
    adapter = VectorStoreAdapter(collection_name="engineering_standards")
    client = adapter.get_client()

    # Re-initialize collection to ensure it exists
    if not client.collection_exists(collection_name="engineering_standards"):
        client.create_collection(
            collection_name="engineering_standards",
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )

    # Key clauses from SBC and FIDIC
    standards_data = [
        {"id": 1, "code": "SBC-303", "section": "Foundations", "content": "All structural foundations must bear on competent strata and withstand a minimum allowable bearing capacity of 150 kPa."},
        {"id": 2, "code": "SBC-304", "section": "Concrete", "content": "Concrete mix design for structural columns must achieve a minimum 28-day compressive strength of 30 MPa."},
        {"id": 3, "code": "FIDIC-RED", "section": "Clause 4.1", "content": "The Contractor shall design (to the extent specified), execute and complete the Works in accordance with the Contract."}
    ]

    points = []
    for std in standards_data:
        # Dummy vector simulating a 1536-d text embedding
        dummy_vector = [0.0] * 1536
        dummy_vector[std["id"]] = 1.0
        
        points.append(PointStruct(
            id=std["id"],
            vector=dummy_vector,
            payload={
                "standard_code": std["code"],
                "section": std["section"],
                "text": std["content"]
            }
        ))
        
    client.upsert(
        collection_name="engineering_standards",
        points=points
    )
    print(f"Successfully ingested {len(points)} standards into 'engineering_standards' collection.")

if __name__ == "__main__":
    ingest_standards()
