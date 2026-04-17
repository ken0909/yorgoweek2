# ============================================================================
# Dockerfile for the Real Estate Agent FastAPI application
#
# This Dockerfile packages the FastAPI app, ML model, and dependencies
# into a portable Docker container that runs on any system with Docker.
#
# Build: docker build -t real-estate-agent:v1 .
# Run:   docker run -p 8000:8000 --env-file .env real-estate-agent:v1
# ============================================================================

# Start with Python 3.11 slim image
# slim = minimal base image (no build tools, small size ~150MB)
# 3.11 = stable release with good performance
# Alpine would be smaller but requires additional C compilation for some packages
FROM python:3.11-slim

# Set working directory inside container
# All subsequent commands (RUN, COPY) happen relative to this path
# /app is a common convention for application code
WORKDIR /app

# Copy requirements.txt BEFORE copying app code
# This leverages Docker's layer caching:
# - If requirements.txt hasn't changed, Docker reuses the layer
# - If code changes, only the code layer is rebuilt (much faster)
# - This order is intentional and important for build performance
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir: Don't store pip cache in the image (saves ~100MB)
# This runs pip install and installs all packages listed in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
# This includes:
#   - app/main.py (FastAPI application)
#   - app/schemas.py (Pydantic models)
#   - app/predictor.py (ML model loading)
#   - app/llm_chain.py (LLM orchestration)
#   - app/prompts.py (LLM prompts)
#   - app/model/pipeline.joblib (serialized ML model)
#   - app/model/train_stats.json (training statistics)
COPY . .

# Expose port 8000
# This documents that the container listens on port 8000
# Does NOT automatically map host:container ports (that's done with -p flag)
# The flag is informational and helpful for container orchestration
EXPOSE 8000

# Start the FastAPI application with Uvicorn
# Command explanation:
#   uvicorn = ASGI server that runs FastAPI apps
#   main:app = module:variable (main.py, FastAPI app instance named 'app')
#   --host 0.0.0.0 = listen on all network interfaces
#     Required for Docker: without this, only localhost:8000 works
#     Inside Docker, localhost only reaches processes in the same container
#     0.0.0.0 accepts traffic from outside the container (from host or other containers)
#   --port 8000 = listen on port 8000 (must match EXPOSE above)
#   --workers 1 = single worker process (fine for bootcamp project)
#     For production, use --workers 4 or more, or use gunicorn instead
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Health check (optional but recommended for production)
# Docker can use this to determine if the container is healthy
# Uncomment to enable:
# HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
#   CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)" || exit 1
