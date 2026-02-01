# CareLock Sync - Setup Guide for Team Members

## Prerequisites

Before starting, ensure you have:
- **Python 3.10+** installed
- **Docker Desktop** installed and running
- **Git** installed
- **PostgreSQL client tools** (optional, for direct DB access)
- **Postman** or similar API testing tool (optional)

---

## Quick Start Guide

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone <your-repo-url>
cd CareLock-Sync

# Or if you're getting it via USB/shared folder
# Just extract to: C:\Projects\CareLock-Sync
```

### Step 2: Create Virtual Environment

```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\activate

# Verify Python version
python --version  # Should be 3.10+
```

### Step 3: Install Dependencies

```bash
# Install all required packages
pip install -r backend\requirements.txt

# Verify installation
pip list
```

### Step 4: Configure Environment

```bash
# Copy example environment file
copy .env.example .env

# Edit .env if needed (default settings should work)
# Database ports: 5432 (hospital), 5433 (shared), 5050 (pgAdmin)
```

### Step 5: Start Docker Containers

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Verify containers are running
docker ps

# You should see:
# - carelock-hospital-db (port 5432)
# - carelock-shared-db (port 5433)
# - carelock-pgadmin (port 5050)
```

### Step 6: Initialize Databases

```bash
# Create hospital database schema
Get-Content databases\hospital-dbs\01_schema.sql | docker exec -i carelock-hospital-db psql -U hospital_user -d hospital_db

# Create shared FHIR database schema
Get-Content databases\shared-db\01_fhir_schema.sql | docker exec -i carelock-shared-db psql -U shared_user -d carelock_shared

# Generate synthetic hospital data
python scripts\generate_hospital_data.py

# Verify data was created
docker exec carelock-hospital-db psql -U hospital_user -d hospital_db -c "SELECT COUNT(*) FROM patients;"
```

### Step 7: Setup Change Data Capture (CDC)

```bash
# Setup CDC triggers on hospital database
cd backend\connector
..\..\venv\Scripts\python cdc_monitor.py
```

### Step 8: Run Initial Data Sync

```bash
# Activate virtual environment if not already active
.\venv\Scripts\activate

# Run full sync to populate shared database
cd backend\etl
..\..\venv\Scripts\python pipeline.py
```

### Step 9: Start the API Server

```bash
# Start FastAPI server
cd backend\api
..\..\venv\Scripts\python main.py

# API will be available at:
# - Main API: http://localhost:8000
# - Swagger Docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

### Step 10: Verify Installation

```bash
# Run validation tests
.\venv\Scripts\python scripts\quick_validation.py

# Test API endpoint
Invoke-WebRequest http://localhost:8000/health

# Access pgAdmin at http://localhost:5050
# Email: admin@carelock.com
# Password: admin123
```

---

## Troubleshooting

### Docker Issues

**Problem**: "Port already in use"
```bash
# Find what's using the port
netstat -ano | findstr :5432

# Stop the conflicting service or change ports in docker-compose.dev.yml
```

**Problem**: Docker containers won't start
```bash
# Check Docker Desktop is running
# Restart Docker Desktop
# Remove old containers and try again
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d
```

### Database Connection Issues

**Problem**: Cannot connect to databases
```bash
# Wait 10-15 seconds for databases to fully start
# Check container logs
docker logs carelock-hospital-db
docker logs carelock-shared-db

# Try connecting directly
docker exec -it carelock-hospital-db psql -U hospital_user -d hospital_db
```

### Python/Package Issues

**Problem**: Module not found errors
```bash
# Ensure virtual environment is activated
.\venv\Scripts\activate

# Reinstall packages
pip install -r backend\requirements.txt
```

**Problem**: Import errors when running scripts
```bash
# Run scripts from project root, not from subdirectories
cd C:\Projects\CareLock-Sync
.\venv\Scripts\python backend\api\main.py
```

---

## Common Commands Reference

### Docker Management

```bash
# Start all containers
docker-compose -f docker-compose.dev.yml up -d

# Stop all containers
docker-compose -f docker-compose.dev.yml down

# View container logs
docker logs carelock-hospital-db

# Access database directly
docker exec -it carelock-hospital-db psql -U hospital_user -d hospital_db
```

### API Server

```bash
# Start API server
cd backend\api
..\..\venv\Scripts\python main.py

# Test endpoints
Invoke-WebRequest http://localhost:8000/api/v1/patients?limit=5
Invoke-WebRequest http://localhost:8000/api/v1/sync/status
```

### Data Sync

```bash
# Full sync
cd backend\etl
..\..\venv\Scripts\python pipeline.py

# Incremental sync
..\..\venv\Scripts\python incremental_sync.py
```

---

## File Structure Overview

```
CareLock-Sync/
├── backend/
│   ├── api/              # FastAPI application
│   ├── common/           # Shared utilities
│   ├── connector/        # Schema discovery & CDC
│   ├── etl/             # Sync pipeline
│   └── schema-mapper/   # FHIR mapping
├── databases/           # SQL schemas
├── scripts/            # Utility scripts
├── tests/              # Test suites
├── docker-compose.dev.yml
├── .env
└── requirements.txt
```

---

## Team Member Checklist

- [ ] Python 3.10+ installed
- [ ] Docker Desktop installed and running
- [ ] Repository cloned/extracted
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Docker containers running
- [ ] Databases initialized
- [ ] Sample data generated
- [ ] CDC configured
- [ ] Initial sync completed
- [ ] API server running
- [ ] Validation tests passed
- [ ] Can access pgAdmin
- [ ] Can access API docs

---

## Quick Health Check

Run this to verify everything is working:

```bash
# 1. Check Docker
docker ps

# 2. Check databases
docker exec carelock-hospital-db psql -U hospital_user -d hospital_db -c "SELECT COUNT(*) FROM patients;"
docker exec carelock-shared-db psql -U shared_user -d carelock_shared -c "SELECT COUNT(*) FROM fhir_patient;"

# 3. Check API
Invoke-WebRequest http://localhost:8000/health

# 4. Run validation
.\venv\Scripts\python scripts\quick_validation.py
```

If all commands execute without errors, your setup is complete!

---

## Getting Help

If you encounter issues:
1. Check the troubleshooting section above
2. Check Docker Desktop is running
3. Ensure virtual environment is activated
4. Verify all containers are running: `docker ps`
5. Contact team lead: [Your contact info]

---

**Setup Time**: ~30 minutes  
**Last Updated**: January 31, 2026
