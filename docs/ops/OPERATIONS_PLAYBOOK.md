# ConTech AI Platform: Operations Playbook

## 1. System Requirements & Tech Stack
- **OS**: Linux / Windows Server (WSL2 recommended for local dev)
- **Runtime**: Python 3.10+, Node.js 20+
- **Database**: PostgreSQL 16 (Primary), SQLite (Fallback), Qdrant (Vector DB), Redis (State Cache)
- **Orchestration**: Kubernetes v1.28+, Helm v3

## 2. Multi-Provider LLM Gateway Failover Configuration
The `llm_gateway.py` module operates a robust failover circuit protecting the system from API rate limits.
Set the following environment variables in your Kubernetes Secrets:
```env
OPENAI_API_KEY="sk-..."       # Priority 1: GPT-4o
ANTHROPIC_API_KEY="sk-..."    # Priority 2: Claude 3.5 Sonnet
GEMINI_API_KEY="AIza..."      # Priority 3: Gemini 1.5 Pro
OLLAMA_BASE_URL="http://..."  # Priority 4: Local Llama3 (Airgapped Fallback)
```

## 3. Kubernetes Deployment via Helm
The entire microservices stack (Frontend, Backend, DBs) is packaged in a Helm Chart.

### Installation
1. Ensure your Kubernetes cluster context is set.
2. Deploy the platform to the `contech-prod` namespace:
```bash
kubectl create namespace contech-prod
helm install contech-ai ./deploy/helm/contech-platform --namespace contech-prod -f ./deploy/helm/contech-platform/values.yaml
```
3. Check pod status:
```bash
kubectl get pods -n contech-prod
```

## 4. Disaster Recovery & Restoration (DR)
The `backup_restore_manager.py` script automatically manages encrypted snapshots for PostgreSQL and the Qdrant local persistence directories.

### Creating a Manual Backup
```bash
python scripts/backup_restore_manager.py --action backup
```
*Outputs an encrypted zip payload to `backups/YYYYMMDD_HHMMSS_snapshot.zip`*

### Restoring from a Snapshot
In the event of catastrophic data corruption:
```bash
python scripts/backup_restore_manager.py --action restore --target backups/YYYYMMDD_HHMMSS_snapshot.zip
```
*Note: This requires restarting the Uvicorn workers and Next.js frontend to clear caching layers post-restoration.*

## 5. End-to-End Auditing
To verify platform health post-deployment, trigger the E2E verification test suite:
```bash
pytest tests/test_full_system_e2e.py
```
This guarantees the active LangGraph routing, empirical engines, and cryptographic sealers are operating cohesively.
