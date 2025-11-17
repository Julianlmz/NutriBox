from fastapi import APIRouter, HTTPException, Query, File, UploadFile, Form, Depends
from Core.database import SessionDep
from Modulos.models import (
    Alimento, AlimentoCreate, AlimentoUpdate, MovimientoInventario,
    TipoMovimiento, CategoriaAlimento, HistorialEliminacion
)
from Core.supabase_client import upload_to_bucket
from typing import List, Optional
import json

router = APIRouter(tags=["Alimentos"], prefix="/alimento")


@router.post("/", response_model=Alimento, status_code=201)
async def crear_alimento(
        session: SessionDep,
        # --- ⭐️ ¡CORRECCIÓN! Usamos tipos primitivos para Form() ⭐️
        nombre: str = Form(...),
        categoria: str = Form(...),  # <-- Ahora es str
        calorias_por_100g: float = Form(...),
        proteinas_por_100g: float = Form(...),
        carbohidratos_por_100g: float = Form(...),
        grasas_por_100g: float = Form(...),
        precio_unitario: float = Form(...),
        stock_inicial: int = Form(0),
        imagen: Optional[UploadFile] = File(None)
):
    """
    Crea un nuevo alimento. Recibe datos de formulario y una imagen opcional.
    """

    # 1. Subir la imagen a Supabase (si existe)
    imagen_url = None
    if imagen and imagen.filename:
        imagen_url = await upload_to_bucket(imagen)

    # 2. Verificar si ya existe el alimento
    alimento_existente = session.query(Alimento).filter(Alimento.nombre == nombre).first()
    if alimento_existente:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe un alimento con el nombre '{nombre}'"
        )

    # 3. Validar y crear el objeto AlimentoCreate (Pydantic valida el Enum aquí)
    try:
        alimento_data = AlimentoCreate(
            nombre=nombre,
            categoria=categoria,  # <- Pydantic lo convertirá de str a Enum
            calorias_por_100g=calorias_por_100g,
            proteinas_por_100g=proteinas_por_100g,
            carbohidratos_por_100g=carbohidratos_por_100g,
            grasas_por_100g=grasas_por_100g,
            precio_unitario=precio_unitario,
            stock_inicial=stock_inicial
        )
    except Exception as e:
        # Esto captura errores si el float/int no es correcto o si la categoría no es válida
        raise HTTPException(status_code=400, detail=f"Error de validación: {e}")

    # 4. Crear la instancia de la tabla y asignar la URL de la imagen
    alimento = Alimento.model_validate(alimento_data)
    alimento.imagen_url = imagen_url
    alimento.stock_actual = stock_inicial

    session.add(alimento)
    session.commit()
    session.refresh(alimento)

    # 5. Registrar el movimiento de inventario (tu lógica original)
    if stock_inicial > 0:
        movimiento = MovimientoInventario(
            alimento_id=alimento.id,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            cantidad=stock_inicial,
            motivo="Stock inicial del alimento",
            stock_anterior=0,
            stock_nuevo=stock_inicial,
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

    session.add(alimento)
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

    session.add(alimento)
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
    """
    alimento = session.get(Alimento, alimento_id)
    if not alimento:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")

    if hard_delete:
        # Guardar en historial antes de eliminar (asumiendo que HistorialEliminacion y Usuario existen)
        try:
            datos_str = json.dumps({
                "nombre": alimento.nombre,
                "categoria": str(alimento.categoria),
                "stock": alimento.stock_actual
            })
            historial = HistorialEliminacion(
                tabla_nombre="alimento",
                registro_id=alimento.id,
                datos_json=datos_str,
                motivo=motivo or "Eliminación permanente",
                usuario_eliminador_id=None
            )
            session.add(historial)
        except NameError:
            # Si HistorialEliminacion no está importado o definido, ignoramos el historial en hard delete.
            pass

        session.delete(alimento)
    else:
        # Soft delete: solo desactivar
        alimento.is_active = False
        session.add(alimento)

    session.commit()
    return


@router.get("/{alimento_id}/restricciones")
async def obtener_restricciones_alimento(alimento_id: int, session: SessionDep):
    """
    Obtiene todas las restricciones/alergias asociadas a un alimento.
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
    session.add(alimento)
    session.commit()
    session.refresh(alimento)

    return alimento


# --- ⭐️ ¡ENDPOINT DE IMAGEN DE ALIMENTO (PATCH) ⭐️ ---
@router.post("/{alimento_id}/upload-image", response_model=Alimento)
async def subir_imagen_alimento(
        alimento_id: int,
        session: SessionDep,
        imagen: UploadFile = File(...)
):
    """
    Sube una imagen para un alimento existente.
    """
    # 1. Busca el alimento
    alimento = obtener_alimento(alimento_id, session)

    # 2. Sube la imagen a Supabase (usando tu lógica Core/supabase_client)
    imagen_url = await upload_to_bucket(imagen)

    # 3. Actualiza la base de datos
    alimento.imagen_url = imagen_url
    session.add(alimento)
    session.commit()
    session.refresh(alimento)

    return alimento