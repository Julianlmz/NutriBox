from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from typing import List, Optional
from models import Pedido, PedidoProducto, Producto
from db import SessionDep

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

@router.post("/", response_model=Pedido, status_code=status.HTTP_201_CREATED)
async def crear_pedido(pedido: Pedido, session: SessionDep):
    session.add(pedido)
    session.commit()
    session.refresh(pedido)
    return pedido

@router.post("/{pedido_id}/productos/{producto_id}", status_code=status.HTTP_201_CREATED)
async def agregar_producto_a_pedido(pedido_id: int, producto_id: int, cantidad: Optional[int] = 1, session: SessionDep = None):
    # crear asociación PedidoProducto
    pedido = session.get(Pedido, pedido_id)
    producto = session.get(Producto, producto_id)
    if not pedido or not producto:
        raise HTTPException(status_code=404, detail="Pedido o Producto no encontrado")
    assoc = PedidoProducto(pedido_id=pedido_id, producto_id=producto_id, cantidad=cantidad)
    session.add(assoc)
    session.commit()
    return {"message": "Producto agregado al pedido"}

@router.get("/", response_model=List[Pedido])
async def listar_pedidos(session: SessionDep):
    pedidos = session.exec(select(Pedido)).all()
    return pedidos
