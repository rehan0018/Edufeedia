"""
Automatic schema migration for Discovery Engine columns and tables.
Ensures existing SQLite / Postgres databases receive all required discovery fields safely.
"""

from sqlalchemy import text
from app.database import engine, Base
import app.models.models

def run_migration():
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        # Check SQLite or Postgres dialect
        dialect_name = engine.dialect.name
        if dialect_name == "sqlite":
            cols = [r[1] for r in conn.execute(text("PRAGMA table_info(content_items)")).fetchall()]
            new_cols = [
                ("source_authority_tier", "VARCHAR DEFAULT 'TIER_B'"),
                ("creator_name", "VARCHAR"),
                ("creator_id", "VARCHAR"),
                ("creator_verified", "BOOLEAN DEFAULT 0"),
                ("organization_name", "VARCHAR"),
                ("organization_verified", "BOOLEAN DEFAULT 0"),
                ("curriculum_alignment_score", "NUMERIC(4, 2)"),
                ("pedagogical_score", "NUMERIC(4, 2)"),
                ("resource_quality_score", "NUMERIC(4, 2)"),
                ("why_recommended", "JSON"),
                ("scoring_breakdown", "JSON")
            ]
            for c_name, c_def in new_cols:
                if c_name not in cols:
                    print(f"Adding column {c_name} to content_items...")
                    conn.execute(text(f"ALTER TABLE content_items ADD COLUMN {c_name} {c_def}"))
            conn.commit()
    print("Schema migration completed successfully.")

if __name__ == "__main__":
    run_migration()
