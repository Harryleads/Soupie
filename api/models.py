"""
Updated models.py to use JSON database instead of SQLAlchemy
"""

from .json_db import db, get_db

# Re-export the database functions for compatibility
create_tables = db.init_tables
get_db = get_db

# Database models are now handled by the JSON database system
# The JSON database provides the same functionality as the original SQLAlchemy models