from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv
load_dotenv()

Base = declarative_base()

DATABASE_URL = os.getenv("DATABASE_URL")


engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Enable SQL logging for debugging
    pool_size=20,  # Max number of connections in pool
    max_overflow=10,  # Allow extra connections if pool is full
    pool_timeout=30,  # Wait 30 seconds for a connection
    pool_recycle=1800,  # Recycle connections after 30 minutes
)

# Async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

        
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()