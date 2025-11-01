from fastapi import APIRouter, HTTPException, Query
from Aplicacion.database import SessionDep
from Datos.models import (Lonchera, LoncheraCreate, LoncheraUpdate, LoncheraAlimento, AgregarAlimento, Usuario, Alimento, RestriccionAlimento)
from typing import List

router = APIRouter(tags=["Loncheras"], prefix="/lonchera")


@router.post("/", response_model=Lonchera, status_code=201)
async def crear_lonchera(data: LoncheraCreate, session: SessionDep):
    """
    Crea una nueva lonchera para un usuario.

    Args:
        data: Datos de la lonchera (nombre, descripción, usuario_id)
        session: Sesión de base de datos

    Returns:
        Lonchera: Lonchera creada

    Raises:
        HTTPException 404: Si el usuario no existe o está inactivo
    """
    usuario = session.get(Usuario, data.usuario_id)
    if not usuario or not usuario.is_active:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado o inactivo"
        )

    lonchera = Lonchera(**data.model_dump())
    session.add(lonchera)
    session.commit()
    session.refresh(lonchera)
    return lonchera


@router.get("/", response_model=List[Lonchera])
async def listar_loncheras(
        usuario_id: int = Query(default=None),
        incluir_inactivas: bool = Query(default=False),
        session: SessionDep = None
):
    """
    Lista loncheras con filtros opcionales.

    Args:
        usuario_id: Filtrar por usuario específico
        incluir_inactivas: Incluir loncheras desactivadas
        session: Sesión de base de datos

    Returns:
        List[Lonchera]: Lista de loncheras

    Examples:
        - GET /lonchera/ - Loncheras activas
        - GET /lonchera/?usuario_id=5 - Loncheras de un usuario
        - GET /lonchera/?incluir_inactivas=true - Todas las loncheras
    """
    query = session.query(Lonchera)

    if usuario_id:
        query = query.filter(Lonchera.usuario_id == usuario_id)

    if not incluir_inactivas:
        query = query.filter(Lonchera.is_active == True)

    loncheras = query.all()
    return loncheras


@router.get("/{lonchera_id}", response_model=Lonchera)
async def obtener_lonchera(lonchera_id: int, session: SessionDep):
    """
    Obtiene una lonchera por ID.

    Args:
        lonchera_id: ID de la lonchera
        session: Sesión de base de datos

    Returns:
        Lonchera: Datos de la lonchera

    Raises:
        HTTPException 404: Si la lonchera no existe o está inactiva
    """
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera or not lonchera.is_active:
        raise HTTPException(status_code=404, detail="Lonchera no encontrada")
    return lonchera


@router.patch("/{lonchera_id}", response_model=Lonchera)
async def actualizar_lonchera(
        lonchera_id: int,
        data: LoncheraUpdate,
        session: SessionDep
):
    """
    Actualiza parcialmente una lonchera.

    Args:
        lonchera_id: ID de la lonchera
        data: Campos a actualizar
        session: Sesión de base de datos

    Returns:
        Lonchera: Lonchera actualizada

    Raises:
        HTTPException 404: Si la lonchera no existe
        HTTPException 400: Si no se proporcionan datos
    """
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera or not lonchera.is_active:
        raise HTTPException(status_code=404, detail="Lonchera no encontrada")

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No se proporcionaron datos para actualizar"
        )

    for key, value in update_data.items():
        setattr(lonchera, key, value)

    session.commit()
    session.refresh(lonchera)
    return lonchera


@router.delete("/{lonchera_id}", status_code=204)
async def eliminar_lonchera(
        lonchera_id: int,
        session: SessionDep,
        hard_delete: bool = Query(default=False)
):
    """
    Elimina o desactiva una lonchera.

    Args:
        lonchera_id: ID de la lonchera
        session: Sesión de base de datos
        hard_delete: Si es True, elimina permanentemente

    Returns:
        None: Respuesta vacía con código 204

    Raises:
        HTTPException 404: Si la lonchera no existe
    """
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera:
        raise HTTPException(status_code=404, detail="Lonchera no encontrada")

    if hard_delete:
        session.delete(lonchera)
    else:
        lonchera.is_active = False

    session.commit()
    return


@router.post("/{lonchera_id}/alimento", status_code=201)
async def agregar_alimento(
        lonchera_id: int,
        data: AgregarAlimento,
        session: SessionDep
):
    """
    Agrega un alimento a la lonchera con cantidad específica.

    Recalcula automáticamente calorías y precio total de la lonchera.

    Args:
        lonchera_id: ID de la lonchera
        data: Datos del alimento (alimento_id, cantidad_gramos)
        session: Sesión de base de datos

    Returns:
        dict: Confirmación con detalles del alimento agregado

    Raises:
        HTTPException 404: Si la lonchera o alimento no existen
        HTTPException 400: Si la cantidad es inválida
    """
    if data.cantidad_gramos <= 0:
        raise HTTPException(
            status_code=400,
            detail="La cantidad debe ser mayor a 0"
        )

    lonchera = session.get(Lonchera, lonchera_id)
    alimento = session.get(Alimento, data.alimento_id)

    if not lonchera or not lonchera.is_active:
        raise HTTPException(status_code=404, detail="Lonchera no encontrada o inactiva")
    if not alimento or not alimento.is_active:
        raise HTTPException(status_code=404, detail="Alimento no encontrado o inactivo")

    # Verificar si ya existe el alimento en la lonchera
    existing = session.query(LoncheraAlimento).filter(
        LoncheraAlimento.lonchera_id == lonchera_id,
        LoncheraAlimento.alimento_id == data.alimento_id
    ).first()

    if existing:
        # Actualizar cantidad
        existing.cantidad_gramos = data.cantidad_gramos
        mensaje = "Cantidad del alimento actualizada"
    else:
        # Agregar nuevo alimento
        la = LoncheraAlimento(
            lonchera_id=lonchera_id,
            alimento_id=data.alimento_id,
            cantidad_gramos=data.cantidad_gramos
        )
        session.add(la)
        mensaje = "Alimento agregado a la lonchera"

    session.commit()

    # Recalcular totales de la lonchera
    _recalcular_totales_lonchera(lonchera, session)

    # Calcular valores del alimento agregado
    factor = data.cantidad_gramos / 100
    calorias_alimento = factor * alimento.calorias_por_100g
    precio_alimento = factor * alimento.precio_unitario

    return {
        "message": mensaje,
        "lonchera_id": lonchera_id,
        "alimento": {
            "id": alimento.id,
            "nombre": alimento.nombre,
            "cantidad_gramos": data.cantidad_gramos,
            "calorias_aportadas": round(calorias_alimento, 2),
            "precio_aportado": round(precio_alimento, 2)
        },
        "totales_lonchera": {
            "calorias": lonchera.calorias,
            "precio": lonchera.precio
        }
    }


@router.delete("/{lonchera_id}/alimento/{alimento_id}", status_code=204)
async def quitar_alimento(
        lonchera_id: int,
        alimento_id: int,
        session: SessionDep
):
    """
    Quita un alimento de la lonchera.

    Recalcula automáticamente calorías y precio total.

    Args:
        lonchera_id: ID de la lonchera
        alimento_id: ID del alimento a quitar
        session: Sesión de base de datos

    Returns:
        None: Respuesta vacía con código 204

    Raises:
        HTTPException 404: Si la relación no existe
    """
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera:
        raise HTTPException(status_code=404, detail="Lonchera no encontrada")

    la = session.query(LoncheraAlimento).filter(
        LoncheraAlimento.lonchera_id == lonchera_id,
        LoncheraAlimento.alimento_id == alimento_id
    ).first()

    if not la:
        raise HTTPException(
            status_code=404,
            detail="El alimento no está en la lonchera"
        )

    session.delete(la)
    session.commit()

    # Recalcular totales
    _recalcular_totales_lonchera(lonchera, session)

    return


@router.get("/{lonchera_id}/alimentos")
async def listar_alimentos_lonchera(lonchera_id: int, session: SessionDep):
    """
    Lista todos los alimentos de una lonchera con información nutricional detallada.

    Args:
        lonchera_id: ID de la lonchera
        session: Sesión de base de datos

    Returns:
        dict: Información completa de la lonchera y sus alimentos

    Raises:
        HTTPException 404: Si la lonchera no existe
    """
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera:
        raise HTTPException(status_code=404, detail="Lonchera no encontrada")

    alimentos_info = []
    total_calorias = 0
    total_proteinas = 0
    total_carbohidratos = 0
    total_grasas = 0
    total_precio = 0

    for la in lonchera.alimentos:
        factor = la.cantidad_gramos / 100
        calorias = factor * la.alimento.calorias_por_100g
        proteinas = factor * la.alimento.proteinas_por_100g
        carbohidratos = factor * la.alimento.carbohidratos_por_100g
        grasas = factor * la.alimento.grasas_por_100g
        precio = factor * la.alimento.precio_unitario

        alimentos_info.append({
            "alimento_id": la.alimento_id,
            "nombre": la.alimento.nombre,
            "categoria": la.alimento.categoria,
            "cantidad_gramos": la.cantidad_gramos,
            "calorias": round(calorias, 2),
            "proteinas": round(proteinas, 2),
            "carbohidratos": round(carbohidratos, 2),
            "grasas": round(grasas, 2),
            "precio": round(precio, 2)
        })

        total_calorias += calorias
        total_proteinas += proteinas
        total_carbohidratos += carbohidratos
        total_grasas += grasas
        total_precio += precio

    return {
        "lonchera_id": lonchera_id,
        "nombre": lonchera.nombre,
        "descripcion": lonchera.descripcion,
        "alimentos": alimentos_info,
        "totales": {
            "calorias": round(total_calorias, 2),
            "proteinas": round(total_proteinas, 2),
            "carbohidratos": round(total_carbohidratos, 2),
            "grasas": round(total_grasas, 2),
            "precio": round(total_precio, 2)
        },
        "total_alimentos": len(alimentos_info)
    }


@router.get("/{lonchera_id}/completo")
async def obtener_lonchera_completa(lonchera_id: int, session: SessionDep):
    """
    Obtiene información completa de la lonchera con usuario y alimentos.

    Args:
        lonchera_id: ID de la lonchera
        session: Sesión de base de datos

    Returns:
        dict: Lonchera con usuario (1:N) y alimentos (N:M)

    Raises:
        HTTPException 404: Si la lonchera no existe
    """
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera:
        raise HTTPException(status_code=404, detail="Lonchera no encontrada")

    usuario_info = {
        "id": lonchera.usuario.id,
        "nombre": lonchera.usuario.nombre,
        "apellido": lonchera.usuario.apellido,
        "rol": lonchera.usuario.rol,
        "edad": lonchera.usuario.edad
    }

    alimentos_info = []
    for la in lonchera.alimentos:
        alimentos_info.append({
            "id": la.alimento.id,
            "nombre": la.alimento.nombre,
            "cantidad_gramos": la.cantidad_gramos,
            "categoria": la.alimento.categoria
        })

    return {
        "lonchera": {
            "id": lonchera.id,
            "nombre": lonchera.nombre,
            "descripcion": lonchera.descripcion,
            "precio": lonchera.precio,
            "calorias": lonchera.calorias,
            "fecha_creacion": lonchera.fecha_creacion,
            "is_active": lonchera.is_active
        },
        "usuario": usuario_info,
        "alimentos": alimentos_info,
        "total_alimentos": len(alimentos_info)
    }


@router.get("/{lonchera_id}/validar-restricciones")
async def validar_restricciones_lonchera(
        lonchera_id: int,
        restriccion_ids: List[int] = Query(default=[]),
        session: SessionDep = None
):
    """
    Valida si la lonchera contiene alimentos con restricciones específicas.

    Útil para verificar alergias antes de consumir la lonchera.

    Args:
        lonchera_id: ID de la lonchera
        restriccion_ids: Lista de IDs de restricciones a verificar
        session: Sesión de base de datos

    Returns:
        dict: Análisis de compatibilidad con restricciones

    Raises:
        HTTPException 404: Si la lonchera no existe

    Example:
        GET /lonchera/5/validar-restricciones?restriccion_ids=1&restriccion_ids=3
    """
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera:
        raise HTTPException(status_code=404, detail="Lonchera no encontrada")

    if not restriccion_ids:
        return {
            "lonchera_id": lonchera_id,
            "mensaje": "No se especificaron restricciones para validar",
            "es_segura": True,
            "alimentos_problematicos": []
        }

    # Obtener alimentos con las restricciones especificadas
    alimentos_restringidos = {}
    for restriccion_id in restriccion_ids:
        asociaciones = session.query(RestriccionAlimento).filter(
            RestriccionAlimento.restriccion_id == restriccion_id
        ).all()
        for asoc in asociaciones:
            alimentos_restringidos[asoc.alimento_id] = restriccion_id

    # Verificar alimentos de la lonchera
    alimentos_problematicos = []
    for la in lonchera.alimentos:
        if la.alimento_id in alimentos_restringidos:
            alimentos_problematicos.append({
                "alimento_id": la.alimento.id,
                "nombre": la.alimento.nombre,
                "cantidad_gramos": la.cantidad_gramos,
                "restriccion_id": alimentos_restringidos[la.alimento_id]
            })

    es_segura = len(alimentos_problematicos) == 0

    return {
        "lonchera_id": lonchera_id,
        "nombre_lonchera": lonchera.nombre,
        "es_segura": es_segura,
        "total_alimentos": len(lonchera.alimentos),
        "alimentos_problematicos": alimentos_problematicos,
        "mensaje": "Lonchera segura" if es_segura else "⚠️ Contiene alimentos con restricciones"
    }


def _recalcular_totales_lonchera(lonchera: Lonchera, session: SessionDep):
    """
    Función auxiliar para recalcular calorías y precio total de una lonchera.

    Args:
        lonchera: Instancia de la lonchera
        session: Sesión de base de datos
    """
    total_calorias = 0
    total_precio = 0

    for la in lonchera.alimentos:
        factor = la.cantidad_gramos / 100
        total_calorias += factor * la.alimento.calorias_por_100g
        total_precio += factor * la.alimento.precio_unitario

    lonchera.calorias = int(round(total_calorias))
    lonchera.precio = round(total_precio, 2)

    session.commit()
    session.refresh(lonchera)