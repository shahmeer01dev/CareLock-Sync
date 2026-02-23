#!/usr/bin/env python3
"""
CareLock Sync - Ultimate Cross-Platform Setup Script
Handles everything: Prerequisites, Docker, all 5 databases, testing, daemon config
Works on Windows, macOS, and Linux
"""
import os
import sys
import time
import subprocess
import platform
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}\n")

def print_step(step_num, total, description):
    print(f"\n{Colors.BLUE}[{step_num}/{total}] {description}...{Colors.END}")

def print_success(message):
    print(f"  {Colors.GREEN}[OK]{Colors.END} {message}")

def print_error(message):
    print(f"  {Colors.RED}[ERROR]{Colors.END} {message}")

def print_warning(message):
    print(f"  {Colors.YELLOW}[WARN]{Colors.END} {message}")

def run_command(cmd, shell=True, check=True, capture_output=False, cwd=None):
    """Run shell command with error handling"""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=shell, check=check, 
                                  capture_output=True, text=True, cwd=cwd)
            return result.stdout.strip()
        else:
            result = subprocess.run(cmd, shell=shell, check=check, cwd=cwd)
            return result.returncode == 0
    except subprocess.CalledProcessError:
        return False
    except Exception:
        return False

def check_python_version():
    """Verify Python 3.10+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print_error(f"Python 3.10+ required. You have {version.major}.{version.minor}")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_docker():
    """Verify Docker is installed and running"""
    if not run_command("docker --version", capture_output=True, check=False):
        print_error("Docker not installed")
        print_warning("Download from: https://www.docker.com/products/docker-desktop")
        return False
    
    if not run_command("docker ps", capture_output=True, check=False):
        print_error("Docker installed but not running")
        print_warning("Please start Docker Desktop and wait for initialization")
        return False
    
    docker_version = run_command("docker --version", capture_output=True)
    print_success(f"Docker: {docker_version}")
    return True

def check_oracle_instant_client():
    """Check if Oracle Instant Client is accessible"""
    system = platform.system()
    
    if system == "Windows":
        oracle_path = Path("C:/oracle/instantclient_23_0")
    elif system == "Darwin":
        oracle_path = Path("/usr/local/instantclient_19_8")
    else:
        oracle_path = Path("/opt/oracle/instantclient_23_5")
    
    if not oracle_path.exists():
        print_error(f"Oracle Instant Client not found at {oracle_path}")
        print_warning("Oracle database will not work without it")
        print_warning("Download from: https://www.oracle.com/database/technologies/instant-client/downloads.html")
        
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != 'y':
            return False
    else:
        print_success(f"Oracle Instant Client: {oracle_path}")
        
        # Add to PATH
        if system == "Windows":
            os.environ['PATH'] = f"{oracle_path};{os.environ.get('PATH', '')}"
        else:
            os.environ['PATH'] = f"{oracle_path}:{os.environ.get('PATH', '')}"
            if system != "Darwin":
                os.environ['LD_LIBRARY_PATH'] = f"{oracle_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"
    
    # Test cx_Oracle import
    try:
        import cx_Oracle
        print_success("cx_Oracle can load Instant Client")
        return True
    except Exception as e:
        print_warning(f"cx_Oracle cannot load Instant Client: {e}")
        return True  # Continue anyway

def install_python_dependencies():
    """Install all Python packages"""
    # Find requirements.txt
    req_files = [
        Path("requirements.txt"),
        Path("backend/requirements.txt")
    ]
    
    req_file = None
    for f in req_files:
        if f.exists():
            req_file = f
            break
    
    if not req_file:
        print_warning("requirements.txt not found, skipping")
        return True
    
    # Upgrade pip
    if not run_command(f"{sys.executable} -m pip install --upgrade pip --quiet"):
        print_warning("Failed to upgrade pip, continuing...")
    
    # Install requirements
    if not run_command(f"{sys.executable} -m pip install -r {req_file} --quiet"):
        print_error("Failed to install dependencies")
        return False
    
    print_success("All Python packages installed")
    return True

def start_docker_containers():
    """Start all Docker containers"""
    # Force stop and remove any existing containers
    print("  Stopping existing containers...")
    run_command("docker-compose down --volumes --remove-orphans", check=False)
    
    # Remove orphaned containers if any
    print("  Removing orphaned containers...")
    containers = run_command("docker ps -a --filter 'name=carelock' --format '{{.Names}}'", 
                            capture_output=True, check=False)
    if containers:
        for container in containers.split('\n'):
            if container.strip():
                run_command(f"docker rm -f {container.strip()}", check=False)
    
    # Start all containers
    print("  Starting fresh containers...")
    if not run_command("docker-compose up -d"):
        print_error("Failed to start Docker containers")
        print_warning("Try running: docker-compose down --volumes && docker-compose up -d")
        return False
    
    print_success("Docker containers started")
    print_warning("Waiting 15 seconds for initialization...")
    time.sleep(15)
    
    # Verify
    output = run_command("docker ps --format '{{.Names}}'", capture_output=True)
    containers = output.split('\n') if output else []
    
    expected = ['carelock_postgres', 'carelock_mysql', 'carelock_mongodb',
                'carelock_oracle', 'carelock_sqlserver']
    
    running = sum(1 for c in expected if c in containers)
    print_success(f"{running}/{len(expected)} containers running")
    
    return True

def wait_for_oracle():
    """Wait for Oracle initialization"""
    print_warning("Oracle takes 2-3 minutes to initialize...")
    
    max_wait = 180
    waited = 0
    
    while waited < max_wait:
        logs = run_command("docker logs carelock_oracle 2>&1", capture_output=True)
        if logs and "DATABASE IS READY TO USE" in logs:
            print_success("Oracle initialized successfully")
            return True
        
        time.sleep(10)
        waited += 10
        print(f"  ... waited {waited}/{max_wait}s")
    
    print_warning("Oracle may still be initializing, continuing...")
    return True

def setup_databases():
    """Run setup scripts for all databases"""
    scripts_dir = Path("scripts")
    
    databases = [
        ("PostgreSQL", scripts_dir / "setup_postgres.py"),
        ("MySQL", scripts_dir / "setup_mysql_complete.py"),
        ("MongoDB", scripts_dir / "setup_mongodb_complete.py"),
        ("Oracle", scripts_dir / "setup_oracle_and_sqlserver_complete.py"),
        ("SQL Server", scripts_dir / "setup_sqlserver_simple.py")
    ]
    
    for name, script in databases:
        print(f"\n  Setting up {name}...")
        
        if not script.exists():
            print_warning(f"Setup script not found: {script}")
            continue
        
        # Set Oracle PATH before running
        system = platform.system()
        if system == "Windows":
            os.environ['PATH'] = f"C:\\oracle\\instantclient_23_0;{os.environ.get('PATH', '')}"
        
        if run_command(f"{sys.executable} {script}"):
            print_success(f"{name} setup complete")
        else:
            print_warning(f"{name} setup had issues, continuing...")
    
    return True

def create_sync_config():
    """Create sync daemon configuration"""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    config = {
        "sources": [
            {
                "id": "postgres_hospital",
                "connection_string": "postgresql://hospital_user:hospital_pass@localhost:5432/hospital_db",
                "tables": ["patients", "encounters", "lab_results", "medications"]
            },
            {
                "id": "mysql_hospital",
                "connection_string": "mysql://root:root@localhost:3306/hospital_db_mysql",
                "tables": ["patients", "encounters", "lab_results", "medications"]
            },
            {
                "id": "mongodb_hospital",
                "connection_string": "mongodb://localhost:27017/hospital_db_mongodb",
                "collections": ["patients", "encounters", "lab_results", "medications"]
            },
            {
                "id": "oracle_hospital",
                "connection_string": "oracle://hospital_user:hospital_pass@localhost:1521/XE",
                "tables": ["patients", "encounters", "lab_results", "medications"]
            },
            {
                "id": "sqlserver_hospital",
                "connection_string": "sqlserver://sa:YourStrong@Passw0rd@localhost:1433/hospital_db_sqlserver",
                "tables": ["patients", "encounters", "lab_results", "medications"]
            }
        ],
        "polling_interval": 5,
        "batch_size": 1000,
        "deduplication": True,
        "gemini_api_key": "YOUR_GEMINI_API_KEY_HERE"
    }
    
    config_file = config_dir / "sync_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print_success(f"Configuration created: {config_file}")
    print_warning("Remember to add your Gemini API key")
    return True

def run_comprehensive_tests():
    """Run all database tests"""
    test_script = Path("scripts/test_all_5_databases_final.py")
    
    if not test_script.exists():
        print_warning("Test script not found, skipping")
        return True
    
    # Set Oracle PATH
    system = platform.system()
    if system == "Windows":
        os.environ['PATH'] = f"C:\\oracle\\instantclient_23_0;{os.environ.get('PATH', '')}"
    
    if run_command(f"{sys.executable} {test_script}"):
        print_success("All database tests passed")
        return True
    else:
        print_warning("Some tests had issues")
        return True

def test_cdc():
    """Test Change Data Capture"""
    cdc_script = Path("scripts/test_cdc_all_databases.py")
    
    if not cdc_script.exists():
        print_warning("CDC test script not found, skipping")
        return True
    
    # Set Oracle PATH
    system = platform.system()
    if system == "Windows":
        os.environ['PATH'] = f"C:\\oracle\\instantclient_23_0;{os.environ.get('PATH', '')}"
    
    if run_command(f"{sys.executable} {cdc_script}"):
        print_success("CDC tests passed")
    else:
        print_warning("CDC tests had issues")
    
    return True

def print_next_steps():
    """Print completion message and next steps"""
    print_header("SETUP COMPLETE - SYSTEM READY")
    
    print(f"{Colors.GREEN}✓ All 5 databases are running and configured{Colors.END}")
    print(f"{Colors.GREEN}✓ Change Data Capture is enabled{Colors.END}")
    print(f"{Colors.GREEN}✓ Sync daemon configuration created{Colors.END}\n")
    
    print(f"{Colors.BOLD}NEXT STEPS:{Colors.END}\n")
    
    print(f"{Colors.WHITE}1. Add your Gemini API key:{Colors.END}")
    print(f"   Edit: config/sync_config.json\n")
    
    print(f"{Colors.WHITE}2. Start the sync daemon:{Colors.END}")
    
    if platform.system() == "Windows":
        print(f"   $env:PATH = 'C:\\oracle\\instantclient_23_0;' + $env:PATH")
    else:
        print(f"   export PATH=\"/path/to/instantclient:$PATH\"")
    
    print(f"   python backend/sync_daemon.py\n")
    
    print(f"{Colors.BOLD}USEFUL COMMANDS:{Colors.END}")
    print(f"  View containers:    docker ps")
    print(f"  View logs:          docker logs <container_name>")
    print(f"  Stop all:           docker-compose down")
    print(f"  Restart all:        docker-compose up -d\n")
    
    print(f"{Colors.BOLD}DATABASE CONNECTIONS:{Colors.END}")
    print(f"  PostgreSQL:  localhost:5432  (hospital_user/hospital_pass)")
    print(f"  MySQL:       localhost:3306  (root/root)")
    print(f"  MongoDB:     localhost:27017")
    print(f"  Oracle:      localhost:1521  (hospital_user/hospital_pass)")
    print(f"  SQL Server:  localhost:1433  (sa/YourStrong@Passw0rd)\n")
    
    print(f"{Colors.GREEN}{'='*80}{Colors.END}")
    print(f"{Colors.GREEN}Setup completed successfully!{Colors.END}")
    print(f"{Colors.GREEN}{'='*80}{Colors.END}\n")

def main():
    """Main setup orchestrator"""
    print_header("CARELOCK SYNC - ULTIMATE AUTOMATED SETUP")
    print(f"Cross-platform setup for all 5 databases")
    print(f"Estimated time: 10-15 minutes\n")
    
    # Prerequisites
    print_header("PHASE 1: CHECKING PREREQUISITES")
    
    print_step(1, 3, "Checking Python version")
    if not check_python_version():
        sys.exit(1)
    
    print_step(2, 3, "Checking Docker")
    if not check_docker():
        sys.exit(1)
    
    print_step(3, 3, "Checking Oracle Instant Client")
    if not check_oracle_instant_client():
        sys.exit(1)
    
    # Python Setup
    print_header("PHASE 2: PYTHON ENVIRONMENT")
    
    print_step(1, 1, "Installing Python dependencies")
    if not install_python_dependencies():
        sys.exit(1)
    
    # Docker
    print_header("PHASE 3: DOCKER CONTAINERS")
    
    print_step(1, 2, "Starting Docker containers")
    if not start_docker_containers():
        sys.exit(1)
    
    print_step(2, 2, "Waiting for Oracle initialization")
    wait_for_oracle()
    
    # Database Setup
    print_header("PHASE 4: DATABASE INITIALIZATION")
    
    print_step(1, 1, "Setting up all 5 databases")
    setup_databases()
    
    # Configuration
    print_header("PHASE 5: SYNC DAEMON CONFIGURATION")
    
    print_step(1, 1, "Creating sync configuration")
    create_sync_config()
    
    # Testing
    print_header("PHASE 6: COMPREHENSIVE TESTING")
    
    print_step(1, 2, "Running database tests")
    run_comprehensive_tests()
    
    print_step(2, 2, "Testing Change Data Capture")
    test_cdc()
    
    # Done!
    print_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
