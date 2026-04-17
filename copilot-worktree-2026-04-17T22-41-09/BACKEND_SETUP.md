# Backend Setup & Quick Start

## What's Included

✅ **FastAPI Backend** - REST API with OpenAPI docs
✅ **PostgreSQL Database** - Persistent storage with SQLAlchemy ORM
✅ **Prediction History** - Endpoints to retrieve/delete past predictions
✅ **Extraction Logging** - Audit trail of LLM feature extraction
✅ **Docker Compose** - One-command setup and deployment

## Quick Start (Docker Desktop)

### Step 1: Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:
```
POSTGRES_USER=realestateuser
POSTGRES_PASSWORD=securepassword123
POSTGRES_DB=real_estate_agent
GEMINI_API_KEY=your_actual_gemini_key_here
```

### Step 2: Build and start services

```bash
docker compose up --build
```

This will:
- Build the FastAPI backend image
- Start PostgreSQL container
- Create database tables automatically
- Expose the API at `http://localhost:8000`

### Step 3: Verify services are running

**Health check:**
```bash
curl http://localhost:8000/health
```

**API docs (interactive):**
- Open http://localhost:8000/docs in your browser
- Try out endpoints with live API documentation

**View logs:**
```bash
docker compose logs -f backend
```

---

## API Endpoints

### Core Endpoints

**POST /extract**
- Extract house features from natural language query
- Request: `{"query": "3 bedroom house with 2 bathrooms..."}`
- Response: Extracted features + confidence + missing fields

**POST /predict**
- Full pipeline: extract → ML model → LLM interpretation
- Request: `{"query": "...", "features": {...}}`
- Response: Predicted price + interpretation + confidence

**GET /health**
- Health check (used by Docker healthchecks)
- Response: `{"status": "ok"}`

### History & Analytics Endpoints

**GET /api/predictions** (paginated)
- List all predictions
- Query params: `skip=0&limit=100`

**GET /api/predictions/{id}**
- Get a specific prediction by ID

**DELETE /api/predictions/{id}**
- Delete a specific prediction

**GET /api/extractions** (paginated)
- List all extraction logs (for debugging)

**GET /api/extractions/{id}**
- Get a specific extraction log

**GET /api/stats**
- Aggregate statistics (total predictions, avg price, confidence distribution)

**DELETE /api/predictions/older-than/{days}**
- Delete predictions older than N days (cleanup)

---

## Interactive API Documentation

The API comes with auto-generated docs powered by FastAPI:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Try endpoints directly in the browser!

---

## Database

### Access Postgres directly (optional)

```bash
# From your host machine:
psql postgresql://realestateuser:securepassword123@localhost:5432/real_estate_agent

# Inside Docker container:
docker compose exec db psql -U realestateuser -d real_estate_agent
```

### Database schema

**Predictions table**
- Stores full prediction results with extracted features, price, interpretation, confidence
- Indexed by: id, created_at, predicted_price

**ExtractionLogs table**
- Stores Stage 1 LLM extraction results for debugging
- Indexed by: id, created_at, confidence

**Users table** (reserved for multi-tenant expansion)
- Currently unused, available for future user authentication

---

## File Structure

```
├── main.py               # FastAPI app, startup logic, /extract and /predict endpoints
├── history.py            # History & analytics endpoints
├── database.py           # SQLAlchemy models, Postgres connection
├── schemas.py            # Pydantic models (input/output validation)
├── predictor.py          # ML model loading and prediction
├── llm_chain.py          # LLM Stages 1 & 2
├── prompts.py            # Prompt templates
├── requirements.txt      # Python dependencies (FastAPI, SQLAlchemy, etc.)
├── Dockerfile            # Container image definition
├── docker-compose.yml    # Multi-container orchestration
├── .env.example          # Template for environment variables
└── model/                # Serialized ML pipeline (from notebooks)
    ├── pipeline.joblib   # Trained sklearn model
    └── train_stats.json  # Training set statistics
```

---

## Common Tasks

### Rebuild after code changes

```bash
docker compose down
docker compose up --build
```

### View recent predictions

```bash
curl http://localhost:8000/api/predictions?limit=10
```

### Check model performance

```bash
curl http://localhost:8000/api/stats
```

### Stop services

```bash
docker compose down
```

### Stop and remove all data (clean slate)

```bash
docker compose down -v  # -v also removes the database volume
```

---

## Troubleshooting

### "Connection refused" when accessing http://localhost:8000

- Verify `docker compose up` completed successfully
- Check: `docker compose ps` (both `backend` and `db` should be `Up`)
- View logs: `docker compose logs backend`

### Database errors in logs

- Ensure `.env` is copied from `.env.example`
- Verify Postgres credentials match in `.env` and docker-compose.yml
- Try clean restart: `docker compose down -v && docker compose up --build`

### "ModuleNotFoundError" for database or other imports

- Rebuild: `docker compose down && docker compose up --build`

### GEMINI_API_KEY errors

- Verify your API key is set in `.env`
- Test extraction/predict without running LLM: use `/extract` endpoint first to debug

---

## Next Steps

1. **Integrate with Streamlit UI** (`streamlit_app.py`)
   - Update the API base URL to `http://localhost:8000` (or Docker service name)

2. **Add Authentication** (optional)
   - Add JWT tokens to User model
   - Protect endpoints with `@require_auth` decorator

3. **Database Migrations** (optional)
   - Use Alembic to version control schema changes

4. **Production Deployment**
   - Use environment-specific configs
   - Set up cloud Postgres (e.g., AWS RDS, Azure Database for Postgres)
   - Deploy Docker image to container registry (ECR, Docker Hub, etc.)

---

## Support

For issues or questions:
1. Check Docker logs: `docker compose logs backend`
2. Review OpenAPI docs at http://localhost:8000/docs
3. Test manually with `curl` commands from this guide
