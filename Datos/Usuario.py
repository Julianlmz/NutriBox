from Aplicacion.db import SessionDep
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import select
from Datos.models import Usuario, UsuarioCreate, UsuarioUpdate, HistorialEliminacion
from datetime import datetime
import json

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.post("/", response_model=Usuario, status_code=status.HTTP_201_CREATED)
async def crear_usuario(new_usuario: UsuarioCreate, session: SessionDep):
    usuario = Usuario(**new_usuario.model_dump())
    session.add(usuario)
    try:
        session.commit()
        session.refresh(usuario)
        return usuario
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cédula ya está registrada"
        )
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.get("/", response_model=list[Usuario])
async def obtener_usuarios(
        session: SessionDep,
        incluir_inactivos: bool = False
):
    query = select(Usuario)
    if not incluir_inactivos:
        query = query.where(Usuario.is_active == True)

    usuarios = session.exec(query).all()
    if not usuarios:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay usuarios registrados"
        )
    return usuarios


@router.get("/{id_usuario}", response_model=Usuario)
async def obtener_usuario(id_usuario: int, session: SessionDep):
    usuario_db = session.get(Usuario, id_usuario)
    if not usuario_db or not usuario_db.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return usuario_db


@router.put("/{id_usuario}", response_model=Usuario)
async def actualizar_usuario(
        id_usuario: int,
        new_usuario: UsuarioUpdate,
        session: SessionDep
):
    usuario_db = session.get(Usuario, id_usuario)
    if not usuario_db or not usuario_db.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    for key, value in new_usuario.model_dump(exclude_unset=True).items():
        setattr(usuario_db, key, value)

    usuario_db.fecha_modificacion = datetime.now()

    try:
        session.add(usuario_db)
        session.commit()
        session.refresh(usuario_db)
        return usuario_db
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cédula ya está registrada"
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.delete("/{id_usuario}", status_code=status.HTTP_200_OK)
async def eliminar_usuario(
        id_usuario: int,
        session: SessionDep,
        motivo: str = None,
        hard_delete: bool = False
):
    usuario_db = session.get(Usuario, id_usuario)
    if not usuario_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    if hard_delete:
        historial = HistorialEliminacion(
            tabla_nombre="usuario",
            registro_id=usuario_db.id,
            datos_json=json.dumps(usuario_db.model_dump(), default=str),
            motivo=motivo or "Eliminación permanente",
            usuario_eliminador_id=None
        )
        session.add(historial)
        session.delete(usuario_db)
        mensaje = "Usuario eliminado permanentemente"
    else:
        # Soft delete
        usuario_db.is_active = False
        usuario_db.fecha_modificacion = datetime.now()
        session.add(usuario_db)
        mensaje = "Usuario desactivado correctamente"

    try:
        session.commit()
        return {"message": mensaje, "id": id_usuario}
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar: {str(e)}"
        )


@router.post("/{id_usuario}/reactivar", response_model=Usuario)
async def reactivar_usuario(id_usuario: int, session: SessionDep):
    usuario_db = session.get(Usuario, id_usuario)
    if not usuario_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    usuario_db.is_active = True
    usuario_db.fecha_modificacion = datetime.now()
    session.add(usuario_db)
    session.commit()
    session.refresh(usuario_db)
    return usuario_db
