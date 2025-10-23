from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from typing import List
from Datos.models import Lonchera, LoncheraCreate, LoncheraAlimento, Alimento, Usuario
from Aplicacion.db import SessionDep

router = APIRouter(prefix="/loncheras", tags=["Loncheras"])


# ========================================
# RELACIÓN 1:N - Usuario → Lonchera
# Un usuario puede tener MUCHAS loncheras
# Una lonchera pertenece a UN usuario
# ========================================


@router.post("/", response_model=Lonchera, status_code=status.HTTP_201_CREATED)
async def crear_lonchera(data: LoncheraCreate, session: SessionDep):
    usuario = session.get(Usuario, data.usuario_id)
    if not usuario or not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado o inactivo"
        )

    lonchera = Lonchera(**data.dict())
    session.add(lonchera)
    session.commit()
    session.refresh(lonchera)
    return lonchera


@router.get("/", response_model=List[Lonchera])
async def obtener_loncheras(
        session: SessionDep,
        usuario_id: int = None,
        incluir_inactivas: bool = False
):
    query = select(Lonchera)

    if usuario_id:
        query = query.where(Lonchera.usuario_id == usuario_id)

    if not incluir_inactivas:
        query = query.where(Lonchera.is_active == True)

    loncheras = session.exec(query).all()
    return loncheras


@router.get("/{lonchera_id}", response_model=Lonchera)
async def obtener_lonchera(lonchera_id: int, session: SessionDep):
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera or not lonchera.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lonchera no encontrada"
        )
    return lonchera


@router.put("/{lonchera_id}", response_model=Lonchera)
async def actualizar_lonchera(lonchera_id: int, data: LoncheraCreate, session: SessionDep):
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera or not lonchera.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lonchera no encontrada"
        )

    for key, value in data.dict(exclude_unset=True).items():
        setattr(lonchera, key, value)

    session.add(lonchera)
    session.commit()
    session.refresh(lonchera)
    return lonchera


@router.delete("/{lonchera_id}", status_code=status.HTTP_200_OK)
async def eliminar_lonchera(lonchera_id: int, session: SessionDep, hard_delete: bool = False):
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lonchera no encontrada"
        )

    if hard_delete:
        session.delete(lonchera)
        mensaje = "Lonchera eliminada permanentemente"
    else:
        lonchera.is_active = False
        session.add(lonchera)
        mensaje = "Lonchera desactivada"

    session.commit()
    return {"message": mensaje, "id": lonchera_id}


# ========================================
# RELACIÓN N:M - Lonchera ↔ Alimento
# Una lonchera tiene MUCHOS alimentos
# Un alimento puede estar en MUCHAS loncheras
# Tabla intermedia: LoncheraAlimento
# ========================================


@router.post("/{lonchera_id}/alimentos/{alimento_id}", status_code=status.HTTP_201_CREATED)
async def agregar_alimento_a_lonchera(
        lonchera_id: int,
        alimento_id: int,
        cantidad_gramos: float,
        session: SessionDep
):
    if cantidad_gramos <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cantidad debe ser mayor a 0"
        )

    lonchera = session.get(Lonchera, lonchera_id)
    alimento = session.get(Alimento, alimento_id)

    if not lonchera or not lonchera.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lonchera no encontrada o inactiva"
        )

    if not alimento or not alimento.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alimento no encontrado o inactivo"
        )

    existing = session.exec(
        select(LoncheraAlimento).where(
            LoncheraAlimento.lonchera_id == lonchera_id,
            LoncheraAlimento.alimento_id == alimento_id
        )
    ).first()

    if existing:
        existing.cantidad_gramos = cantidad_gramos
        session.add(existing)
        mensaje = "Cantidad actualizada"
    else:
        la = LoncheraAlimento(
            lonchera_id=lonchera_id,
            alimento_id=alimento_id,
            cantidad_gramos=cantidad_gramos
        )
        session.add(la)
        mensaje = "Alimento agregado a la lonchera"

    session.commit()
    return {
        "message": mensaje,
        "lonchera_id": lonchera_id,
        "alimento_id": alimento_id,
        "cantidad_gramos": cantidad_gramos
    }


@router.delete("/{lonchera_id}/alimentos/{alimento_id}", status_code=status.HTTP_200_OK)
async def quitar_alimento_de_lonchera(
        lonchera_id: int,
        alimento_id: int,
        session: SessionDep
):
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lonchera no encontrada"
        )

    la = session.exec(
        select(LoncheraAlimento).where(
            LoncheraAlimento.lonchera_id == lonchera_id,
            LoncheraAlimento.alimento_id == alimento_id
        )
    ).first()

    if not la:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alimento no encontrado en la lonchera"
        )

    session.delete(la)
    session.commit()
    return {"message": "Alimento eliminado de la lonchera"}


@router.get("/{lonchera_id}/alimentos")
async def listar_alimentos_lonchera(lonchera_id: int, session: SessionDep):
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lonchera no encontrada"
        )

    alimentos_info = []
    total_calorias = 0
    total_proteinas = 0
    total_carbohidratos = 0
    total_grasas = 0

    for la in lonchera.alimentos:
        factor = la.cantidad_gramos / 100
        calorias = factor * la.alimento.calorias_por_100g
        proteinas = factor * la.alimento.proteinas_por_100g
        carbohidratos = factor * la.alimento.carbohidratos_por_100g
        grasas = factor * la.alimento.grasas_por_100g

        alimentos_info.append({
            "alimento_id": la.alimento_id,
            "nombre": la.alimento.nombre,
            "categoria": la.alimento.categoria,
            "cantidad_gramos": la.cantidad_gramos,
            "calorias_totales": round(calorias, 2),
            "proteinas_totales": round(proteinas, 2),
            "carbohidratos_totales": round(carbohidratos, 2),
            "grasas_totales": round(grasas, 2)
        })

        total_calorias += calorias
        total_proteinas += proteinas
        total_carbohidratos += carbohidratos
        total_grasas += grasas

    return {
        "lonchera_id": lonchera_id,
        "nombre_lonchera": lonchera.nombre,
        "alimentos": alimentos_info,
        "totales": {
            "calorias": round(total_calorias, 2),
            "proteinas": round(total_proteinas, 2),
            "carbohidratos": round(total_carbohidratos, 2),
            "grasas": round(total_grasas, 2)
        }
    }


@router.get("/{lonchera_id}/completo")
async def obtener_lonchera_completa(lonchera_id: int, session: SessionDep):
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lonchera no encontrada"
        )

    usuario_info = {
        "id": lonchera.usuario.id,
        "nombre": lonchera.usuario.nombre,
        "apellido": lonchera.usuario.apellido,
        "rol": lonchera.usuario.rol
    }

    alimentos_info = []
    for la in lonchera.alimentos:
        alimentos_info.append({
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
            "fecha_creacion": lonchera.fecha_creacion
        },
        "usuario": usuario_info,  # Relación 1:N
        "alimentos": alimentos_info,  # Relación N:M
        "total_alimentos": len(alimentos_info)
    }