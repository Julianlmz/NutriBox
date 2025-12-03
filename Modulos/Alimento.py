from fastapi import APIRouter, HTTPException, Query, File, UploadFile, Form, Depends
from sqlmodel import select
from sqlalchemy.orm import selectinload
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
        nombre: str = Form(...),
        categoria: str = Form(...),
        calorias_por_100g: float = Form(...),
        proteinas_por_100g: float = Form(...),
        carbohidratos_por_100g: float = Form(...),
        grasas_por_100g: float = Form(...),
        precio_unitario: float = Form(...),
        stock_inicial: int = Form(0),
        # LÓGICA TIPO HIJOS:
        tipo_imagen: str = Form("file"),  # Recibe "file" (archivo) o "url"
        imagen_url: Optional[str] = Form(None),  # URL directa
        imagen: Optional[UploadFile] = File(None)  # Archivo
):
    final_imagen_url = None

    # Lógica idéntica a Hijo.py
    if tipo_imagen == "file" and imagen and imagen.filename:
        final_imagen_url = await upload_to_bucket(imagen)
    elif tipo_imagen == "url" and imagen_url:
        final_imagen_url = imagen_url

    query = select(Alimento).where(Alimento.nombre == nombre)
    result = await session.execute(query)
    if result.scalars().first():
        raise HTTPException(status_code=409, detail=f"Ya existe un alimento con el nombre '{nombre}'")

    alimento = Alimento(
        nombre=nombre,
        categoria=categoria,
        calorias_por_100g=calorias_por_100g,
        proteinas_por_100g=proteinas_por_100g,
        carbohidratos_por_100g=carbohidratos_por_100g,
        grasas_por_100g=grasas_por_100g,
        precio_unitario=precio_unitario,
        stock_actual=0,
        imagen_url=final_imagen_url  # Usamos la URL procesada
    )

    session.add(alimento)
    await session.commit()
    await session.refresh(alimento)
    return alimento


@router.get("/", response_model=List[Alimento])
async def listar_alimentos(
        incluir_inactivos: bool = Query(default=False),
        session: SessionDep = None
):
    query = select(Alimento)
    if not incluir_inactivos:
        query = query.where(Alimento.is_active == True)
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/{alimento_id}", response_model=Alimento)
async def obtener_alimento(alimento_id: int, session: SessionDep):
    alimento = await session.get(Alimento, alimento_id)
    if not alimento or not alimento.is_active:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")
    return alimento


@router.patch("/{alimento_id}", response_model=Alimento)
async def actualizar_parcial_alimento(
        alimento_id: int,
        data: AlimentoUpdate,
        session: SessionDep
):
    alimento = await session.get(Alimento, alimento_id)
    if not alimento or not alimento.is_active:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")

    update_data = data.model_dump(exclude_unset=True)
    if 'stock_actual' in update_data: del update_data['stock_actual']

    for key, value in update_data.items():
        setattr(alimento, key, value)

    session.add(alimento)
    await session.commit()
    await session.refresh(alimento)
    return alimento


@router.delete("/{alimento_id}", status_code=204)
async def eliminar_alimento(alimento_id: int, session: SessionDep):
    alimento = await session.get(Alimento, alimento_id)
    if not alimento:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")

    alimento.is_active = False
    session.add(alimento)
    await session.commit()
    return


@router.post("/{alimento_id}/upload-image", response_model=Alimento)
async def subir_imagen_alimento(alimento_id: int, session: SessionDep, imagen: UploadFile = File(...)):
    alimento = await session.get(Alimento, alimento_id)
    if not alimento:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")

    alimento.imagen_url = await upload_to_bucket(imagen)
    session.add(alimento)
    await session.commit()
    await session.refresh(alimento)
    return alimento