from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from typing import List, Optional
from Datos.models import (
    MovimientoInventario, MovimientoInventarioCreate,
    Alimento, TipoMovimiento
)
from Aplicacion.db import SessionDep
from datetime import datetime, date

router = APIRouter(prefix="/inventario", tags=["Inventario"])


@router.post("/movimientos", response_model=MovimientoInventario, status_code=status.HTTP_201_CREATED)
async def registrar_movimiento(data: MovimientoInventarioCreate, session: SessionDep):
    alimento = session.get(Alimento, data.alimento_id)
    if not alimento or not alimento.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alimento no encontrado"
        )

    stock_anterior = alimento.stock_actual

    if data.tipo_movimiento == TipoMovimiento.ENTRADA:
        stock_nuevo = stock_anterior + abs(data.cantidad)
    elif data.tipo_movimiento == TipoMovimiento.SALIDA:
        if stock_anterior < abs(data.cantidad):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente. Disponible: {stock_anterior}"
            )
        stock_nuevo = stock_anterior - abs(data.cantidad)
    else:
        stock_nuevo = data.cantidad

    if stock_nuevo < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El stock no puede ser negativo"
        )

    movimiento = MovimientoInventario(
        **data.model_dump(),
        stock_anterior=stock_anterior,
        stock_nuevo=stock_nuevo
    )

    alimento.stock_actual = stock_nuevo
    session.add(movimiento)
    session.add(alimento)
    session.commit()
    session.refresh(movimiento)

    return movimiento


@router.get("/movimientos", response_model=List[MovimientoInventario])
async def listar_movimientos(
        session: SessionDep,
        alimento_id: Optional[int] = None,
        tipo_movimiento: Optional[TipoMovimiento] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
):
    query = select(MovimientoInventario)

    if alimento_id:
        query = query.where(MovimientoInventario.alimento_id == alimento_id)

    if tipo_movimiento:
        query = query.where(MovimientoInventario.tipo_movimiento == tipo_movimiento)

    if fecha_desde:
        fecha_desde_dt = datetime.combine(fecha_desde, datetime.min.time())
        query = query.where(MovimientoInventario.fecha >= fecha_desde_dt)

    if fecha_hasta:
        fecha_hasta_dt = datetime.combine(fecha_hasta, datetime.max.time())
        query = query.where(MovimientoInventario.fecha <= fecha_hasta_dt)

    query = query.order_by(MovimientoInventario.fecha.desc())
    movimientos = session.exec(query).all()
    return movimientos


@router.get("/movimientos/{movimiento_id}", response_model=MovimientoInventario)
async def obtener_movimiento(movimiento_id: int, session: SessionDep):
    movimiento = session.get(MovimientoInventario, movimiento_id)
    if not movimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimiento no encontrado"
        )
    return movimiento


@router.get("/stock-bajo")
async def alimentos_stock_bajo(session: SessionDep, limite: int = 10):
    alimentos = session.exec(
        select(Alimento).where(
            Alimento.is_active == True,
            Alimento.stock_actual < limite
        )
    ).all()

    return [
        {
            "id": a.id,
            "nombre": a.nombre,
            "categoria": a.categoria,
            "stock_actual": a.stock_actual,
            "precio_unitario": a.precio_unitario
        }
        for a in alimentos
    ]


@router.get("/reporte-inventario")
async def reporte_inventario(session: SessionDep):
    alimentos = session.exec(
        select(Alimento).where(Alimento.is_active == True)
    ).all()

    total_items = len(alimentos)
    valor_total = sum(a.stock_actual * a.precio_unitario for a in alimentos)
    stock_bajo = sum(1 for a in alimentos if a.stock_actual < 10)
    sin_stock = sum(1 for a in alimentos if a.stock_actual == 0)

    return {
        "total_items": total_items,
        "valor_total_inventario": round(valor_total, 2),
        "items_stock_bajo": stock_bajo,
        "items_sin_stock": sin_stock,
        "por_categoria": {
            categoria: {
                "cantidad": len([a for a in alimentos if a.categoria == categoria]),
                "valor": sum(
                    a.stock_actual * a.precio_unitario
                    for a in alimentos if a.categoria == categoria
                )
            }
            for categoria in set(a.categoria for a in alimentos)
        }
    }
