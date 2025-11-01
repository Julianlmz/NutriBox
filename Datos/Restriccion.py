from fastapi import APIRouter, HTTPException, Query
from Aplicacion.database import SessionDep
from Datos.models import (Restriccion, RestriccionCreate, RestriccionUpdate, RestriccionAlimento, Alimento, NivelSeveridad)
from typing import List

router = APIRouter(tags=["Restricciones y Alergias"], prefix="/restriccion")


@router.post("/", response_model=Restriccion, status_code=201)
async def crear_restriccion(data: RestriccionCreate, session: SessionDep):
    """
    Crea una nueva restricción alimentaria o alergia.

    Args:
        data: Datos de la restricción (nombre, descripción, nivel_severidad)
        session: Sesión de base de datos

    Returns:
        Restriccion: Restricción creada con su ID

    Raises:
        HTTPException 409: Si ya existe una restricción con el mismo nombre
        HTTPException 400: Si los datos son inválidos
    """
    # Verificar si ya existe restricción con ese nombre
    restriccion_existente = session.query(Restriccion).filter(
        Restriccion.nombre == data.nombre
    ).first()

    if restriccion_existente:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe una restricción con el nombre '{data.nombre}'"
        )

    restriccion = Restriccion(**data.model_dump())
    session.add(restriccion)
    session.commit()
    session.refresh(restriccion)
    return restriccion


@router.get("/", response_model=List[Restriccion])
async def listar_restricciones(
        nivel_severidad: NivelSeveridad = Query(default=None),
        session: SessionDep = None
):
    """
    Lista todas las restricciones alimentarias.

    Args:
        nivel_severidad: Filtrar por nivel de severidad (Bajo, Medio, Alto)
        session: Sesión de base de datos

    Returns:
        List[Restriccion]: Lista de restricciones

    Examples:
        - GET /restriccion/ - Todas las restricciones
        - GET /restriccion/?nivel_severidad=Alto - Solo restricciones de alta severidad
    """
    query = session.query(Restriccion)

    if nivel_severidad:
        query = query.filter(Restriccion.nivel_severidad == nivel_severidad)

    restricciones = query.all()
    return restricciones


@router.get("/{restriccion_id}", response_model=Restriccion)
async def obtener_restriccion(restriccion_id: int, session: SessionDep):
    """
    Obtiene una restricción por ID.

    Args:
        restriccion_id: ID de la restricción
        session: Sesión de base de datos

    Returns:
        Restriccion: Datos de la restricción

    Raises:
        HTTPException 404: Si la restricción no existe
    """
    restriccion = session.get(Restriccion, restriccion_id)
    if not restriccion:
        raise HTTPException(status_code=404, detail="Restricción no encontrada")
    return restriccion


@router.patch("/{restriccion_id}", response_model=Restriccion)
async def actualizar_restriccion(
        restriccion_id: int,
        data: RestriccionUpdate,
        session: SessionDep
):
    """
    Actualiza parcialmente una restricción.

    Args:
        restriccion_id: ID de la restricción
        data: Campos a actualizar
        session: Sesión de base de datos

    Returns:
        Restriccion: Restricción actualizada

    Raises:
        HTTPException 404: Si la restricción no existe
        HTTPException 400: Si no se proporcionan datos
    """
    restriccion = session.get(Restriccion, restriccion_id)
    if not restriccion:
        raise HTTPException(status_code=404, detail="Restricción no encontrada")

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No se proporcionaron datos para actualizar"
        )

    # Verificar nombre duplicado si se está actualizando
    if "nombre" in update_data and restriccion.nombre != update_data["nombre"]:
        restriccion_existente = session.query(Restriccion).filter(
            Restriccion.nombre == update_data["nombre"]
        ).first()
        if restriccion_existente:
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe una restricción con el nombre '{update_data['nombre']}'"
            )

    # Actualizar campos
    for key, value in update_data.items():
        setattr(restriccion, key, value)

    session.commit()
    session.refresh(restriccion)
    return restriccion


@router.delete("/{restriccion_id}", status_code=204)
async def eliminar_restriccion(restriccion_id: int, session: SessionDep):
    """
    Elimina una restricción del sistema.

    Nota: También elimina todas las asociaciones con alimentos.

    Args:
        restriccion_id: ID de la restricción
        session: Sesión de base de datos

    Returns:
        None: Respuesta vacía con código 204

    Raises:
        HTTPException 404: Si la restricción no existe
    """
    restriccion = session.get(Restriccion, restriccion_id)
    if not restriccion:
        raise HTTPException(status_code=404, detail="Restricción no encontrada")

    session.delete(restriccion)
    session.commit()
    return


@router.post("/{restriccion_id}/alimento/{alimento_id}", status_code=201)
async def asociar_alimento(
        restriccion_id: int,
        alimento_id: int,
        session: SessionDep
):
    """
    Asocia un alimento a una restricción/alergia.

    Args:
        restriccion_id: ID de la restricción
        alimento_id: ID del alimento
        session: Sesión de base de datos

    Returns:
        dict: Mensaje de confirmación

    Raises:
        HTTPException 404: Si la restricción o alimento no existen
        HTTPException 409: Si la asociación ya existe
    """
    restriccion = session.get(Restriccion, restriccion_id)
    alimento = session.get(Alimento, alimento_id)

    if not restriccion:
        raise HTTPException(status_code=404, detail="Restricción no encontrada")
    if not alimento:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")

    # Verificar si ya existe la asociación
    asociacion_existente = session.query(RestriccionAlimento).filter(
        RestriccionAlimento.restriccion_id == restriccion_id,
        RestriccionAlimento.alimento_id == alimento_id
    ).first()

    if asociacion_existente:
        raise HTTPException(
            status_code=409,
            detail=f"El alimento '{alimento.nombre}' ya está asociado a la restricción '{restriccion.nombre}'"
        )

    # Crear asociación
    asociacion = RestriccionAlimento(
        restriccion_id=restriccion_id,
        alimento_id=alimento_id
    )
    session.add(asociacion)
    session.commit()

    return {
        "message": "Alimento asociado exitosamente",
        "restriccion": restriccion.nombre,
        "alimento": alimento.nombre
    }


@router.delete("/{restriccion_id}/alimento/{alimento_id}", status_code=204)
async def desasociar_alimento(
        restriccion_id: int,
        alimento_id: int,
        session: SessionDep
):
    """
    Desasocia un alimento de una restricción/alergia.

    Args:
        restriccion_id: ID de la restricción
        alimento_id: ID del alimento
        session: Sesión de base de datos

    Returns:
        None: Respuesta vacía con código 204

    Raises:
        HTTPException 404: Si la asociación no existe
    """
    asociacion = session.query(RestriccionAlimento).filter(
        RestriccionAlimento.restriccion_id == restriccion_id,
        RestriccionAlimento.alimento_id == alimento_id
    ).first()

    if not asociacion:
        raise HTTPException(
            status_code=404,
            detail="La asociación no existe"
        )

    session.delete(asociacion)
    session.commit()
    return


@router.get("/{restriccion_id}/alimentos")
async def listar_alimentos_restriccion(restriccion_id: int, session: SessionDep):
    """
    Lista todos los alimentos asociados a una restricción.

    Args:
        restriccion_id: ID de la restricción
        session: Sesión de base de datos

    Returns:
        dict: Información de la restricción y sus alimentos asociados

    Raises:
        HTTPException 404: Si la restricción no existe
    """
    restriccion = session.get(Restriccion, restriccion_id)
    if not restriccion:
        raise HTTPException(status_code=404, detail="Restricción no encontrada")

    alimentos = [
        {
            "id": a.alimento.id,
            "nombre": a.alimento.nombre,
            "categoria": a.alimento.categoria,
            "precio_unitario": a.alimento.precio_unitario,
            "fecha_asociacion": a.fecha_asociacion
        }
        for a in restriccion.alimentos
    ]

    return {
        "restriccion_id": restriccion.id,
        "nombre_restriccion": restriccion.nombre,
        "nivel_severidad": restriccion.nivel_severidad,
        "total_alimentos": len(alimentos),
        "alimentos": alimentos
    }


@router.post("/buscar-compatibles", response_model=List[Alimento])
async def buscar_alimentos_compatibles(
        restriccion_ids: List[int],
        session: SessionDep
):
    """
    Busca alimentos compatibles (sin restricciones específicas).

    Args:
        restriccion_ids: Lista de IDs de restricciones a evitar
        session: Sesión de base de datos

    Returns:
        List[Alimento]: Alimentos que NO tienen las restricciones especificadas

    Example:
        POST /restriccion/buscar-compatibles
        Body: [1, 3, 5]  # IDs de restricciones a evitar
    """
    if not restriccion_ids:
        # Si no hay restricciones, devolver todos los alimentos activos
        return session.query(Alimento).filter(Alimento.is_active == True).all()

    # Obtener IDs de alimentos con las restricciones especificadas
    alimentos_restringidos_ids = set()
    for restriccion_id in restriccion_ids:
        asociaciones = session.query(RestriccionAlimento).filter(
            RestriccionAlimento.restriccion_id == restriccion_id
        ).all()
        alimentos_restringidos_ids.update(a.alimento_id for a in asociaciones)

    # Obtener alimentos que NO están en la lista de restringidos
    if alimentos_restringidos_ids:
        alimentos_compatibles = session.query(Alimento).filter(
            Alimento.is_active == True,
            ~Alimento.id.in_(alimentos_restringidos_ids)
        ).all()
    else:
        alimentos_compatibles = session.query(Alimento).filter(
            Alimento.is_active == True
        ).all()

    return alimentos_compatibles


@router.get("/estadisticas/resumen")
async def obtener_estadisticas(session: SessionDep):
    """
    Obtiene estadísticas generales de restricciones.

    Args:
        session: Sesión de base de datos

    Returns:
        dict: Estadísticas de restricciones por severidad y alimentos afectados
    """
    # Total de restricciones
    total_restricciones = session.query(Restriccion).count()

    # Por nivel de severidad
    por_severidad = {}
    for nivel in NivelSeveridad:
        count = session.query(Restriccion).filter(
            Restriccion.nivel_severidad == nivel
        ).count()
        por_severidad[nivel.value] = count

    # Alimentos más restringidos
    alimentos_restricciones = session.query(RestriccionAlimento).all()
    alimento_count = {}
    for ar in alimentos_restricciones:
        alimento_id = ar.alimento_id
        if alimento_id not in alimento_count:
            alimento_count[alimento_id] = 0
        alimento_count[alimento_id] += 1

    # Top 5 alimentos más restringidos
    top_restringidos = []
    for alimento_id in sorted(alimento_count, key=alimento_count.get, reverse=True)[:5]:
        alimento = session.get(Alimento, alimento_id)
        if alimento:
            top_restringidos.append({
                "id": alimento.id,
                "nombre": alimento.nombre,
                "total_restricciones": alimento_count[alimento_id]
            })

    return {
        "total_restricciones": total_restricciones,
        "por_nivel_severidad": por_severidad,
        "top_alimentos_restringidos": top_restringidos,
        "total_asociaciones": len(alimentos_restricciones)
    }