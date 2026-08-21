"""
Developer & Test Environment Convenience Entrypoint.
Delegates to backend/scripts/seed_demo_data.py to seed the local database.
"""

import sys
import os

# Add backend and backend/scripts to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend", "scripts")))

from seed_demo_data import seed_demo_data

# Alias for backwards compatibility with existing test runners
seed_database = seed_demo_data

if __name__ == "__main__":
    seed_demo_data()
