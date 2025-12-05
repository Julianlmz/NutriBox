from fastapi import APIRouter, HTTPException
from database import SessionDep
from models import (
    Estadistica, EstadisticaCreate, EstadisticaUpdate,
    Jugador, Partido, Estados
)
from typing import List
from sqlmodel import select

router = APIRouter(tags=["Estadistica"], prefix="/estadistica")


@router.post("/", response_model=Estadistica, status_code=201)
def create_estadistica(new_estadistica: EstadisticaCreate, session: SessionDep):
    """
    Crear una nueva estadística para un jugador en un partido.
    Automáticamente calcula suspensiones y actualiza el estado del jugador.
    """
    # Verificar que el jugador existe
    jugador = session.get(Jugador, new_estadistica.jugador_id)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # Verificar que el partido existe
    partido = session.get(Partido, new_estadistica.partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    # Verificar que no exista ya una estadística para este jugador en este partido
    existing = session.exec(
        select(Estadistica).where(
            Estadistica.jugador_id == new_estadistica.jugador_id,
            Estadistica.partido_id == new_estadistica.partido_id
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una estadística para este jugador en este partido"
        )

    # Crear la estadística
    estadistica = Estadistica.model_validate(new_estadistica)
    session.add(estadistica)
    session.flush()  # Para obtener el ID de la estadística

    # Calcular y aplicar suspensión si hay tarjetas
    partidos_suspension = estadistica.calcular_suspension()
    if partidos_suspension > 0:
        jugador.partidos_suspension_restantes += partidos_suspension
        jugador.estado = Estados.SUSPENDIDO
        session.add(jugador)

    session.commit()
    session.refresh(estadistica)

    return estadistica


@router.get("/", response_model=List[Estadistica])
def read_estadisticas(
        jugador_id: int = None,
        partido_id: int = None,
        session: SessionDep = None
):
    """Obtener estadísticas con filtros opcionales"""
    query = select(Estadistica)

    if jugador_id:
        query = query.where(Estadistica.jugador_id == jugador_id)

    if partido_id:
        query = query.where(Estadistica.partido_id == partido_id)

    estadisticas = session.exec(query).all()
    return estadisticas


@router.get("/{estadistica_id}", response_model=Estadistica)
def read_estadistica(estadistica_id: int, session: SessionDep):
    """Obtener una estadística por ID"""
    estadistica = session.get(Estadistica, estadistica_id)
    if not estadistica:
        raise HTTPException(status_code=404, detail="Estadística no encontrada")
    return estadistica


@router.patch("/{estadistica_id}", response_model=Estadistica)
def update_estadistica(
        estadistica_id: int,
        estadistica_update: EstadisticaUpdate,
        session: SessionDep
):
    """
    Actualizar una estadística existente.
    Recalcula suspensiones si se modifican las tarjetas.
    """
    estadistica = session.get(Estadistica, estadistica_id)
    if not estadistica:
        raise HTTPException(status_code=404, detail="Estadística no encontrada")

    # Guardar valores anteriores de tarjetas
    tarjetas_amarillas_antes = estadistica.tarjetas_amarillas
    tarjetas_rojas_antes = estadistica.tarjetas_rojas

    # Actualizar campos
    update_data = estadistica_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(estadistica, key, value)

    # Si cambiaron las tarjetas, recalcular suspensión
    if ("tarjetas_amarillas" in update_data or "tarjetas_rojas" in update_data):
        jugador = session.get(Jugador, estadistica.jugador_id)

        # Calcular diferencia de suspensión
        suspension_anterior = (
                tarjetas_rojas_antes + (tarjetas_amarillas_antes // 5)
        )
        suspension_nueva = estadistica.calcular_suspension()
        diferencia = suspension_nueva - suspension_anterior

        if diferencia != 0:
            jugador.partidos_suspension_restantes = max(
                0,
                jugador.partidos_suspension_restantes + diferencia
            )

            # Actualizar estado del jugador
            if jugador.partidos_suspension_restantes > 0:
                jugador.estado = Estados.SUSPENDIDO
            elif jugador.estado == Estados.SUSPENDIDO:
                jugador.estado = Estados.ACTIVO

            session.add(jugador)

    session.add(estadistica)
    session.commit()
    session.refresh(estadistica)

    return estadistica


@router.delete("/{estadistica_id}")
def delete_estadistica(estadistica_id: int, session: SessionDep):
    """
    Eliminar una estadística.
    Ajusta la suspensión del jugador si es necesario.
    """
    estadistica = session.get(Estadistica, estadistica_id)
    if not estadistica:
        raise HTTPException(status_code=404, detail="Estadística no encontrada")

    # Obtener el jugador para ajustar suspensión
    jugador = session.get(Jugador, estadistica.jugador_id)

    # Restar la suspensión de esta estadística
    partidos_suspension = estadistica.calcular_suspension()
    if partidos_suspension > 0:
        jugador.partidos_suspension_restantes = max(
            0,
            jugador.partidos_suspension_restantes - partidos_suspension
        )

        # Actualizar estado si ya no tiene suspensión
        if jugador.partidos_suspension_restantes == 0 and jugador.estado == Estados.SUSPENDIDO:
            jugador.estado = Estados.ACTIVO

        session.add(jugador)

    session.delete(estadistica)
    session.commit()

    return {"ok": True, "detail": "Estadística eliminada exitosamente"}


@router.get("/jugador/{jugador_id}/eficiencia")
def calcular_eficiencia_jugador(jugador_id: int, session: SessionDep):
    """
    Calcular la eficiencia goleadora de un jugador.
    Retorna goles por 90 minutos.
    """
    jugador = session.get(Jugador, jugador_id)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # Obtener todas las estadísticas
    estadisticas = session.exec(
        select(Estadistica).where(Estadistica.jugador_id == jugador_id)
    ).all()

    if not estadisticas:
        return {
            "jugador_id": jugador_id,
            "nombre": jugador.nombre,
            "eficiencia_goleadora": 0.0,
            "total_goles": 0,
            "total_minutos": 0,
            "mensaje": "Sin estadísticas registradas"
        }

    total_goles = sum(est.goles for est in estadisticas)
    total_minutos = sum(est.minutos_jugados for est in estadisticas)

    eficiencia = (total_goles / total_minutos * 90) if total_minutos > 0 else 0

    return {
        "jugador_id": jugador_id,
        "nombre": jugador.nombre,
        "eficiencia_goleadora": round(eficiencia, 3),
        "total_goles": total_goles,
        "total_minutos": total_minutos,
        "partidos_jugados": len(estadisticas),
        "promedio_goles_partido": round(total_goles / len(estadisticas), 2)
    }


@router.get("/partido/{partido_id}/resumen")
def resumen_partido(partido_id: int, session: SessionDep):
    """
    Obtener un resumen completo del partido con estadísticas de todos los jugadores.
    """
    partido = session.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    # Obtener estadísticas del partido
    estadisticas = session.exec(
        select(Estadistica).where(Estadistica.partido_id == partido_id)
    ).all()

    jugadores_stats = []
    for est in estadisticas:
        jugador = session.get(Jugador, est.jugador_id)
        jugadores_stats.append({
            "jugador_id": jugador.id,
            "nombre": jugador.nombre,
            "numero": jugador.numero,
            "minutos_jugados": est.minutos_jugados,
            "goles": est.goles,
            "asistencias": est.asistencias,
            "faltas": est.faltas_cometidas,
            "tarjetas_amarillas": est.tarjetas_amarillas,
            "tarjetas_rojas": est.tarjetas_rojas,
            "eficiencia": round(est.eficiencia_goleadora(), 3)
        })

    return {
        "partido": {
            "id": partido.id,
            "fecha": partido.fecha,
            "rival": partido.rival,
            "resultado": partido.resultado,
            "goles_favor": partido.goles_favor,
            "goles_contra": partido.goles_contra
        },
        "jugadores": jugadores_stats,
        "totales": {
            "jugadores_participantes": len(estadisticas),
            "total_minutos_equipo": sum(est.minutos_jugados for est in estadisticas),
            "total_tarjetas_amarillas": sum(est.tarjetas_amarillas for est in estadisticas),
            "total_tarjetas_rojas": sum(est.tarjetas_rojas for est in estadisticas)
        }
    }