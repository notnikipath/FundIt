# Demo Script

1. Start stack:

```bash
docker compose up --build -d
```

2. Check gateway health:

```bash
curl http://localhost:8500/health
```

3. Run pledge workflow:

```bash
python scripts/demo_pipeline.py
```

4. Open dashboard:

- `http://localhost:5177`
- Project ID: `PRJ-DEMO`

5. Validate services health:

```bash
curl http://localhost:8500/services/health
```

6. Finalize campaign (optional):

```bash
curl -X POST http://localhost:8500/workflow/finalize/PRJ-DEMO -H "Content-Type: application/json" -d "{\"actor_role\":\"admin\",\"actor_id\":\"SYS\"}"
```
