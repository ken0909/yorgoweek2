# Backend Quick Reference

## 🚀 Start Backend (One Command)

```bash
cp .env.example .env  # Setup once
# Edit .env and add GEMINI_API_KEY
docker compose up --build
```

Then visit: **http://localhost:8000/docs**

---

## 📡 Core Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/extract` | Stage 1 LLM extraction |
| POST | `/predict` | Full pipeline + save to DB |
| GET | `/health` | Health check |
| GET | `/api/predictions` | List all predictions |
| GET | `/api/predictions/{id}` | Get one prediction |
| DELETE | `/api/predictions/{id}` | Delete prediction |
| GET | `/api/extractions` | List extraction logs |
| GET | `/api/stats` | Get statistics |

---

## 💾 Database

**Predictions Table:**
- `id` - Unique ID
- `query` - User input
- `features` - JSON (10 features)
- `predicted_price` - Model output
- `interpretation` - LLM explanation
- `confidence` - high/medium/low
- `created_at` - Timestamp

**ExtractionLogs Table:**
- `id`, `query`, `extracted_fields`, `missing_fields`, `confidence`, `features`, `created_at`

---

## 🧪 Test Examples

```bash
# Health check
curl http://localhost:8000/health

# Get all predictions
curl http://localhost:8000/api/predictions

# Get stats
curl http://localhost:8000/api/stats

# Delete old data
curl -X DELETE http://localhost:8000/api/predictions/older-than/30
```

---

## 🐳 Docker Commands

```bash
# Start
docker compose up --build

# View logs
docker compose logs -f backend
docker compose logs -f db

# Stop
docker compose down

# Clean (delete data)
docker compose down -v
```

---

## 📁 Key Files

- **main.py** - Core FastAPI app
- **history.py** - Analytics endpoints
- **database.py** - Database models & connection
- **docker-compose.yml** - Container orchestration
- **.env.example** - Environment template
- **requirements.txt** - Dependencies (added: sqlalchemy, psycopg2)

---

## ⚙️ Configuration

**In .env:**
```
POSTGRES_USER=realestateuser
POSTGRES_PASSWORD=securepassword123
POSTGRES_DB=real_estate_agent
GEMINI_API_KEY=your_key_here
```

Docker Compose auto-sets: `DATABASE_URL=postgresql://user:pass@db:5432/db`

---

## 📖 Documentation

- **BACKEND_SETUP.md** - Detailed setup guide
- **BACKEND_ARCHITECTURE.md** - Architecture overview
- **BACKEND_COMPLETE.md** - Feature summary

---

## ✅ What's Included

✓ PostgreSQL database
✓ SQLAlchemy ORM models
✓ Prediction history endpoints
✓ Analytics endpoints  
✓ Automatic DB initialization
✓ Docker Compose setup
✓ Full CORS support
✓ Pagination
✓ Error handling
✓ Interactive API docs

---

## 🔗 URLs

- **API (Main):** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Database:** postgresql://localhost:5432 (see .env)

---

## ⚡ Common Issues

| Issue | Fix |
|-------|-----|
| Connection refused | `docker compose ps` - check if running |
| Table not found | Check logs: `docker compose logs backend` |
| GEMINI_API_KEY error | Add key to `.env`, restart |
| Port 5432 in use | `docker compose down`, stop Postgres |

---

**Quick Start: `docker compose up --build` → Open http://localhost:8000/docs**
