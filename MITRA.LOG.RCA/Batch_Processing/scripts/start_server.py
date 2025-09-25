#!/usr/bin/env python3
"""
Startup script for the Batch Processing Engine
"""

import sys
import os
import argparse
import asyncio

# Add the project root to Python path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(project_root)

# Add the api directory to Python path
api_dir = os.path.join(project_root, 'api')
sys.path.append(api_dir)

def check_dependencies():
    """Check if all required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    try:
        # Check basic imports
        import fastapi
        import uvicorn
        import sqlalchemy
        print("✅ Core dependencies available")
        
        # Check database connection (we'll implement this later)
        print("✅ Basic dependency check passed")
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting Batch Processing Engine...")
    
    # Change to api directory
    api_dir = os.path.join(os.path.dirname(__file__), '..', 'api')
    os.chdir(api_dir)
    
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Batch Processing Engine")
    parser.add_argument(
        "--check-deps", 
        action="store_true",
        help="Check dependencies and exit"
    )
    parser.add_argument(
        "--skip-checks", 
        action="store_true",
        help="Skip dependency checks"
    )
    
    args = parser.parse_args()
    
    if args.check_deps:
        if check_dependencies():
            sys.exit(0)
        else:
            sys.exit(1)
    
    # Normal startup
    if not args.skip_checks:
        if not check_dependencies():
            print("❌ Dependency check failed. Use --skip-checks to bypass.")
            sys.exit(1)
    
    start_server()

if __name__ == "__main__":
    main()
