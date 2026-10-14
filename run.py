# run.py - ResearchMate AI Server Launcher & Public Deployment
import sys
import os
import uvicorn
import subprocess
import time

from config import HOST, PORT

def main():
    print("=" * 65)
    print("  RESEARCHMATE AI — ACADEMIC RESEARCH & PUBLICATION SUITE")
    print(f"  Starting local server on http://localhost:{PORT}")
    print("=" * 65)
    
    # Run uvicorn server
    uvicorn.run("app:app", host=HOST, port=PORT, reload=False)

if __name__ == "__main__":
    main()
