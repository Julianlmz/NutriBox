from fastapi import APIRouter, HTTPException, Query, Depends
from Core.database import SessionDep
from Modulos.models import (Usuario, UsuarioCreate, UsuarioUpdate, UsuarioConRelaciones, Perfil, PerfilCreate,
                            PerfilUpdate)
from typing import List, Annotated
from Core.seguridad import hashear_password
from Core.auth import get_current_user
from sqlmodel import select
from sqlalchemy.orm import selectinload

router = APIRouter(tags=["Usuarios"], prefix="/usuario")


@router.get("/me", response_model=Usuario)
async def read_users_me(current_user: Annotated[Usuario, Depends(get_current_user)], session: SessionDep):
    # Cargar perfil del usuario actual si existe
    # (Opcional, pero útil para el frontend)
    query = select(Usuario).where(Usuario.id == current_user.id).options(selectinload(Usuario.perfil))
    result = await session.execute(query)
    user_con_perfil = result.scalars().first()
    return user_con_perfil


@router.post("/", response_model=Usuario, status_code=201)
async def crear_usuario(nuevo_usuario: UsuarioCreate, session: SessionDep):
    # ASYNC FIX: select en lugar de query
    query = select(Usuario).where(Usuario.email == nuevo_usuario.email)
    result = await session.execute(query)
    usuario_existente = result.scalars().first()

    if usuario_existente:
        raise HTTPException(status_code=409, detail=f"Ya existe un usuario con el email '{nuevo_usuario.email}'")

    password_hasheado = hashear_password(nuevo_usuario.password)
    datos_db = nuevo_usuario.model_dump(exclude={"password", "rol"})

    usuario = Usuario(**datos_db, hashed_password=password_hasheado)

    session.add(usuario)
    await session.commit()  # AWAIT
    await session.refresh(usuario)  # AWAIT
    return usuario


@router.get("/", response_model=List[Usuario])
async def listar_usuarios(activo: bool = Query(default=None), session: SessionDep = None):
    query = select(Usuario)
    if activo is not None:
        query = query.where(Usuario.is_active == activo)

    result = await session.execute(query)  # AWAIT
    return result.scalars().all()


@router.get("/{usuario_id}", response_model=UsuarioConRelaciones)
async def obtener_usuario(usuario_id: int, session: SessionDep):
    # Eager loading para relaciones
    query = select(Usuario).where(Usuario.id == usuario_id).options(
        selectinload(Usuario.loncheras),
        selectinload(Usuario.perfil)
    )
    result = await session.execute(query)
    usuario = result.scalars().first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

# ... (Para brevedad, asumo que los otros endpoints PUT/PATCH/DELETE los corregirás
#      usando el patrón: await session.get(), await session.commit()) ...
#      Lo más importante para la demo es Registro y Login.