#!/usr/bin/env python3
"""
Entry point for running the Job Matching App
Respects PORT environment variable for Cloud Run compatibility
"""

import os
import uvicorn
from main import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"🚀 Starting Job Matching App on {host}:{port}")
    print(f"📊 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🔧 Maintenance Mode: {os.getenv('MAINTENANCE_MODE', 'false')}")
    
    uvicorn.run(
        app=app,
        host=host,
        port=port,
        log_level="info"
    ) 