"""
Database connection management with optimization for SQLite.

Optimizations applied:
1. WAL (Write-Ahead Logging) mode for better concurrency
2. Increased cache size for better read performance
3. Connection pooling with proper lifecycle management
4. PRAGMA optimizations for SQLite
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import event, text
from ..core.config import settings
from ..core.logging import logger
from ..models.trajectory import Base


# Create async engine with optimizations
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    # Use StaticPool for SQLite to maintain single connection
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
    }
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Set SQLite PRAGMAs for optimization.

    Optimizations:
    - journal_mode=WAL: Better concurrency
    - synchronous=NORMAL: Balance between safety and speed
    - cache_size: More memory for caching (negative = KB)
    - temp_store=MEMORY: Use memory for temp tables
    - mmap_size: Memory-mapped I/O for faster reads
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA mmap_size=268435456")  # 256MB mmap
    cursor.execute("PRAGMA page_size=4096")
    cursor.close()
    logger.info("SQLite PRAGMAs applied for optimization")


async def init_db():
    """Initialize database with all tables and indexes."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully")


async def get_db() -> AsyncSession:
    """
    Dependency function to get database session.

    Usage in FastAPI endpoints:
        @app.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db():
    """Close database connections gracefully."""
    await engine.dispose()
    logger.info("Database connections closed")
