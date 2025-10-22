from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from typing import List
from models import Producto
from db import SessionDep

router = APIRouter(prefix="/productos", tags=["Productos"])

@router.post("/", response_model=Producto, status_code=status.HTTP_201_CREATED)
async def crear_producto(producto: Producto, session: SessionDep):
    session.add(producto)
    session.commit()
    session.refresh(producto)
    return producto

@router.get("/", response_model=List[Producto])
async def listar_productos(session: SessionDep):
    productos = session.exec(select(Producto)).all()
    return productos

@router.get("/{producto_id}", response_model=Producto)
async def obtener_producto(producto_id: int, session: SessionDep):
    producto = session.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto
