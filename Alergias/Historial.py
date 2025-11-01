from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from typing import List, Optional
from Datos.models import HistorialEliminacion
from Aplicacion.database import SessionDep
import json

router = APIRouter(prefix="/historial", tags=["Historial de Eliminaciones"])


@router.get("/", response_model=List[HistorialEliminacion])
async def listar_historial(
        session: SessionDep,
        tabla_nombre: Optional[str] = None,
        usuario_id: Optional[int] = None
):
    query = select(HistorialEliminacion)

    if tabla_nombre:
        query = query.where(HistorialEliminacion.tabla_nombre == tabla_nombre)
    if usuario_id:
        query = query.where(HistorialEliminacion.usuario_eliminador_id == usuario_id)

    query = query.order_by(HistorialEliminacion.fecha_eliminacion.desc())
    historial = session.exec(query).all()
    return historial


@router.get("/{historial_id}", response_model=HistorialEliminacion)
async def obtener_registro_historial(historial_id: int, session: SessionDep):
    """
    Obtiene un registro específico del historial por su ID.
    """
    registro = session.get(HistorialEliminacion, historial_id)
    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro no encontrado"
        )
    return registro


@router.get("/{historial_id}/datos")
async def obtener_datos_eliminados(historial_id: int, session: SessionDep):
    """
    Obtiene los datos completos del registro eliminado en formato JSON.
    """
    registro = session.get(HistorialEliminacion, historial_id)
    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro no encontrado"
        )

    try:
        datos = json.loads(registro.datos_json)
        return {
            "tabla": registro.tabla_nombre,
            "registro_id": registro.registro_id,
            "fecha_eliminacion": registro.fecha_eliminacion,
            "motivo": registro.motivo,
            "datos": datos
        }
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al decodificar los datos"
        )


@router.get("/por-tabla/{tabla_nombre}")
async def historial_por_tabla(tabla_nombre: str, session: SessionDep):
    """
    Obtiene todo el historial de eliminaciones de una tabla específica.

    - **tabla_nombre**: usuario, lonchera, alimento, producto, etc.
    """
    historial = session.exec(
        select(HistorialEliminacion)
        .where(HistorialEliminacion.tabla_nombre == tabla_nombre)
        .order_by(HistorialEliminacion.fecha_eliminacion.desc())
    ).all()

    return historial


@router.get("/estadisticas/resumen")
async def estadisticas_eliminaciones(session: SessionDep):
    """
    Obtiene estadísticas generales sobre las eliminaciones registradas.
    """
    registros = session.exec(select(HistorialEliminacion)).all()

    por_tabla = {}
    por_usuario = {}

    for r in registros:
        # Conteo por tabla
        if r.tabla_nombre not in por_tabla:
            por_tabla[r.tabla_nombre] = 0
        por_tabla[r.tabla_nombre] += 1

        # Conteo por usuario
        if r.usuario_eliminador_id:
            if r.usuario_eliminador_id not in por_usuario:
                por_usuario[r.usuario_eliminador_id] = 0
            por_usuario[r.usuario_eliminador_id] += 1

    return {
        "total_eliminaciones": len(registros),
        "por_tabla": por_tabla,
        "por_usuario": por_usuario,
        "ultima_eliminacion": registros[0].fecha_eliminacion if registros else None
    }


@router.delete("/{historial_id}", status_code=status.HTTP_200_OK)
async def eliminar_registro_historial(historial_id: int, session: SessionDep):

    registro = session.get(HistorialEliminacion, historial_id)
    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro no encontrado"
        )

    session.delete(registro)
    session.commit()
    return {"message": "Registro de historial eliminado"}