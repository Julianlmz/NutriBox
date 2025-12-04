from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends
from typing import Annotated, Optional
from sqlmodel import select
from Core.database import SessionDep
from Core.auth import get_current_user
from Core.supabase_client import upload_to_bucket
from Modulos.models import Perfil, Usuario

router = APIRouter(prefix="/perfiles", tags=["Perfiles"])


@router.get("/usuario/{usuario_id}", response_model=Perfil)
async def obtener_perfil_por_usuario(usuario_id: int, session: SessionDep):
    # Validación asíncrona de usuario
    usuario = await session.get(Usuario, usuario_id)
    if not usuario or not usuario.is_active:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    query = select(Perfil).where(Perfil.usuario_id == usuario_id)
    result = await session.execute(query)
    perfil = result.scalars().first()

    if not perfil:
        raise HTTPException(status_code=404, detail="El usuario no tiene un perfil creado")
    return perfil


@router.post("/me/foto", response_model=Perfil)
async def subir_foto_perfil(
        session: SessionDep,
        current_user: Annotated[Usuario, Depends(get_current_user)],
        archivo: UploadFile = File(...)
):
    """Sube una foto de perfil para el usuario actual"""

    # 1. Buscar perfil del usuario logueado
    query = select(Perfil).where(Perfil.usuario_id == current_user.id)
    result = await session.execute(query)
    perfil = result.scalars().first()

    # Si no existe perfil, lo creamos automáticamente
    if not perfil:
        perfil = Perfil(usuario_id=current_user.id)
        session.add(perfil)
        await session.commit()
        await session.refresh(perfil)

    # 2. Subir a Supabase
    try:
        url_foto = await upload_to_bucket(archivo)
        if url_foto:
            perfil.foto_url = url_foto
            session.add(perfil)
            await session.commit()
            await session.refresh(perfil)
            return perfil
        else:
            raise HTTPException(status_code=500, detail="Error al obtener URL de la imagen")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir imagen: {str(e)}")