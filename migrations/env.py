import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# Import Base and models
from app.core.database import Base
from app.models.user import User

# Load .env variables
load_dotenv()

# Alembic Config object
config = context.config

# Logging configuration
fileConfig(config.config_file_name)

# Read and patch DATABASE_URL
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL environment variable is not set")

# Convert asyncpg to psycopg2 for Alembic compatibility
if "asyncpg" in database_url:
    database_url = database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")

# Update the config so engine_from_config gets the right URL
config.set_main_option("sqlalchemy.url", database_url)

# Metadata for migrations
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
