from fastapi import APIRouter, HTTPException, Depends
from Core.database import SessionDep
from sqlmodel import select
from typing import List
from Core.auth import get_current_user
# IMPORTACIÓN CLAVE: Usamos los modelos de models.py para que no haya conflictos
from Modulos.models import Usuario, Direccion, DireccionCreate, DireccionUpdate

router = APIRouter(prefix="/direcciones", tags=["Direcciones"])

@router.post("/", response_model=Direccion, status_code=201)
async def crear_direccion(
        data: DireccionCreate,
        session: SessionDep,
        current_user: Usuario = Depends(get_current_user)
):
    # Si marca como principal, desmarcar las demás
    if data.principal:
        query = select(Direccion).where(
            Direccion.usuario_id == current_user.id,
            Direccion.principal == True
        )
        result = await session.execute(query)
        direcciones_principales = result.scalars().all()
        for dir in direcciones_principales:
            dir.principal = False
            session.add(dir)

    # Crear la dirección usando el modelo de la base de datos
    direccion = Direccion(
        **data.model_dump(),
        usuario_id=current_user.id
    )
    session.add(direccion)
    await session.commit()
    await session.refresh(direccion)
    return direccion

@router.get("/", response_model=List[Direccion])
async def listar_direcciones(
        session: SessionDep,
        current_user: Usuario = Depends(get_current_user)
):
    # Filtrar solo las direcciones del usuario actual
    query = select(Direccion).where(Direccion.usuario_id == current_user.id)
    result = await session.execute(query)
    return result.scalars().all()

@router.get("/{direccion_id}", response_model=Direccion)
async def obtener_direccion(
        direccion_id: int,
        session: SessionDep,
        current_user: Usuario = Depends(get_current_user)
):
    direccion = await session.get(Direccion, direccion_id)
    if not direccion:
        raise HTTPException(status_code=404, detail="Dirección no encontrada")

    if direccion.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver esta dirección")

    return direccion

@router.put("/{direccion_id}", response_model=Direccion)
async def actualizar_direccion(
        direccion_id: int,
        data: DireccionUpdate,
        session: SessionDep,
        current_user: Usuario = Depends(get_current_user)
):
    direccion = await session.get(Direccion, direccion_id)
    if not direccion:
        raise HTTPException(status_code=404, detail="Dirección no encontrada")

    if direccion.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para editar esta dirección")

    if data.principal:
        query = select(Direccion).where(
            Direccion.usuario_id == current_user.id,
            Direccion.principal == True,
            Direccion.id != direccion_id
        )
        result = await session.execute(query)
        direcciones_principales = result.scalars().all()
        for dir in direcciones_principales:
            dir.principal = False
            session.add(dir)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(direccion, key, value)

    session.add(direccion)
    await session.commit()
    await session.refresh(direccion)
    return direccion

@router.put("/{direccion_id}/principal", response_model=Direccion)
async def establecer_principal(
        direccion_id: int,
        session: SessionDep,
        current_user: Usuario = Depends(get_current_user)
):
    direccion = await session.get(Direccion, direccion_id)
    if not direccion:
        raise HTTPException(status_code=404, detail="Dirección no encontrada")

    if direccion.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso")

    query = select(Direccion).where(
        Direccion.usuario_id == current_user.id,
        Direccion.principal == True
    )
    result = await session.execute(query)
    direcciones_principales = result.scalars().all()
    for dir in direcciones_principales:
        dir.principal = False
        session.add(dir)

    direccion.principal = True
    session.add(direccion)
    await session.commit()
    await session.refresh(direccion)
    return direccion

@router.delete("/{direccion_id}", status_code=204)
async def eliminar_direccion(
        direccion_id: int,
        session: SessionDep,
        current_user: Usuario = Depends(get_current_user)
):
    direccion = await session.get(Direccion, direccion_id)
    if not direccion:
        raise HTTPException(status_code=404, detail="Dirección no encontrada")

    if direccion.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta dirección")

    await session.delete(direccion)
    await session.commit()
    return