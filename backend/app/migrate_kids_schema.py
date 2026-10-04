import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine, Base
import app.models.models
from sqlalchemy import text

def run_migration():
    print("Creating any newly registered tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created/verified.")

    with engine.connect() as conn:
        # Check users columns
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN parent_pin_hash VARCHAR"))
            conn.commit()
            print("Added parent_pin_hash to users.")
        except Exception as e:
            print(f"parent_pin_hash: {e}")

        # Check content_items columns
        new_cols = [
            ("age_min", "INTEGER DEFAULT 0"),
            ("age_max", "INTEGER DEFAULT 18"),
            ("content_category", "VARCHAR DEFAULT 'STEM'"),
            ("subcategory", "VARCHAR"),
            ("language", "VARCHAR DEFAULT 'en'"),
            ("is_cartoon", "BOOLEAN DEFAULT 0"),
            ("mascot_character", "VARCHAR"),
            ("ai_generated_status", "VARCHAR DEFAULT 'HUMAN_CREATED'"),
            ("human_reviewed", "BOOLEAN DEFAULT 1"),
            ("interactive_payload", "JSON")
        ]
        for col_name, col_type in new_cols:
            try:
                conn.execute(text(f"ALTER TABLE content_items ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"Added {col_name} to content_items.")
            except Exception as e:
                print(f"{col_name}: {e}")

    print("Migration finished successfully.")

if __name__ == "__main__":
    run_migration()
