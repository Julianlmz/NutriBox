from fastapi import APIRouter, HTTPException
from Core.database import SessionDep
from sqlmodel import SQLModel, Field, select
from typing import Optional, List
from datetime import datetime


class DireccionBase(SQLModel):
    nombre: str = Field(min_length=3, max_length=100)
    direccion: str = Field(min_length=10, max_length=200)
    ciudad: str = Field(max_length=100)
    codigo_postal: Optional[str] = None
    telefono: Optional[str] = None
    es_principal: bool = Field(default=False)


class Direccion(DireccionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id")
    fecha_creacion: datetime = Field(default_factory=datetime.now)


router = APIRouter(prefix="/direcciones", tags=["Direcciones"])


@router.post("/", response_model=Direccion, status_code=201)
async def crear_direccion(data: DireccionBase, usuario_id: int, session: SessionDep):
    direccion = Direccion(**data.model_dump(), usuario_id=usuario_id)
    session.add(direccion)
    await session.commit()
    await session.refresh(direccion)
    return direccion


@router.get("/", response_model=List[Direccion])
async def listar_direcciones(usuario_id: Optional[int] = None, session: SessionDep = None):
    query = select(Direccion)
    if usuario_id:
        query = query.where(Direccion.usuario_id == usuario_id)

    result = await session.execute(query)
    return result.scalars().all()


@router.delete("/{direccion_id}", status_code=204)
async def eliminar_direccion(direccion_id: int, session: SessionDep):
    direccion = await session.get(Direccion, direccion_id)
    if not direccion:
        raise HTTPException(status_code=404, detail="Dirección no encontrada")

    await session.delete(direccion)
    await session.commit()
    return