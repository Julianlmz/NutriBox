from fastapi import APIRouter, HTTPException, Query
from Aplicacion.database import SessionDep
from Datos.models import (
    Alimento, AlimentoCreate, AlimentoUpdate, MovimientoInventario, TipoMovimiento, CategoriaAlimento, HistorialEliminacion)
from typing import List

router = APIRouter(tags=["Alimentos"], prefix="/alimento")


@router.post("/", response_model=Alimento, status_code=201)
async def crear_alimento(data: AlimentoCreate, session: SessionDep):
    """
    Crea un nuevo alimento en el sistema con stock inicial.

    Args:
        data: Datos del alimento (nombre, categoría, valores nutricionales, precio, stock_inicial)
        session: Sesión de base de datos

    Returns:
        Alimento: Alimento creado con su ID asignado

    Raises:
        HTTPException 409: Si ya existe un alimento con el mismo nombre
        HTTPException 400: Si los datos son inválidos
    """
    # Verificar si ya existe alimento con ese nombre
    alimentos_existentes = session.query(Alimento).filter(
        Alimento.nombre == data.nombre
    ).all()
    if alimentos_existentes:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe un alimento con el nombre '{data.nombre}'"
        )

    # Crear alimento sin stock_inicial (no está en el modelo Alimento)
    alimento = Alimento(**data.model_dump(exclude={'stock_inicial'}))
    alimento.stock_actual = data.stock_inicial

    session.add(alimento)
    session.commit()
    session.refresh(alimento)

    # Registrar movimiento de inventario si hay stock inicial
    if data.stock_inicial > 0:
        movimiento = MovimientoInventario(
            alimento_id=alimento.id,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            cantidad=data.stock_inicial,
            motivo="Stock inicial del alimento",
            stock_anterior=0,
            stock_nuevo=data.stock_inicial,
            usuario_id=None
        )
        session.add(movimiento)
        session.commit()

    return alimento


@router.get("/", response_model=List[Alimento])
async def listar_alimentos(
        incluir_inactivos: bool = Query(default=False),
        categoria: CategoriaAlimento = Query(default=None),
        stock_bajo: bool = Query(default=False),
        stock_minimo: int = Query(default=10, ge=0),
        session: SessionDep = None
):
    """
    Lista alimentos con filtros opcionales.

    Args:
        incluir_inactivos: Incluir alimentos desactivados
        categoria: Filtrar por categoría específica
        stock_bajo: Mostrar solo alimentos con stock bajo
        stock_minimo: Umbral para considerar stock bajo (default: 10)
        session: Sesión de base de datos

    Returns:
        List[Alimento]: Lista de alimentos que cumplen los filtros

    Examples:
        - GET /alimento/ - Alimentos activos
        - GET /alimento/?categoria=Frutas - Solo frutas
        - GET /alimento/?stock_bajo=true - Alimentos con stock bajo
        - GET /alimento/?incluir_inactivos=true - Todos los alimentos
    """
    query = session.query(Alimento)

    if not incluir_inactivos:
        query = query.filter(Alimento.is_active == True)

    if categoria:
        query = query.filter(Alimento.categoria == categoria)

    if stock_bajo:
        query = query.filter(Alimento.stock_actual < stock_minimo)

    alimentos = query.all()
    return alimentos


@router.get("/{alimento_id}", response_model=Alimento)
async def obtener_alimento(alimento_id: int, session: SessionDep):
    """
    Obtiene un alimento por ID.

    Args:
        alimento_id: ID del alimento
        session: Sesión de base de datos

    Returns:
        Alimento: Datos completos del alimento

    Raises:
        HTTPException 404: Si el alimento no existe o está inactivo
    """
    alimento = session.get(Alimento, alimento_id)
    if not alimento or not alimento.is_active:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")
    return alimento


@router.put("/{alimento_id}", response_model=Alimento)
async def actualizar_alimento(
        alimento_id: int,
        data: AlimentoCreate,
        session: SessionDep
):
    """
    Actualiza completamente un alimento (PUT).

    Args:
        alimento_id: ID del alimento
        data: Nuevos datos del alimento
        session: Sesión de base de datos

    Returns:
        Alimento: Alimento actualizado

    Raises:
        HTTPException 404: Si el alimento no existe
        HTTPException 409: Si el nuevo nombre ya está en uso
    """
    alimento = session.get(Alimento, alimento_id)
    if not alimento or not alimento.is_active:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")

    # Verificar nombre duplicado si cambió
    if alimento.nombre != data.nombre:
        alimentos_existentes = session.query(Alimento).filter(
            Alimento.nombre == data.nombre
        ).all()
        if alimentos_existentes:
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe un alimento con el nombre '{data.nombre}'"
            )

    # Actualizar todos los campos excepto stock_inicial
    for key, value in data.model_dump(exclude={'stock_inicial'}).items():
        setattr(alimento, key, value)

    session.commit()
    session.refresh(alimento)
    return alimento


@router.patch("/{alimento_id}", response_model=Alimento)
async def actualizar_parcial_alimento(
        alimento_id: int,
        data: AlimentoUpdate,
        session: SessionDep
):
    """
    Actualiza parcialmente un alimento (PATCH).

    Args:
        alimento_id: ID del alimento
        data: Campos a actualizar
        session: Sesión de base de datos

    Returns:
        Alimento: Alimento actualizado

    Raises:
        HTTPException 404: Si el alimento no existe
        HTTPException 400: Si no se proporcionan datos
    """
    alimento = session.get(Alimento, alimento_id)
    if not alimento or not alimento.is_active:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No se proporcionaron datos para actualizar"
        )

    # Verificar nombre duplicado si se está actualizando
    if "nombre" in update_data and alimento.nombre != update_data["nombre"]:
        alimentos_existentes = session.query(Alimento).filter(
            Alimento.nombre == update_data["nombre"]
        ).all()
        if alimentos_existentes:
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe un alimento con el nombre '{update_data['nombre']}'"
            )

    # Actualizar solo los campos proporcionados
    for key, value in update_data.items():
        setattr(alimento, key, value)

    session.commit()
    session.refresh(alimento)
    return alimento


@router.delete("/{alimento_id}", status_code=204)
async def eliminar_alimento(
        alimento_id: int,
        session: SessionDep,
        motivo: str = Query(default=None),
        hard_delete: bool = Query(default=False)
):
    """
    Elimina o desactiva un alimento.

    Args:
        alimento_id: ID del alimento
        session: Sesión de base de datos
        motivo: Motivo de la eliminación (opcional)
        hard_delete: Si es True, elimina permanentemente. Si es False, solo desactiva

    Returns:
        None: Respuesta vacía con código 204

    Raises:
        HTTPException 404: Si el alimento no existe
    """
    alimento = session.get(Alimento, alimento_id)
    if not alimento:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")

    if hard_delete:
        # Guardar en historial antes de eliminar
        datos_str = f"nombre={alimento.nombre},categoria={alimento.categoria},stock={alimento.stock_actual}"
        historial = HistorialEliminacion(
            tabla_nombre="alimento",
            registro_id=alimento.id,
            datos_json=datos_str,
            motivo=motivo or "Eliminación permanente",
            usuario_eliminador_id=None
        )
        session.add(historial)
        session.delete(alimento)
    else:
        # Soft delete: solo desactivar
        alimento.is_active = False

    session.commit()
    return


@router.get("/{alimento_id}/restricciones")
async def obtener_restricciones_alimento(alimento_id: int, session: SessionDep):
    """
    Obtiene todas las restricciones/alergias asociadas a un alimento.

    Args:
        alimento_id: ID del alimento
        session: Sesión de base de datos

    Returns:
        list: Lista de restricciones con sus detalles

    Raises:
        HTTPException 404: Si el alimento no existe
    """
    alimento = session.get(Alimento, alimento_id)
    if not alimento:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")

    restricciones = [
        {
            "id": r.restriccion.id,
            "nombre": r.restriccion.nombre,
            "descripcion": r.restriccion.descripcion,
            "nivel_severidad": r.restriccion.nivel_severidad,
            "fecha_asociacion": r.fecha_asociacion
        }
        for r in alimento.restricciones
    ]

    return {
        "alimento_id": alimento.id,
        "nombre_alimento": alimento.nombre,
        "total_restricciones": len(restricciones),
        "restricciones": restricciones
    }


@router.get("/{alimento_id}/movimientos")
async def obtener_movimientos_alimento(
        alimento_id: int,
        session: SessionDep,
        limite: int = Query(default=50, ge=1, le=100)
):
    """
    Obtiene el historial de movimientos de inventario de un alimento.

    Args:
        alimento_id: ID del alimento
        session: Sesión de base de datos
        limite: Número máximo de movimientos a retornar

    Returns:
        dict: Información del alimento y su historial de movimientos

    Raises:
        HTTPException 404: Si el alimento no existe
    """
    alimento = session.get(Alimento, alimento_id)
    if not alimento:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")

    # Obtener últimos movimientos
    movimientos_query = session.query(MovimientoInventario).filter(
        MovimientoInventario.alimento_id == alimento_id
    ).order_by(MovimientoInventario.fecha.desc()).limit(limite)

    movimientos = movimientos_query.all()

    movimientos_list = [
        {
            "id": m.id,
            "tipo": m.tipo_movimiento,
            "cantidad": m.cantidad,
            "stock_anterior": m.stock_anterior,
            "stock_nuevo": m.stock_nuevo,
            "motivo": m.motivo,
            "fecha": m.fecha
        }
        for m in movimientos
    ]

    return {
        "alimento_id": alimento.id,
        "nombre_alimento": alimento.nombre,
        "stock_actual": alimento.stock_actual,
        "total_movimientos": len(movimientos_list),
        "movimientos": movimientos_list
    }


@router.post("/{alimento_id}/ajustar-stock", response_model=Alimento)
async def ajustar_stock_alimento(
        alimento_id: int,
        tipo_movimiento: TipoMovimiento,
        cantidad: int = Query(..., description="Cantidad a modificar (positivo o negativo)"),
        motivo: str = Query(..., description="Motivo del ajuste"),
        usuario_id: int = Query(default=None),
        session: SessionDep = None
):
    """
    Ajusta el stock de un alimento y registra el movimiento.

    Args:
        alimento_id: ID del alimento
        tipo_movimiento: Tipo de movimiento (ENTRADA, SALIDA, AJUSTE)
        cantidad: Cantidad a ajustar
        motivo: Motivo del ajuste
        usuario_id: ID del usuario que realiza el ajuste
        session: Sesión de base de datos

    Returns:
        Alimento: Alimento con stock actualizado

    Raises:
        HTTPException 404: Si el alimento no existe
        HTTPException 400: Si el stock resultante es negativo
    """
    alimento = session.get(Alimento, alimento_id)
    if not alimento or not alimento.is_active:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")

    stock_anterior = alimento.stock_actual

    # Calcular nuevo stock según tipo de movimiento
    if tipo_movimiento == TipoMovimiento.ENTRADA:
        stock_nuevo = stock_anterior + abs(cantidad)
    elif tipo_movimiento == TipoMovimiento.SALIDA:
        stock_nuevo = stock_anterior - abs(cantidad)
    else:  # AJUSTE
        stock_nuevo = cantidad

    # Validar que el stock no sea negativo
    if stock_nuevo < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente. Stock actual: {stock_anterior}, cantidad solicitada: {cantidad}"
        )

    # Actualizar stock
    alimento.stock_actual = stock_nuevo

    # Registrar movimiento
    movimiento = MovimientoInventario(
        alimento_id=alimento.id,
        tipo_movimiento=tipo_movimiento,
        cantidad=cantidad,
        motivo=motivo,
        stock_anterior=stock_anterior,
        stock_nuevo=stock_nuevo,
        usuario_id=usuario_id
    )

    session.add(movimiento)
    session.commit()
    session.refresh(alimento)

    return alimento