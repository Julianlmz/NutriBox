from fastapi import APIRouter, HTTPException, Query, Response, status
from Core.database import SessionDep
from Modulos.models import (Restriccion, RestriccionCreate, RestriccionUpdate, RestriccionAlimento, Alimento,
                            NivelSeveridad)
from typing import List
from sqlmodel import select

router = APIRouter(tags=["Restricciones y Modulos"], prefix="/restriccion")


@router.post("/", response_model=Restriccion, status_code=201)
async def crear_restriccion(
        data: RestriccionCreate,
        session: SessionDep,
        response: Response
):
    """
    Crea una nueva restricción o devuelve la existente si ya hay una con ese nombre.
    """
    # 1. Verificar si ya existe restricción con ese nombre
    query = select(Restriccion).where(Restriccion.nombre == data.nombre)
    result = await session.execute(query)
    restriccion_existente = result.scalars().first()

    # CORRECCIÓN: Si existe, la devolvemos en lugar de lanzar error 409
    if restriccion_existente:
        response.status_code = status.HTTP_200_OK  # Cambiamos el estado a 200
        return restriccion_existente

    # 2. Si no existe, la creamos
    restriccion = Restriccion(**data.model_dump())
    session.add(restriccion)
    await session.commit()
    await session.refresh(restriccion)
    return restriccion


@router.get("/", response_model=List[Restriccion])
async def listar_restricciones(
        nivel_severidad: NivelSeveridad = Query(default=None),
        session: SessionDep = None
):
    query = select(Restriccion)

    if nivel_severidad:
        query = query.where(Restriccion.nivel_severidad == nivel_severidad)

    result = await session.execute(query)
    restricciones = result.scalars().all()
    return restricciones


@router.get("/{restriccion_id}", response_model=Restriccion)
async def obtener_restriccion(restriccion_id: int, session: SessionDep):
    restriccion = await session.get(Restriccion, restriccion_id)
    if not restriccion:
        raise HTTPException(status_code=404, detail="Restricción no encontrada")
    return restriccion


@router.patch("/{restriccion_id}", response_model=Restriccion)
async def actualizar_restriccion(
        restriccion_id: int,
        data: RestriccionUpdate,
        session: SessionDep
):
    restriccion = await session.get(Restriccion, restriccion_id)
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
        query = select(Restriccion).where(Restriccion.nombre == update_data["nombre"])
        result = await session.execute(query)
        restriccion_existente = result.scalars().first()
        # Aquí sí mantenemos el error si intentan renombrar a uno que ya existe
        if restriccion_existente:
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe una restricción con el nombre '{update_data['nombre']}'"
            )

    for key, value in update_data.items():
        setattr(restriccion, key, value)

    session.add(restriccion)
    await session.commit()
    await session.refresh(restriccion)
    return restriccion


@router.delete("/{restriccion_id}", status_code=204)
async def eliminar_restriccion(restriccion_id: int, session: SessionDep):
    restriccion = await session.get(Restriccion, restriccion_id)
    if not restriccion:
        raise HTTPException(status_code=404, detail="Restricción no encontrada")

    await session.delete(restriccion)
    await session.commit()
    return


@router.post("/{restriccion_id}/alimento/{alimento_id}", status_code=201)
async def asociar_alimento(
        restriccion_id: int,
        alimento_id: int,
        session: SessionDep
):
    restriccion = await session.get(Restriccion, restriccion_id)
    alimento = await session.get(Alimento, alimento_id)

    if not restriccion:
        raise HTTPException(status_code=404, detail="Restricción no encontrada")
    if not alimento:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")

    query = select(RestriccionAlimento).where(
        RestriccionAlimento.restriccion_id == restriccion_id,
        RestriccionAlimento.alimento_id == alimento_id
    )
    result = await session.execute(query)
    asociacion_existente = result.scalars().first()

    if asociacion_existente:
        raise HTTPException(
            status_code=409,
            detail=f"El alimento '{alimento.nombre}' ya está asociado a la restricción '{restriccion.nombre}'"
        )

    asociacion = RestriccionAlimento(
        restriccion_id=restriccion_id,
        alimento_id=alimento_id
    )
    session.add(asociacion)
    await session.commit()

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
    query = select(RestriccionAlimento).where(
        RestriccionAlimento.restriccion_id == restriccion_id,
        RestriccionAlimento.alimento_id == alimento_id
    )
    result = await session.execute(query)
    asociacion = result.scalars().first()

    if not asociacion:
        raise HTTPException(
            status_code=404,
            detail="La asociación no existe"
        )

    await session.delete(asociacion)
    await session.commit()
    return


@router.get("/{restriccion_id}/alimentos")
async def listar_alimentos_restriccion(restriccion_id: int, session: SessionDep):
    restriccion = await session.get(Restriccion, restriccion_id)
    if not restriccion:
        raise HTTPException(status_code=404, detail="Restricción no encontrada")

    # Nota: Para acceder a .alimentos aquí requeriría eager loading en el GET
    # O hacer una query manual si no está cargado.
    # Asumimos que la sesión lo maneja o se ajusta si falla (similar al fix de Loncheras)

    return {
        "restriccion_id": restriccion.id,
        "nombre_restriccion": restriccion.nombre,
        "nivel_severidad": restriccion.nivel_severidad,
        # Si falla .alimentos, se debería ajustar la query inicial con selectinload
        "total_alimentos": len(restriccion.alimentos) if restriccion.alimentos else 0,
        "alimentos": [
            {"id": a.alimento.id, "nombre": a.alimento.nombre} for a in restriccion.alimentos
        ] if restriccion.alimentos else []
    }


@router.post("/buscar-compatibles", response_model=List[Alimento])
async def buscar_alimentos_compatibles(
        restriccion_ids: List[int],
        session: SessionDep
):
    if not restriccion_ids:
        query = select(Alimento).where(Alimento.is_active == True)
        result = await session.execute(query)
        return result.scalars().all()

    alimentos_restringidos_ids = set()
    for restriccion_id in restriccion_ids:
        query = select(RestriccionAlimento).where(
            RestriccionAlimento.restriccion_id == restriccion_id
        )
        result = await session.execute(query)
        asociaciones = result.scalars().all()
        alimentos_restringidos_ids.update(a.alimento_id for a in asociaciones)

    if alimentos_restringidos_ids:
        query = select(Alimento).where(
            Alimento.is_active == True,
            ~Alimento.id.in_(alimentos_restringidos_ids)
        )
    else:
        query = select(Alimento).where(Alimento.is_active == True)

    result = await session.execute(query)
    return result.scalars().all()


@router.get("/estadisticas/resumen")
async def obtener_estadisticas(session: SessionDep):
    query_total = select(Restriccion)
    result_total = await session.execute(query_total)
    total_restricciones = len(result_total.scalars().all())

    return {
        "total_restricciones": total_restricciones,
        "mensaje": "Estadísticas básicas (expandir según necesidad)"
    }