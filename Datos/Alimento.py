from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from typing import List
from Datos.models import (
    Alimento, AlimentoCreate, MovimientoInventario,
    TipoMovimiento, HistorialEliminacion
)
from Aplicacion.db import SessionDep
import json

router = APIRouter(prefix="/alimentos", tags=["Alimentos"])


@router.post("/", response_model=Alimento, status_code=status.HTTP_201_CREATED)
async def crear_alimento(data: AlimentoCreate, session: SessionDep):
    alimento = Alimento(**data.model_dump(exclude={'stock_inicial'}))
    alimento.stock_actual = data.stock_inicial
    session.add(alimento)
    session.commit()
    session.refresh(alimento)

    if data.stock_inicial > 0:
        movimiento = MovimientoInventario(
            alimento_id=alimento.id,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            cantidad=data.stock_inicial,
            motivo="Stock inicial",
            stock_anterior=0,
            stock_nuevo=data.stock_inicial,
            usuario_id=None
        )
        session.add(movimiento)
        session.commit()

    return alimento


@router.get("/", response_model=List[Alimento])
async def listar_alimentos(
        session: SessionDep,
        incluir_inactivos: bool = False,
        categoria: str = None,
        stock_bajo: bool = False
):
    query = select(Alimento)

    if not incluir_inactivos:
        query = query.where(Alimento.is_active == True)

    if categoria:
        query = query.where(Alimento.categoria == categoria)

    if stock_bajo:
        query = query.where(Alimento.stock_actual < 10)

    alimentos = session.exec(query).all()
    return alimentos


@router.get("/{alimento_id}", response_model=Alimento)
async def obtener_alimento(alimento_id: int, session: SessionDep):
    alimento = session.get(Alimento, alimento_id)
    if not alimento or not alimento.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alimento no encontrado"
        )
    return alimento


@router.put("/{alimento_id}", response_model=Alimento)
async def actualizar_alimento(
        alimento_id: int,
        data: AlimentoCreate,
        session: SessionDep
):
    alimento = session.get(Alimento, alimento_id)
    if not alimento or not alimento.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alimento no encontrado"
        )

    for key, value in data.model_dump(exclude={'stock_inicial'}).items():
        setattr(alimento, key, value)

    session.add(alimento)
    session.commit()
    session.refresh(alimento)
    return alimento


@router.delete("/{alimento_id}", status_code=status.HTTP_200_OK)
async def eliminar_alimento(
        alimento_id: int,
        session: SessionDep,
        motivo: str = None,
        hard_delete: bool = False
):
    alimento = session.get(Alimento, alimento_id)
    if not alimento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alimento no encontrado"
        )

    if hard_delete:
        historial = HistorialEliminacion(
            tabla_nombre="alimento",
            registro_id=alimento.id,
            datos_json=json.dumps(alimento.model_dump(), default=str),
            motivo=motivo or "Eliminación permanente",
            usuario_eliminador_id=None
        )
        session.add(historial)
        session.delete(alimento)
        mensaje = "Alimento eliminado permanentemente"
    else:
        alimento.is_active = False
        session.add(alimento)
        mensaje = "Alimento desactivado correctamente"

    session.commit()
    return {"message": mensaje, "id": alimento_id}


@router.get("/{alimento_id}/restricciones")
async def obtener_restricciones_alimento(alimento_id: int, session: SessionDep):
    alimento = session.get(Alimento, alimento_id)
    if not alimento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alimento no encontrado"
        )

    return [
        {
            "id": r.restriccion.id,
            "nombre": r.restriccion.nombre,
            "descripcion": r.restriccion.descripcion,
            "nivel_severidad": r.restriccion.nivel_severidad
        }
        for r in alimento.restricciones
    ]
