from fastapi import APIRouter, HTTPException
from database import SessionDep
from models import (
    Partido, PartidoCreate, PartidoUpdate,
    PartidoConEstadisticas, Estadistica
)
from typing import List
from sqlmodel import select

router = APIRouter(tags=["Partido"], prefix="/partido")


@router.post("/", response_model=Partido, status_code=201)
def create_partido(new_partido: PartidoCreate, session: SessionDep):
    """Crear un nuevo partido"""
    partido = Partido.model_validate(new_partido)

    # Determinar el resultado automáticamente
    partido.determinar_resultado()

    session.add(partido)
    session.commit()
    session.refresh(partido)
    return partido


@router.get("/", response_model=List[Partido])
def read_partidos(session: SessionDep):
    """Obtener todos los partidos"""
    query = select(Partido).order_by(Partido.fecha.desc())
    partidos = session.exec(query).all()
    return partidos


@router.get("/{partido_id}", response_model=Partido)
def read_partido(partido_id: int, session: SessionDep):
    """Obtener un partido por ID"""
    partido = session.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    return partido


@router.get("/{partido_id}/estadisticas", response_model=PartidoConEstadisticas)
def read_partido_estadisticas(partido_id: int, session: SessionDep):
    """Obtener estadísticas del partido"""
    partido = session.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    # Obtener estadísticas del partido
    estadisticas = session.exec(
        select(Estadistica).where(Estadistica.partido_id == partido_id)
    ).all()

    jugadores_participantes = len(estadisticas)
    total_minutos = sum(est.minutos_jugados for est in estadisticas)

    return PartidoConEstadisticas(
        **partido.model_dump(),
        jugadores_participantes=jugadores_participantes,
        total_minutos_jugados=total_minutos
    )


@router.patch("/{partido_id}", response_model=Partido)
def update_partido(
        partido_id: int,
        partido_update: PartidoUpdate,
        session: SessionDep
):
    """Actualizar un partido existente"""
    partido = session.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    # Actualizar campos
    update_data = partido_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(partido, key, value)

    # Recalcular resultado
    partido.determinar_resultado()

    session.add(partido)
    session.commit()
    session.refresh(partido)
    return partido


@router.delete("/{partido_id}")
def delete_partido(partido_id: int, session: SessionDep):
    """Eliminar un partido"""
    partido = session.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    # Verificar si tiene estadísticas
    estadisticas = session.exec(
        select(Estadistica).where(Estadistica.partido_id == partido_id)
    ).first()

    if estadisticas:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar un partido con estadísticas registradas"
        )

    session.delete(partido)
    session.commit()
    return {"ok": True, "detail": "Partido eliminado exitosamente"}