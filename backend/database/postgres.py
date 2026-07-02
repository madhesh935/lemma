"""
AEGIS-OS Database Layer — PostgreSQL connection manager (SQLAlchemy async).
Gracefully degrades if asyncpg is not installed.
"""
import logging
logger = logging.getLogger("aegis.db")

try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.orm import DeclarativeBase

    from config import DATABASE_URL

    # ─── Engine ───────────────────────────────────────────────────────────────
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    class Base(DeclarativeBase):
        pass

    # ─── Dependency ───────────────────────────────────────────────────────────
    async def get_db():
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # ─── Init tables ──────────────────────────────────────────────────────────
    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("PostgreSQL tables created.")

except ModuleNotFoundError as e:
    logger.warning(f"PostgreSQL unavailable (asyncpg/sqlalchemy not installed): {e}")

    # ─── Stubs so imports don't fail ──────────────────────────────────────────
    engine = None
    AsyncSessionLocal = None

    class Base:
        metadata = type("M", (), {"create_all": lambda *a, **k: None})()

    async def get_db():
        yield None

    async def init_db():
        logger.warning("PostgreSQL init skipped — asyncpg not installed.")
