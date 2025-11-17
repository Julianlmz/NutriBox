import os
from sqlmodel import Session, create_engine, SQLModel
from fastapi import Depends
from typing import Annotated

DATABASE_URL = os.environ.get("POSTGRESQL_ADDON_URI")
connect_args = {}

if DATABASE_URL is None:
    print("MODO DESARROLLO: Conectando a base de datos SQLite local (NutriBox.db)")
    DATABASE_URL = "sqlite:///./NutriBox.db"
    connect_args = {"check_same_thread": False}
else:
    print("MODO PRODUCCIÓN: Conectando a base de datos de Clever Cloud")
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, connect_args=connect_args)

def create_tables():
    SQLModel.metadata.create_all(engine, checkfirst=True)


def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]