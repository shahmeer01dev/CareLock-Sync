# CareLock Sync

**Hospital Database Synchronization System with Automated FHIR Mapping**

> Final Year Project - BS Computer Science  
> Bahria University Lahore Campus 
> Team: Waleed Khalid, Muhammad Mohsin, Shahmeer Nadeem  
> Supervisor: Dr. Muhammad Saqib Sohail

---

## 🎯 Project Overview

CareLock Sync is an intelligent hospital database synchronization system that:
- **Automatically discovers** database schemas
- **Tracks changes** in real-time using CDC (Change Data Capture)
- **Maps data** to FHIR R4 standard
- **Synchronizes** across multiple hospitals
- **Provides REST API** for system control

---

## ✨ Features

✅ **Automatic Schema Discovery** - No manual configuration needed  
✅ **Real-time CDC** - PostgreSQL trigger-based change tracking  
✅ **FHIR R4 Compliance** - International healthcare data standard  
✅ **ETL Pipeline** - Extract, Transform, Load with UPSERT  
✅ **Incremental Sync** - Only sync what changed  
✅ **REST API** - 25+ endpoints for complete control  
✅ **Multi-tenant** - Support multiple hospitals  
✅ **Production Ready** - Tested and validated  

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites:
- Docker Desktop (running)
- Python 3.10+
- Git

### Setup:

```powershell
# Clone and enter directory
git clone <your-repo-url>
cd CareLock-Sync

# Run automated setup (Windows)
.\setup.ps1

# Or manual setup:
docker-compose -f docker-compose.dev.yml up -d
python -m venv venv
.\venv\Scripts\activate
pip install -r backend/requirements.txt

# Initialize databases (see DEPLOYMENT_GUIDE.md)

# Start API
cd backend\api
python main.py
```

### Access:
- **API Documentation**: http://localhost:8000/docs
- **pgAdmin**: http://localhost:5050 (admin@carelock.com / admin123)

---

## 📊 Current Status

**Phase 1**: Foundation ✅ Complete  
**Phase 2**: Local Connector ✅ Complete  
**Phase 3**: RAG-Powered Mapping 🔄 In Progress  
**Phase 4**: Multi-Hospital Support ⏳ Planned  
**Phase 5**: Production Deployment ⏳ Planned  

**Overall Progress**: 40% Complete

---

## 🏗️ Architecture

```
Hospital Database (PostgreSQL)
         ↓ [CDC Triggers]
    Schema Discovery
         ↓
    FHIR Mapping Engine
         ↓
    ETL Pipeline
         ↓
Shared FHIR Database (PostgreSQL)
```

---

## 📁 Project Structure

```
CareLock-Sync/
├── backend/
│   ├── api/              # FastAPI application
│   ├── common/           # Shared utilities
│   ├── connector/        # Schema discovery & CDC
│   ├── schema-mapper/    # FHIR mapping
│   ├── etl/              # Sync pipeline
│   └── requirements.txt  # Python dependencies
├── databases/
│   ├── hospital-dbs/     # Hospital DB schema
│   └── shared-db/        # FHIR DB schema
├── scripts/              # Utility scripts
├── tests/                # Test suites
├── docker-compose.dev.yml
└── setup.ps1             # Automated setup
```

---

## 💻 Tech Stack

**Backend**: Python 3.10, FastAPI, SQLAlchemy  
**Databases**: PostgreSQL 15  
**FHIR**: HL7 FHIR R4  
**CDC**: PostgreSQL Triggers  
**AI/ML**: LangChain, ChromaDB (Phase 3)  
**Tools**: Docker, pgAdmin, Git  

---

## 📖 Documentation

- **Deployment Guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Phase 1 Report**: Phase1_COMPLETE.md
- **Phase 2 Report**: Phase2_COMPLETE.md
- **API Docs**: http://localhost:8000/docs (when running)

---

## 🎬 Demo

### For Team/Supervisor:

1. **Start system**: `.\setup.ps1` or follow DEPLOYMENT_GUIDE.md
2. **Open API docs**: http://localhost:8000/docs
3. **Demonstrate**:
   - Schema discovery
   - CDC change tracking
   - FHIR mapping
   - Full & incremental sync
   - REST API

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete demo script.

---

## 🧪 Testing

```bash
# Quick validation
python scripts/quick_validation.py

# Integration tests
python tests/test_integration.py

# Check sync status
curl http://localhost:8000/api/v1/sync/status
```

---

## 📊 Key Metrics

**Code**: 4,400+ lines  
**Endpoints**: 25+ REST APIs  
**Performance**: 29 records/second  
**Data**: 500 patients, 993 encounters, 2,975 labs  
**Sync**: Sub-second incremental updates  

---

## 👥 Team

**Waleed Khalid** - Schema Discovery & CDC  
**Muhammad Mohsin** - FHIR Mapping & ETL  
**Shahmeer Nadeem** - API & Testing  

**Supervisor**: Dr. Muhammad Saqib Sohail

---

## 📧 Contact

For questions or issues:
- Create an issue in this repository
- Contact team members
- Email supervisor

---

## 📄 License

This is a Final Year Project for educational purposes.  
© 2026 Team CareLock Sync - FAST-NUCES Islamabad

---

## 🙏 Acknowledgments

- Dr. Muhammad Saqib Sohail for supervision
- Bahria University Lahore Campus for resources
- HL7 FHIR community for standards

---

**Last Updated**: February 1st, 2026  
**Version**: 0.3.0 (Phase 2 Complete)
