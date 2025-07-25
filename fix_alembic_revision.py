from sqlalchemy import create_engine, text

# Replace this with your actual database URL
DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_FDsIiOelf70X@ep-dry-boat-a1j807tj-pooler.ap-southeast-1.aws.neon.tech/neondb"

# Replace with the revision ID in your migrations/versions/
correct_revision = "29f3630f566a"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    conn.execute(text("UPDATE alembic_version SET version_num = :rev"), {"rev": correct_revision})
    conn.commit()

print("✅ Alembic version updated to:", correct_revision)
