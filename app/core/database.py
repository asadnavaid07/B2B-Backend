from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker,declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL=os.getenv("DATABASE_URL")


engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal=sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base=declarative_base()


async def init_db():
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session  # Yield the session, not None
        finally:
            await session.close()  # Ensure session is closed
