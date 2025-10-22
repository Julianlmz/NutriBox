from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from typing import List, Optional
from Datos.models import Perfil, Usuario
from Aplicacion.db import SessionDep

router = APIRouter(prefix="/perfiles", tags=["Perfiles"])


# ========================================
# RELACIÓN 1:1 - Usuario ↔ Perfil
# Un usuario tiene UN perfil
# Un perfil pertenece a UN usuario
# ========================================


@router.post("/", response_model=Perfil, status_code=status.HTTP_201_CREATED)
async def crear_perfil(perfil: Perfil, session: SessionDep):
    """
    Crea un nuevo perfil para un usuario.
    RELACIÓN 1:1 - Un usuario solo puede tener UN perfil.
    """
    # Verificar que el usuario existe
    usuario = session.get(Usuario, perfil.usuario_id)
    if not usuario or not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado o inactivo"
        )

    # Verificar que el usuario NO tenga ya un perfil (1:1)
    perfil_existente = session.exec(
        select(Perfil).where(Perfil.usuario_id == perfil.usuario_id)
    ).first()

    if perfil_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya tiene un perfil. Use PUT para actualizar."
        )

    session.add(perfil)
    session.commit()
    session.refresh(perfil)
    return perfil


@router.get("/", response_model=List[Perfil])
async def listar_perfiles(session: SessionDep):
    """Lista todos los perfiles"""
    perfiles = session.exec(select(Perfil)).all()
    return perfiles


@router.get("/{perfil_id}", response_model=Perfil)
async def obtener_perfil(perfil_id: int, session: SessionDep):
    """Obtiene un perfil por su ID"""
    perfil = session.get(Perfil, perfil_id)
    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil no encontrado"
        )
    return perfil


@router.get("/usuario/{usuario_id}", response_model=Perfil)
async def obtener_perfil_por_usuario(usuario_id: int, session: SessionDep):
    """
    Obtiene el perfil de un usuario específico.
    RELACIÓN 1:1 - Solo devuelve UN perfil por usuario.
    """
    # Verificar que el usuario existe
    usuario = session.get(Usuario, usuario_id)
    if not usuario or not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    perfil = session.exec(
        select(Perfil).where(Perfil.usuario_id == usuario_id)
    ).first()

    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario no tiene un perfil creado"
        )
    return perfil


@router.put("/{perfil_id}", response_model=Perfil)
async def actualizar_perfil(perfil_id: int, bio: Optional[str] = None,
                            telefono: Optional[str] = None,
                            foto_url: Optional[str] = None,
                            session: SessionDep = None):
    """Actualiza un perfil existente"""
    perfil = session.get(Perfil, perfil_id)
    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil no encontrado"
        )

    # Actualizar solo los campos proporcionados
    if bio is not None:
        perfil.bio = bio
    if telefono is not None:
        perfil.telefono = telefono
    if foto_url is not None:
        perfil.foto_url = foto_url

    session.add(perfil)
    session.commit()
    session.refresh(perfil)
    return perfil


@router.delete("/{perfil_id}", status_code=status.HTTP_200_OK)
async def eliminar_perfil(perfil_id: int, session: SessionDep):
    """
    Elimina un perfil permanentemente.
    Nota: El usuario seguirá existiendo (relación 1:1 opcional).
    """
    perfil = session.get(Perfil, perfil_id)
    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil no encontrado"
        )

    session.delete(perfil)
    session.commit()
    return {"message": "Perfil eliminado exitosamente", "id": perfil_id}


@router.get("/{perfil_id}/completo")
async def obtener_perfil_completo(perfil_id: int, session: SessionDep):
    """
    Obtiene el perfil con toda la información del usuario asociado.
    Demuestra la RELACIÓN 1:1 bidireccional.
    """
    perfil = session.get(Perfil, perfil_id)
    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil no encontrado"
        )

    return {
        "perfil": {
            "id": perfil.id,
            "bio": perfil.bio,
            "telefono": perfil.telefono,
            "foto_url": perfil.foto_url
        },
        "usuario": {
            "id": perfil.usuario.id,
            "nombre": perfil.usuario.nombre,
            "apellido": perfil.usuario.apellido,
            "cedula": perfil.usuario.cedula,
            "edad": perfil.usuario.edad,
            "localidad": perfil.usuario.localidad,
            "rol": perfil.usuario.rol
        }
    }
