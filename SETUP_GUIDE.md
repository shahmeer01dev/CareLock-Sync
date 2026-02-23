# CareLock Sync - Setup Guide

## 📋 Quick Start

### For Windows Users (Recommended):
```powershell
.\setup_complete.ps1
```

### For All Platforms (Cross-Platform):
```bash
python scripts/ultimate_setup.py
```

---

## 🎯 What Gets Set Up

Both setup scripts do the following:

1. ✅ Check prerequisites (Python 3.10+, Docker, Oracle Instant Client)
2. ✅ Install Python dependencies
3. ✅ Start all 5 Docker database containers
4. ✅ Wait for Oracle initialization (2-3 minutes)
5. ✅ Setup PostgreSQL with sample data
6. ✅ Setup MySQL with sample data
7. ✅ Setup MongoDB with sample data
8. ✅ Setup Oracle with sample data
9. ✅ Setup SQL Server with sample data
10. ✅ Create sync daemon configuration
11. ✅ Run comprehensive tests
12. ✅ Test Change Data Capture on all databases

**Total Time:** 10-15 minutes

---

## 🔧 Setup Methods Comparison

| Method | Platform | Recommended For | Status |
|--------|----------|----------------|--------|
| **`setup_complete.ps1`** | Windows Only | Windows users | ✅ **NEW - Complete** |
| **`scripts/ultimate_setup.py`** | Windows, macOS, Linux | Mixed teams | ✅ **NEW - Complete** |
| `setup.ps1` | Windows Only | Legacy | ⚠️ Deprecated (old structure) |
| `scripts/complete_automated_setup.py` | All | Legacy | ⚠️ Partial (3/5 databases) |

---

## 📝 Detailed Setup Instructions

### Prerequisites

Before running any setup script, ensure you have:

#### 1. Python 3.10 or higher
```bash
python --version
# Should show: Python 3.10.x or higher
```

#### 2. Docker Desktop
- Download: https://www.docker.com/products/docker-desktop
- Must be **running** before setup

#### 3. Oracle Instant Client

**Windows:**
1. Download from: https://www.oracle.com/database/technologies/instant-client/downloads.html
2. Extract to: `C:\oracle\instantclient_23_0`
3. The setup script will add it to PATH automatically

**macOS:**
1. Download from: https://www.oracle.com/database/technologies/instant-client/macos-intel-x86-downloads.html
2. Install to: `/usr/local/instantclient_19_8`

**Linux:**
1. Download from: https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html
2. Extract to: `/opt/oracle/instantclient_23_5`

---

## 🚀 Running Setup

### Method 1: PowerShell (Windows - Recommended)

```powershell
# 1. Open PowerShell (no admin required)
# 2. Navigate to project
cd C:\Projects\CareLock-Sync

# 3. Allow script execution (if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# 4. Run setup
.\setup_complete.ps1
```

### Method 2: Python (Cross-Platform)

```bash
# 1. Navigate to project
cd ~/projects/CareLock-Sync  # macOS/Linux
cd C:\Projects\CareLock-Sync  # Windows

# 2. Run setup
python scripts/ultimate_setup.py
```

---

## ✅ After Setup

### 1. Verify Everything is Working

All setup scripts run tests automatically, but you can re-run them:

```bash
# Set Oracle PATH (Windows)
$env:PATH = "C:\oracle\instantclient_23_0;$env:PATH"

# Set Oracle PATH (macOS/Linux)
export PATH="/usr/local/instantclient_19_8:$PATH"

# Run comprehensive test
python scripts/test_all_5_databases_final.py
```

**Expected Output:**
```
✓ SUCCESS! 100% MARKET COVERAGE ACHIEVED!
All 5 major hospital database types are operational
```

### 2. Add Gemini API Key (Optional)

For AI-powered schema mapping:

1. Get API key from: https://makersuite.google.com/app/apikey
2. Edit `config/sync_config.json`
3. Replace `YOUR_GEMINI_API_KEY_HERE` with your actual key

### 3. Start the Sync Daemon

```bash
# Set Oracle PATH first
# Windows:
$env:PATH = "C:\oracle\instantclient_23_0;$env:PATH"

# macOS/Linux:
export PATH="/usr/local/instantclient_19_8:$PATH"

# Start daemon
python backend/sync_daemon.py
```

**Expected Output:**
```
2026-02-08 14:30:15 - INFO - Starting synchronization daemon
2026-02-08 14:30:15 - INFO - Connected to postgres_hospital
2026-02-08 14:30:15 - INFO - Connected to mysql_hospital
2026-02-08 14:30:15 - INFO - Connected to mongodb_hospital
2026-02-08 14:30:16 - INFO - Connected to oracle_hospital
2026-02-08 14:30:16 - INFO - Connected to sqlserver_hospital
2026-02-08 14:30:16 - INFO - Starting synchronization loop...
```

The daemon now continuously monitors all 5 databases! 🎉

---

## 🧪 Testing Live Synchronization

### Make a Change

```bash
# Update patient in PostgreSQL
docker exec -it carelock_postgres psql -U hospital_user -d hospital_db -c \
  "UPDATE patients SET email='live-test@demo.com' WHERE patient_id=1;"
```

### Watch the Daemon

Within 5 seconds, you should see:

```
2026-02-08 14:32:26 - INFO - Retrieved 1 changes from postgres_hospital
2026-02-08 14:32:26 - INFO - Deduplicated to 1 operations
2026-02-08 14:32:26 - INFO - Transformed 1 FHIR resources
2026-02-08 14:32:26 - INFO - Synchronized 1 resources
```

**Success!** Your change was detected and synchronized! ✅

---

## 📊 Database Connections

After setup, all databases are accessible:

| Database | Host | Port | Username | Password |
|----------|------|------|----------|----------|
| PostgreSQL | localhost | 5432 | hospital_user | hospital_pass |
| MySQL | localhost | 3306 | root | root |
| MongoDB | localhost | 27017 | - | - |
| Oracle | localhost | 1521 | hospital_user | hospital_pass |
| SQL Server | localhost | 1433 | sa | YourStrong@Passw0rd |

### Connection Examples

```bash
# PostgreSQL
psql -h localhost -U hospital_user -d hospital_db

# MySQL
mysql -h localhost -u root -proot

# MongoDB
mongosh mongodb://localhost:27017

# Oracle
sqlplus hospital_user/hospital_pass@localhost:1521/XE

# SQL Server
sqlcmd -S localhost -U sa -P 'YourStrong@Passw0rd'
```

---

## 🛠️ Useful Commands

### Docker Container Management

```bash
# View all containers
docker ps

# View container logs
docker logs carelock_postgres
docker logs carelock_mysql
docker logs carelock_mongodb
docker logs carelock_oracle
docker logs carelock_sqlserver

# Stop all containers
docker-compose down

# Start all containers
docker-compose up -d

# Restart a specific container
docker restart carelock_oracle
```

### Database Management

```bash
# Execute SQL in PostgreSQL
docker exec -it carelock_postgres psql -U hospital_user -d hospital_db

# Execute SQL in MySQL
docker exec -it carelock_mysql mysql -uroot -proot hospital_db_mysql

# Access MongoDB shell
docker exec -it carelock_mongodb mongosh

# Execute SQL in Oracle
docker exec -it carelock_oracle sqlplus hospital_user/hospital_pass@XE

# Execute SQL in SQL Server
docker exec carelock_sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P 'YourStrong@Passw0rd'
```

---

## 🐛 Troubleshooting

### Issue: "Docker is not running"

**Solution:**
1. Open Docker Desktop
2. Wait for it to fully start (whale icon in system tray)
3. Run setup again

### Issue: "Oracle Instant Client not found"

**Solution:**
1. Download from Oracle website
2. Extract to correct location:
   - Windows: `C:\oracle\instantclient_23_0`
   - macOS: `/usr/local/instantclient_19_8`
   - Linux: `/opt/oracle/instantclient_23_5`
3. Run setup again

### Issue: "DPI-1047: Cannot locate Oracle Client library"

**Solution:**
```bash
# Windows:
$env:PATH = "C:\oracle\instantclient_23_0;$env:PATH"

# macOS/Linux:
export PATH="/usr/local/instantclient_19_8:$PATH"

# Verify:
python -c "import cx_Oracle; print('OK!')"
```

### Issue: "Oracle container keeps exiting"

**Solution:**
```bash
# Oracle needs 2-3 minutes to initialize
# Check logs:
docker logs carelock_oracle

# Look for "DATABASE IS READY TO USE"
# If not appearing after 5 minutes, restart:
docker restart carelock_oracle
```

### Issue: "Some tests failed"

**Solution:**
1. Check which database failed
2. View that container's logs:
   ```bash
   docker logs <container_name>
   ```
3. Common fixes:
   - Wait longer (Oracle takes time)
   - Restart the specific container
   - Check Oracle PATH is set

---

## 📁 Project Structure

```
CareLock-Sync/
├── backend/
│   ├── cdc/                    # Database adapters
│   ├── sync_daemon.py          # Main synchronization daemon
│   └── requirements.txt        # Python dependencies
├── config/
│   └── sync_config.json        # Sync daemon configuration (created by setup)
├── scripts/
│   ├── ultimate_setup.py       # ✨ NEW: Cross-platform setup
│   ├── test_all_5_databases_final.py  # Comprehensive tests
│   └── [other setup scripts]
├── docker-compose.yml          # All 5 database containers
├── setup_complete.ps1          # ✨ NEW: Windows PowerShell setup
└── setup.ps1                   # ⚠️ Deprecated (old structure)
```

---

## 🎓 For Team Members

### First Time Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/CareLock-Sync.git
   cd CareLock-Sync
   ```

2. **Install Oracle Instant Client** (see Prerequisites section)

3. **Run setup:**
   ```powershell
   # Windows:
   .\setup_complete.ps1
   
   # macOS/Linux:
   python scripts/ultimate_setup.py
   ```

4. **Verify:**
   ```bash
   python scripts/test_all_5_databases_final.py
   ```

5. **Start developing!**

### Daily Development

```bash
# Start containers (if stopped)
docker-compose up -d

# Set Oracle PATH
$env:PATH = "C:\oracle\instantclient_23_0;$env:PATH"  # Windows
export PATH="/usr/local/instantclient_19_8:$PATH"      # macOS/Linux

# Run your code
python your_script.py
```

---

## 📖 Additional Documentation

- **Manual Setup Guide:** See original guide for step-by-step manual setup
- **API Documentation:** Check `backend/` for API details
- **Database Schemas:** See `scripts/setup_*.py` for schema definitions

---

## 🚀 Summary

**Quick Start:**
```powershell
# Windows:
.\setup_complete.ps1

# All platforms:
python scripts/ultimate_setup.py
```

**Test:**
```bash
python scripts/test_all_5_databases_final.py
```

**Run Daemon:**
```bash
python backend/sync_daemon.py
```

**You're done!** 🎉

---

**Questions?** Check the troubleshooting section or ask your team members!
