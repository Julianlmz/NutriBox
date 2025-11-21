import os
from dotenv import load_dotenv
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import Annotated
from fastapi import Depends

# Carga las variables del archivo .env
load_dotenv()

# Obtener URL de base de datos
DATABASE_URL = os.getenv("POSTGRESQL_ADDON_URI")

# Lógica para ajustar la URL
if not DATABASE_URL:
    # Usamos aiosqlite para local (es la versión async de sqlite)
    print("ADVERTENCIA: No se encontró POSTGRESQL_ADDON_URI, usando SQLite local")
    DATABASE_URL = "sqlite+aiosqlite:///./NutriBox.db"
else:
    # Corrección para SQLAlchemy (requiere postgresql+asyncpg://)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# 1. Crear el motor ASÍNCRONO
engine = create_async_engine(DATABASE_URL, echo=True)

# 2. Crear la fábrica de sesiones ASÍNCRONAS
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 3. Función para crear tablas (ahora es async)
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# 4. Dependencia para obtener la sesión
async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

# Definir el tipo para inyección de dependencias
SessionDep = Annotated[AsyncSession, Depends(get_session)]