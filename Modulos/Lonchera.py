from fastapi import APIRouter, HTTPException, Query, Depends
from Core.database import SessionDep
from Modulos.models import (
    Lonchera, LoncheraCreate, LoncheraUpdate, LoncheraAlimento,
    AgregarAlimento, Usuario, Alimento, RestriccionAlimento,
    Direccion  # Importamos la dirección del modelo
)
from typing import List, Annotated
from Core.auth import get_current_user
from sqlmodel import select
from sqlalchemy.orm import selectinload

router = APIRouter(tags=["Loncheras"], prefix="/lonchera")


@router.post("/", response_model=Lonchera, status_code=201)
async def crear_lonchera(data: LoncheraCreate, session: SessionDep):
    """
    Crea una nueva lonchera para un usuario, validando el hijo y la dirección.
    """
    # 1. Validar Usuario (Padre, que es el creador/dueño de la dirección)
    usuario = await session.get(Usuario, data.usuario_id)
    if not usuario or not usuario.is_active:
        raise HTTPException(status_code=404, detail="Usuario (creador/padre) no encontrado o inactivo")

    # 2. Validar Dirección
    if data.direccion_id:
        direccion = await session.get(Direccion, data.direccion_id)
        if not direccion:
            raise HTTPException(status_code=404, detail="Dirección no encontrada")

        # Seguridad: Verificar que la dirección pertenezca al usuario creador
        if direccion.usuario_id != data.usuario_id:
            raise HTTPException(status_code=403, detail="La dirección no pertenece al usuario creador")
    else:
        raise HTTPException(status_code=400, detail="Se requiere una dirección de entrega")

    # 3. Crear Lonchera
    lonchera = Lonchera(**data.model_dump())
    session.add(lonchera)

    await session.commit()
    await session.refresh(lonchera)
    return lonchera


@router.get("/", response_model=List[Lonchera])
async def listar_loncheras_del_usuario_actual(
        session: SessionDep,
        current_user: Annotated[Usuario, Depends(get_current_user)],
        incluir_inactivas: bool = Query(default=False)
):
    """
    Lista las loncheras del usuario actual.
    """
    # Consulta con eager loading para traer la dirección si es necesario
    query = select(Lonchera).where(Lonchera.usuario_id == current_user.id).options(
        selectinload(Lonchera.direccion)
    )

    if not incluir_inactivas:
        query = query.where(Lonchera.is_active == True)

    result = await session.execute(query)
    loncheras = result.scalars().all()
    return loncheras


@router.get("/{lonchera_id}", response_model=Lonchera)
async def obtener_lonchera(lonchera_id: int, session: SessionDep):
    """
    Obtiene una lonchera por ID cargando sus alimentos y dirección.
    """
    query = select(Lonchera).where(Lonchera.id == lonchera_id).options(
        selectinload(Lonchera.alimentos).selectinload(LoncheraAlimento.alimento),
        selectinload(Lonchera.direccion)  # Incluir la dirección en la carga
    )
    result = await session.execute(query)
    lonchera = result.scalars().first()

    if not lonchera or not lonchera.is_active:
        raise HTTPException(status_code=404, detail="Lonchera no encontrada")
    return lonchera


# --- Resto del código se mantiene igual ---

@router.patch("/{lonchera_id}", response_model=Lonchera)
async def actualizar_lonchera(
        lonchera_id: int,
        data: LoncheraUpdate,
        session: SessionDep
):
    lonchera = await obtener_lonchera(lonchera_id, session)

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No se proporcionaron datos para actualizar"
        )

    for key, value in update_data.items():
        setattr(lonchera, key, value)

    session.add(lonchera)
    await session.commit()
    await session.refresh(lonchera)
    return lonchera


@router.delete("/{lonchera_id}", status_code=204)
async def eliminar_lonchera(
        lonchera_id: int,
        session: SessionDep,
        hard_delete: bool = Query(default=False)
):
    lonchera = await session.get(Lonchera, lonchera_id)
    if not lonchera:
        raise HTTPException(status_code=404, detail="Lonchera no encontrada")

    if hard_delete:
        await session.delete(lonchera)
    else:
        lonchera.is_active = False
        session.add(lonchera)

    await session.commit()
    return


@router.post("/{lonchera_id}/alimento", status_code=201)
async def agregar_alimento(
        lonchera_id: int,
        data: AgregarAlimento,
        session: SessionDep
):
    lonchera = await obtener_lonchera(lonchera_id, session)
    alimento = await session.get(Alimento, data.alimento_id)

    if not alimento or not alimento.is_active:
        raise HTTPException(status_code=404, detail="Alimento no encontrado o inactivo")

    if data.cantidad_gramos <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a 0")

    query = select(LoncheraAlimento).where(
        LoncheraAlimento.lonchera_id == lonchera_id,
        LoncheraAlimento.alimento_id == data.alimento_id
    )
    result = await session.execute(query)
    existing = result.scalars().first()

    if existing:
        existing.cantidad_gramos = data.cantidad_gramos
        mensaje = "Cantidad del alimento actualizada"
        session.add(existing)
    else:
        la = LoncheraAlimento(
            lonchera_id=lonchera_id,
            alimento_id=data.alimento_id,
            cantidad_gramos=data.cantidad_gramos
        )
        session.add(la)
        mensaje = "Alimento agregado a la lonchera"

    await session.commit()

    await session.refresh(lonchera)
    await _recalcular_totales_lonchera(lonchera, session)

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
    lonchera = await obtener_lonchera(lonchera_id, session)

    query = select(LoncheraAlimento).where(
        LoncheraAlimento.lonchera_id == lonchera_id,
        LoncheraAlimento.alimento_id == alimento_id
    )
    result = await session.execute(query)
    la = result.scalars().first()

    if not la:
        raise HTTPException(
            status_code=404,
            detail="El alimento no está en la lonchera"
        )

    await session.delete(la)
    await session.commit()

    await session.refresh(lonchera)
    await _recalcular_totales_lonchera(lonchera, session)
    return


@router.get("/{lonchera_id}/alimentos")
async def listar_alimentos_lonchera(lonchera_id: int, session: SessionDep):
    lonchera = await obtener_lonchera(lonchera_id, session)

    alimentos_info = []
    total_calorias = 0
    total_proteinas = 0
    total_carbohidratos = 0
    total_grasas = 0
    total_precio = 0

    for la in lonchera.alimentos:
        if not la.alimento: continue

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
    lonchera = await obtener_lonchera(lonchera_id, session)

    usuario = await session.get(Usuario, lonchera.usuario_id)

    usuario_info = {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "apellido": usuario.apellido
    }

    alimentos_info = []
    for la in lonchera.alimentos:
        if not la.alimento: continue
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
            "is_active": lonchera.is_active,
            # Incluir la dirección de entrega
            "direccion_entrega": f"{lonchera.direccion.direccion} ({lonchera.direccion.nombre})" if lonchera.direccion else "No asignada"
        },
        "usuario": usuario_info,
        "alimentos": alimentos_info,
        "total_alimentos": len(alimentos_info)
    }


@router.get("/{lonchera_id}/validar-restricciones")
async def validar_restricciones_lonchera(
        lonchera_id: int,
        session: SessionDep,
        restriccion_ids: List[int] = Query(default=[])
):
    lonchera = await obtener_lonchera(lonchera_id, session)

    if not restriccion_ids:
        return {
            "lonchera_id": lonchera_id,
            "mensaje": "No se especificaron restricciones para validar",
            "es_segura": True,
            "alimentos_problematicos": []
        }

    alimentos_restringidos = {}
    for restriccion_id in restriccion_ids:
        query = select(RestriccionAlimento).where(RestriccionAlimento.restriccion_id == restriccion_id)
        result = await session.execute(query)
        asociaciones = result.scalars().all()

        for asoc in asociaciones:
            alimentos_restringidos[asoc.alimento_id] = restriccion_id

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


async def _recalcular_totales_lonchera(lonchera: Lonchera, session: SessionDep):
    query = select(LoncheraAlimento).where(LoncheraAlimento.lonchera_id == lonchera.id).options(
        selectinload(LoncheraAlimento.alimento))
    result = await session.execute(query)
    items = result.scalars().all()

    total_calorias = 0
    total_precio = 0

    for la in items:
        if la.alimento:
            factor = la.cantidad_gramos / 100
            total_calorias += factor * la.alimento.calorias_por_100g
            total_precio += factor * la.alimento.precio_unitario

    lonchera.calorias = int(round(total_calorias))
    lonchera.precio = round(total_precio, 2)

    session.add(lonchera)
    await session.commit()
    await session.refresh(lonchera)