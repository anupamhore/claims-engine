# Docker Setup Guide - Claims Triage Engine

## Quick Start (3 Commands)

```bash
# 1. Start all services (PostgreSQL + Redis)
docker-compose up -d

# 2. Run database migrations
docker-compose exec postgres psql -U claims_user -d claims_db -c "SELECT 1"

# 3. Start your FastAPI app (on your MacBook)
uvicorn src.api.main:app --reload
```
