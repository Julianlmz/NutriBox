from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from typing import List
from Datos.models import Lonchera, LoncheraCreate
from Aplicacion.db import SessionDep

router = APIRouter(prefix="/loncheras", tags=["Loncheras"])

@router.post("/", response_model=Lonchera, status_code=status.HTTP_201_CREATED)
async def crear_lonchera(data: LoncheraCreate, session: SessionDep):
    lonchera = Lonchera(**data.dict())
    session.add(lonchera)
    session.commit()
    session.refresh(lonchera)
    return lonchera

@router.get("/", response_model=List[Lonchera])
async def obtener_loncheras(session: SessionDep):
    loncheras = session.exec(select(Lonchera)).all()
    return loncheras

@router.get("/{lonchera_id}", response_model=Lonchera)
async def obtener_lonchera(lonchera_id: int, session: SessionDep):
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera:
        raise HTTPException(status_code=404, detail="Lonchera no encontrada")
    return lonchera

@router.put("/{lonchera_id}", response_model=Lonchera)
async def actualizar_lonchera(lonchera_id: int, data: LoncheraCreate, session: SessionDep):
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera:
        raise HTTPException(status_code=404, detail="Lonchera no encontrada")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(lonchera, key, value)
    session.add(lonchera)
    session.commit()
    session.refresh(lonchera)
    return lonchera

@router.delete("/{lonchera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_lonchera(lonchera_id: int, session: SessionDep):
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera:
        raise HTTPException(status_code=404, detail="Lonchera no encontrada")
    session.delete(lonchera)
    session.commit()
