from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, create_engine, Session
from typing import Annotated


db_name = "usuarios.sqlite3"
db_url = f"sqlite:///{db_name}"

engine = create_engine(db_url, echo=True)

def create_tables(app:FastAPI):
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

