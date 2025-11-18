import os
from sqlmodel import Session, create_engine, SQLModel
from fastapi import Depends
from typing import Annotated

DATABASE_URL = os.environ.get("POSTGRESQL_ADDON_URI")
connect_args = {} # Se inicializa vacío

if DATABASE_URL is None:
    # MODO DESARROLLO (SQLite)
    print("MODO DESARROLLO: Conectando a base de datos SQLite local (NutriBox.db)")
    DATABASE_URL = "sqlite:///./NutriBox.db"
    connect_args = {"check_same_thread": False}
else:
    # MODO PRODUCCIÓN (Azure PostgreSQL)
    print("MODO PRODUCCIÓN: Conectando a base de datos en Azure")

    # Asegura que se use el driver 'postgresql://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # ¡Importante! Azure requiere conexiones SSL
    connect_args = {"sslmode": "require"}

# Crea el 'engine' con los argumentos de conexión correctos (ya sea para SQLite o Azure)
engine = create_engine(DATABASE_URL, connect_args=connect_args)

def create_tables():
    SQLModel.metadata.create_all(engine, checkfirst=True)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]