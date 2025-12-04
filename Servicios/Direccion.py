from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from typing import List
from Core.database import SessionDep
from Modulos.models import Usuario, Direccion, DireccionCreate, DireccionUpdate

router = APIRouter()


# ====================================================================
# LISTAR TODAS LAS DIRECCIONES POR USUARIO (QUERY PARAM)
# ====================================================================
@router.get("/direcciones/", response_model=List[Direccion], tags=["Direcciones"])
async def listar_direcciones(
        usuario_id: int,
        session: SessionDep
):
    """
    Lista todas las direcciones de un usuario específico usando query parameter.
    Ejemplo: GET /direcciones/?usuario_id=1
    """
    # Verificar que el usuario existe
    usuario = await session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail=f"Usuario con ID {usuario_id} no encontrado")

    # Obtener todas las direcciones del usuario
    statement = select(Direccion).where(Direccion.usuario_id == usuario_id)
    result = await session.execute(statement)
    direcciones = result.scalars().all()

    return direcciones


# ====================================================================
# CREAR DIRECCIÓN
# ====================================================================
@router.post("/usuarios/{usuario_id}/direcciones", response_model=Direccion, tags=["Direcciones"])
async def crear_direccion(
        usuario_id: int,
        direccion_data: DireccionCreate,
        session: SessionDep
):
    """
    Crea una nueva dirección para un usuario específico.
    """
    # Verificar que el usuario existe
    usuario = await session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail=f"Usuario con ID {usuario_id} no encontrado")

    # Si la nueva dirección es principal, quitar el flag de las demás
    if direccion_data.principal:
        statement = select(Direccion).where(Direccion.usuario_id == usuario_id)
        result = await session.execute(statement)
        direcciones_existentes = result.scalars().all()
        for dir_existente in direcciones_existentes:
            dir_existente.principal = False
            session.add(dir_existente)

    # Crear la nueva dirección
    nueva_direccion = Direccion(
        **direccion_data.model_dump(),
        usuario_id=usuario_id
    )

    session.add(nueva_direccion)
    await session.commit()
    await session.refresh(nueva_direccion)

    return nueva_direccion


# ====================================================================
# LISTAR DIRECCIONES DE UN USUARIO
# ====================================================================
@router.get("/usuarios/{usuario_id}/direcciones", response_model=List[Direccion], tags=["Direcciones"])
async def listar_direcciones_usuario(
        usuario_id: int,
        session: SessionDep
):
    """
    Lista todas las direcciones de un usuario específico.
    """
    # Verificar que el usuario existe
    usuario = await session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail=f"Usuario con ID {usuario_id} no encontrado")

    # Obtener todas las direcciones del usuario
    statement = select(Direccion).where(Direccion.usuario_id == usuario_id)
    result = await session.execute(statement)
    direcciones = result.scalars().all()

    return direcciones


# ====================================================================
# ACTUALIZAR DIRECCIÓN
# ====================================================================
@router.patch("/direcciones/{direccion_id}", response_model=Direccion, tags=["Direcciones"])
async def actualizar_direccion(
        direccion_id: int,
        direccion_data: DireccionUpdate,
        session: SessionDep
):
    """
    Actualiza una dirección existente.
    """
    direccion = await session.get(Direccion, direccion_id)
    if not direccion:
        raise HTTPException(status_code=404, detail=f"Dirección con ID {direccion_id} no encontrada")

    # Si se marca como principal, quitar el flag de las demás direcciones del mismo usuario
    if direccion_data.principal:
        statement = select(Direccion).where(
            Direccion.usuario_id == direccion.usuario_id,
            Direccion.id != direccion_id
        )
        result = await session.execute(statement)
        otras_direcciones = result.scalars().all()
        for otra_dir in otras_direcciones:
            otra_dir.principal = False
            session.add(otra_dir)

    # Actualizar los campos proporcionados
    datos_actualizacion = direccion_data.model_dump(exclude_unset=True)
    for key, value in datos_actualizacion.items():
        setattr(direccion, key, value)

    session.add(direccion)
    await session.commit()
    await session.refresh(direccion)

    return direccion


# ====================================================================
# ELIMINAR DIRECCIÓN
# ====================================================================
@router.delete("/direcciones/{direccion_id}", tags=["Direcciones"])
async def eliminar_direccion(
        direccion_id: int,
        session: SessionDep
):
    """
    Elimina una dirección específica.
    """
    direccion = await session.get(Direccion, direccion_id)
    if not direccion:
        raise HTTPException(status_code=404, detail=f"Dirección con ID {direccion_id} no encontrada")

    # Verificar si hay loncheras asociadas a esta dirección
    if direccion.loncheras:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar la dirección porque tiene {len(direccion.loncheras)} lonchera(s) asociada(s)"
        )

    await session.delete(direccion)
    await session.commit()

    return {"mensaje": f"Dirección con ID {direccion_id} eliminada exitosamente"}


# ====================================================================
# MARCAR DIRECCIÓN COMO PRINCIPAL
# ====================================================================
@router.post("/direcciones/{direccion_id}/principal", response_model=Direccion, tags=["Direcciones"])
async def marcar_como_principal(
        direccion_id: int,
        session: SessionDep
):
    """
    Marca una dirección como principal y quita el flag de las demás direcciones del usuario.
    """
    direccion = await session.get(Direccion, direccion_id)
    if not direccion:
        raise HTTPException(status_code=404, detail=f"Dirección con ID {direccion_id} no encontrada")

    # Quitar el flag principal de todas las direcciones del usuario
    statement = select(Direccion).where(
        Direccion.usuario_id == direccion.usuario_id,
        Direccion.id != direccion_id
    )
    result = await session.execute(statement)
    otras_direcciones = result.scalars().all()
    for otra_dir in otras_direcciones:
        otra_dir.principal = False
        session.add(otra_dir)

    # Marcar esta dirección como principal
    direccion.principal = True
    session.add(direccion)
    await session.commit()
    await session.refresh(direccion)

    return direccion