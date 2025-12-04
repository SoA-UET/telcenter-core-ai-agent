"""
Telcenter Core - AI Agent

Main entry point for the AI Agent microservice.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .server import main

if __name__ == "__main__":
    main()
