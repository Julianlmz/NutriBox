from fastapi import APIRouter, HTTPException
from Core.database import SessionDep
from Modulos.models import Usuario, UsuarioCreate
from Core.seguridad import hashear_password
from sqlmodel import select
from typing import List

router = APIRouter(tags=["Hijos"], prefix="/hijo")


@router.post("/", response_model=Usuario, status_code=201)
async def crear_hijo(data: UsuarioCreate, session: SessionDep):
    query = select(Usuario).where(Usuario.email == data.email)
    result = await session.execute(query)
    if result.scalars().first():
        raise HTTPException(status_code=409, detail="Email ya existe")

    password_hash = hashear_password(data.password)
    hijo = Usuario(**data.model_dump(exclude={"password"}), hashed_password=password_hash)

    session.add(hijo)
    await session.commit()
    await session.refresh(hijo)
    return hijo


@router.get("/", response_model=List[Usuario])
async def listar_hijos(session: SessionDep):
    query = select(Usuario).where(Usuario.is_active == True)
    result = await session.execute(query)
    return result.scalars().all()


@router.delete("/{hijo_id}", status_code=204)
async def eliminar_hijo(hijo_id: int, session: SessionDep):
    hijo = await session.get(Usuario, hijo_id)
    if not hijo:
        raise HTTPException(status_code=404, detail="Hijo no encontrado")

    hijo.is_active = False
    session.add(hijo)
    await session.commit()
    return