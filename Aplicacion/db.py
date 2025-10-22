from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, create_engine, Session
from typing import Annotated

db_name = "NutriBox.sqlite3"
db_url = f"sqlite:///{db_name}"

engine = create_engine(db_url, echo=True)


def create_tables(app: FastAPI):
    """Crea todas las tablas en la base de datos"""
    # Importar modelos aquí para asegurar que estén registrados
    from Datos.models import (
        Usuario, Lonchera, Perfil, Alimento, Restriccion, RestriccionAlimento,
        LoncheraAlimento, Producto, Pedido, PedidoProducto,
        MovimientoInventario, HistorialEliminacion
    )

    print("📊 Creando tablas en la base de datos...")
    SQLModel.metadata.create_all(engine)
    print(f"✅ {len(SQLModel.metadata.sorted_tables)} tablas creadas")


def get_session() -> Session:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
