"""
CareLock Sync - Environment Verification Script
This script verifies that all components of the development environment are working correctly.
"""

import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def check_command(cmd, description):
    """Check if a command executes successfully"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"[OK] {description}: PASSED")
            return True
        else:
            print(f"[FAIL] {description}: FAILED")
            print(f"       Error: {result.stderr[:100]}")
            return False
    except Exception as e:
        print(f"[ERROR] {description}: {str(e)[:100]}")
        return False


def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"[OK] {description}: EXISTS")
        return True
    else:
        print(f"[FAIL] {description}: NOT FOUND")
        return False


def check_python_package(package_name):
    """Check if a Python package is installed"""
    try:
        __import__(package_name)
        print(f"[OK] {package_name}: Installed")
        return True
    except ImportError:
        print(f"[FAIL] {package_name}: Not installed")
        return False


def main():
    print_header("CareLock Sync - Environment Verification")
    
    checks_passed = []
    
    # Check System Tools
    print_header("1. System Tools")
    checks_passed.append(check_command("python --version", "Python"))
    checks_passed.append(check_command("pip --version", "pip"))
    checks_passed.append(check_command("node --version", "Node.js"))
    checks_passed.append(check_command("npm --version", "npm"))
    checks_passed.append(check_command("git --version", "Git"))
    checks_passed.append(check_command("docker --version", "Docker"))
    
    # Check Project Structure
    print_header("2. Project Structure")
    checks_passed.append(check_file_exists("backend/requirements.txt", "requirements.txt"))
    checks_passed.append(check_file_exists("backend/common/config.py", "config.py"))
    checks_passed.append(check_file_exists("docker/docker-compose.dev.yml", "docker-compose.yml"))
    checks_passed.append(check_file_exists("config/.env", ".env file"))
    checks_passed.append(check_file_exists(".gitignore", ".gitignore"))
    checks_passed.append(check_file_exists("README.md", "README.md"))
    
    # Check Python Packages
    print_header("3. Python Packages")
    critical_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'sqlalchemy',
        'psycopg2',
        'pandas',
        'numpy',
        'langchain',
        'openai',
        'chromadb',
        'pytest'
    ]
    
    for package in critical_packages:
        checks_passed.append(check_python_package(package))
    
    # Check Docker Containers
    print_header("4. Docker Containers")
    checks_passed.append(check_command(
        'docker ps --filter "name=carelock-hospital-db" --format "{{.Status}}" | findstr "Up"',
        "Hospital Database Container"
    ))
    checks_passed.append(check_command(
        'docker ps --filter "name=carelock-shared-db" --format "{{.Status}}" | findstr "Up"',
        "Shared Database Container"
    ))
    checks_passed.append(check_command(
        'docker ps --filter "name=carelock-pgadmin" --format "{{.Status}}" | findstr "Up"',
        "pgAdmin Container"
    ))
    
    # Check Configuration
    print_header("5. Configuration")
    try:
        from backend.common.config import settings
        print(f"[OK] Configuration loads successfully")
        print(f"     App Name: {settings.APP_NAME}")
        print(f"     Environment: {settings.APP_ENV}")
        checks_passed.append(True)
    except Exception as e:
        print(f"[FAIL] Configuration failed to load: {str(e)[:100]}")
        checks_passed.append(False)
    
    # Summary
    print_header("Summary")
    total_checks = len(checks_passed)
    passed_checks = sum(checks_passed)
    failed_checks = total_checks - passed_checks
    
    print(f"\nTotal Checks: {total_checks}")
    print(f"PASSED: {passed_checks}")
    print(f"FAILED: {failed_checks}")
    
    percentage = (passed_checks / total_checks) * 100
    print(f"\nSuccess Rate: {percentage:.1f}%")
    
    if percentage == 100:
        print("\n*** ALL CHECKS PASSED! ***")
        print("Environment is ready for development!")
        print("\nNext Steps:")
        print("1. Access pgAdmin at: http://localhost:5050")
        print("   Login: admin@carelock.com / admin123")
        print("2. Start Phase 1, Step 2: Database Infrastructure Setup")
        return 0
    elif percentage >= 90:
        print("\n*** Environment is mostly ready! ***")
        print("Fix the failed checks above.")
        return 0
    else:
        print("\n*** Multiple issues detected ***")
        print("Please review the failed checks above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
