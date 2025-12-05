from fastapi import APIRouter, HTTPException, Query
from database import SessionDep
from models import (
    Jugador, JugadorCreate, JugadorUpdate, Estados,
    JugadorConEstadisticas, Estadistica
)
from typing import List
from sqlmodel import select, func

router = APIRouter(tags=["Jugador"], prefix="/jugador")


@router.post("/", response_model=Jugador, status_code=201)
def create_jugador(new_jugador: JugadorCreate, session: SessionDep):
    """Crear un nuevo jugador"""
    # Verificar si el número ya existe
    existing = session.exec(
        select(Jugador).where(Jugador.numero == new_jugador.numero)
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"El número {new_jugador.numero} ya está asignado a otro jugador"
        )

    jugador = Jugador.model_validate(new_jugador)
    session.add(jugador)
    session.commit()
    session.refresh(jugador)
    return jugador


@router.get("/", response_model=List[Jugador])
def read_jugadores(
        estado: Estados = Query(default=None),
        posicion: str = Query(default=None),
        session: SessionDep = None
):
    """Obtener todos los jugadores con filtros opcionales"""
    query = select(Jugador)

    if estado:
        query = query.where(Jugador.estado == estado)

    if posicion:
        query = query.where(Jugador.posicion == posicion)

    jugadores = session.exec(query).all()
    return jugadores


@router.get("/{jugador_id}", response_model=Jugador)
def read_jugador(jugador_id: int, session: SessionDep):
    """Obtener un jugador por ID"""
    jugador = session.get(Jugador, jugador_id)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return jugador


@router.get("/{jugador_id}/estadisticas", response_model=JugadorConEstadisticas)
def read_jugador_estadisticas(jugador_id: int, session: SessionDep):
    """Obtener estadísticas completas de un jugador"""
    jugador = session.get(Jugador, jugador_id)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # Obtener todas las estadísticas del jugador
    estadisticas = session.exec(
        select(Estadistica).where(Estadistica.jugador_id == jugador_id)
    ).all()

    # Calcular totales y promedios
    total_partidos = len(estadisticas)
    total_minutos = sum(est.minutos_jugados for est in estadisticas)
    total_goles = sum(est.goles for est in estadisticas)
    total_asistencias = sum(est.asistencias for est in estadisticas)
    total_amarillas = sum(est.tarjetas_amarillas for est in estadisticas)
    total_rojas = sum(est.tarjetas_rojas for est in estadisticas)

    promedio_minutos = total_minutos / total_partidos if total_partidos > 0 else 0
    eficiencia = (total_goles / total_minutos * 90) if total_minutos > 0 else 0

    return JugadorConEstadisticas(
        **jugador.model_dump(),
        total_partidos=total_partidos,
        total_minutos=total_minutos,
        total_goles=total_goles,
        total_asistencias=total_asistencias,
        total_tarjetas_amarillas=total_amarillas,
        total_tarjetas_rojas=total_rojas,
        promedio_minutos=round(promedio_minutos, 2),
        eficiencia_goleadora=round(eficiencia, 3)
    )


@router.patch("/{jugador_id}", response_model=Jugador)
def update_jugador(
        jugador_id: int,
        jugador_update: JugadorUpdate,
        session: SessionDep
):
    """Actualizar un jugador existente"""
    jugador = session.get(Jugador, jugador_id)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # Actualizar solo los campos proporcionados
    update_data = jugador_update.model_dump(exclude_unset=True)

    # Verificar número único si se está actualizando
    if "numero" in update_data:
        existing = session.exec(
            select(Jugador).where(
                Jugador.numero == update_data["numero"],
                Jugador.id != jugador_id
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"El número {update_data['numero']} ya está asignado"
            )

    for key, value in update_data.items():
        setattr(jugador, key, value)

    session.add(jugador)
    session.commit()
    session.refresh(jugador)
    return jugador


@router.delete("/{jugador_id}")
def delete_jugador(jugador_id: int, session: SessionDep):
    """Eliminar un jugador"""
    jugador = session.get(Jugador, jugador_id)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # Verificar si tiene estadísticas asociadas
    estadisticas = session.exec(
        select(Estadistica).where(Estadistica.jugador_id == jugador_id)
    ).first()

    if estadisticas:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar un jugador con estadísticas registradas"
        )

    session.delete(jugador)
    session.commit()
    return {"ok": True, "detail": "Jugador eliminado exitosamente"}


@router.post("/{jugador_id}/reducir-suspension")
def reducir_suspension(jugador_id: int, session: SessionDep):
    """Reducir en 1 los partidos de suspensión restantes"""
    jugador = session.get(Jugador, jugador_id)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    if jugador.partidos_suspension_restantes > 0:
        jugador.partidos_suspension_restantes -= 1

        # Si ya no tiene suspensión y estaba suspendido, cambiar a activo
        if jugador.partidos_suspension_restantes == 0 and jugador.estado == Estados.SUSPENDIDO:
            jugador.estado = Estados.ACTIVO

        session.add(jugador)
        session.commit()
        session.refresh(jugador)

    return {
        "ok": True,
        "partidos_restantes": jugador.partidos_suspension_restantes,
        "estado": jugador.estado
    }