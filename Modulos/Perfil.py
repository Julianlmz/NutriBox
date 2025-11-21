from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from typing import List, Optional
from Modulos.models import Perfil, Usuario
from Core.database import SessionDep

router = APIRouter(prefix="/perfiles", tags=["Perfiles"])

@router.get("/usuario/{usuario_id}", response_model=Perfil)
async def obtener_perfil_por_usuario(usuario_id: int, session: SessionDep):
    # Validación asíncrona de usuario
    usuario = await session.get(Usuario, usuario_id) # AWAIT
    if not usuario or not usuario.is_active:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    query = select(Perfil).where(Perfil.usuario_id == usuario_id)
    result = await session.execute(query) # AWAIT
    perfil = result.scalars().first()

    if not perfil:
        # En lugar de 404, devolvemos 204 o un objeto vacío para que el frontend no explote
        # O mejor, dejamos el 404 y que el frontend maneje "Crear Perfil"
        raise HTTPException(status_code=404, detail="El usuario no tiene un perfil creado")
    return perfil

# (Asegúrate de aplicar 'await' en los demás métodos de este archivo también)