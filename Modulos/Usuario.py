from fastapi import APIRouter, HTTPException, Query, Depends
from Core.database import SessionDep
from Modulos.models import (Usuario, UsuarioCreate, UsuarioUpdate, UsuarioConRelaciones, Perfil, PerfilCreate, PerfilUpdate)
from typing import List, Annotated
from Core.seguridad import hashear_password
from Core.auth import get_current_user

router = APIRouter(tags=["Usuarios"], prefix="/usuario")


@router.get("/me", response_model=Usuario)
async def read_users_me(current_user: Annotated[Usuario, Depends(get_current_user)]):
    """
    Obtiene los datos del usuario que está actualmente autenticado.

    Requiere un Token de Acceso (Bearer Token).
    """
    return current_user

@router.post("/", response_model=Usuario, status_code=201)
async def crear_usuario(nuevo_usuario: UsuarioCreate, session: SessionDep):
    """
        Crea un nuevo usuario en el sistema.

        Args:
            nuevo_usuario: Servicios del usuario (nombre, apellido, email, password) <-- LIMPIO
            session: Sesión de base de datos

        Returns:
            Usuario: Usuario creado con su ID asignado

        Raises:
            HTTPException 409: Si el email ya está registrado
        """

    usuario_existente = session.query(Usuario).filter(Usuario.email == nuevo_usuario.email).first()
    if usuario_existente:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe un usuario con el email '{nuevo_usuario.email}'"
        )

    password_hasheado = hashear_password(nuevo_usuario.password)
    datos_db = nuevo_usuario.model_dump(exclude={"password", "rol"})

    usuario = Usuario(
        **datos_db,
        hashed_password=password_hasheado
    )

    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@router.get("/", response_model=List[Usuario])
async def listar_usuarios(
        activo: bool = Query(default=None),
        session: SessionDep = None
):
    """
        Lista usuarios con filtros opcionales.

        Args:
            activo: Filtrar por estado activo/inactivo
            session: Sesión de base de datos

        Returns:
            List[Usuario]: Lista de usuarios que cumplen los filtros

        Examples:
            - GET /usuario/ - Todos los usuarios
            - GET /usuario/?activo=true - Solo usuarios activos

        """
    query = session.query(Usuario)

    if activo is not None:
        query = query.filter(Usuario.is_active == activo)

    usuarios = query.all()
    return usuarios


@router.get("/{usuario_id}", response_model=UsuarioConRelaciones)
async def obtener_usuario(usuario_id: int, session: SessionDep):
    """
    Obtiene un usuario por ID con sus relaciones (loncheras, perfil).

    Args:
        usuario_id: ID del usuario
        session: Sesión de base de datos

    Returns:
        UsuarioConRelaciones: Usuario con loncheras y perfil

    Raises:
        HTTPException 404: Si el usuario no existe
    """
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.put("/{usuario_id}", response_model=Usuario)
async def actualizar_usuario(
        usuario_id: int,
        datos_actualizados: UsuarioCreate,
        session: SessionDep
):
    """
    Actualiza todos los datos de un usuario (PUT completo).

    Args:
        usuario_id: ID del usuario a actualizar
        datos_actualizados: Nuevos datos del usuario
        session: Sesión de base de datos

    Returns:
        Usuario: Usuario actualizado

    Raises:
        HTTPException 404: Si el usuario no existe
        HTTPException 409: Si la nueva cédula ya está en uso
    """
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Actualizar campos
    usuario.nombre = datos_actualizados.nombre
    usuario.apellido = datos_actualizados.apellido
    usuario.email = datos_actualizados.email

    session.commit()
    session.refresh(usuario)
    return usuario


@router.patch("/{usuario_id}", response_model=Usuario)
async def actualizar_parcial_usuario(
        usuario_id: int,
        datos_actualizados: UsuarioUpdate,
        session: SessionDep
):
    """
    Actualiza parcialmente un usuario (PATCH).

    Args:
        usuario_id: ID del usuario
        datos_actualizados: Campos a actualizar (solo los proporcionados)
        session: Sesión de base de datos

    Returns:
        Usuario: Usuario actualizado

    Raises:
        HTTPException 404: Si el usuario no existe
        HTTPException 400: Si no se proporcionan datos para actualizar
    """
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    update_data = datos_actualizados.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No se proporcionaron datos para actualizar"
        )

    # Actualizar solo los campos proporcionados
    for key, value in update_data.items():
        setattr(usuario, key, value)

    session.commit()
    session.refresh(usuario)
    return usuario


@router.delete("/{usuario_id}", status_code=204)
async def eliminar_usuario(usuario_id: int, session: SessionDep):
    """
    Elimina (desactiva) un usuario del sistema.

    Nota: No elimina físicamente, solo marca como inactivo para preservar
    historial de loncheras y pedidos.

    Args:
        usuario_id: ID del usuario
        session: Sesión de base de datos

    Returns:
        None: Respuesta vacía con código 204

    Raises:
        HTTPException 404: Si el usuario no existe
    """
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Soft delete: solo marcar como inactivo
    usuario.is_active = False

    session.commit()
    return


@router.post("/{usuario_id}/perfil", response_model=Perfil, status_code=201)
async def crear_perfil(
        usuario_id: int,
        perfil_data: PerfilCreate,
        session: SessionDep
):
    """
    Crea un perfil para un usuario.

    Args:
        usuario_id: ID del usuario
        perfil_data: Servicios del perfil (bio, teléfono, foto)
        session: Sesión de base de datos

    Returns:
        Perfil: Perfil creado

    Raises:
        HTTPException 404: Si el usuario no existe
        HTTPException 409: Si el usuario ya tiene un perfil
    """
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Verificar si ya tiene perfil
    if usuario.perfil:
        raise HTTPException(
            status_code=409,
            detail="El usuario ya tiene un perfil creado"
        )

    perfil = Perfil(usuario_id=usuario_id, **perfil_data.model_dump())
    session.add(perfil)
    session.commit()
    session.refresh(perfil)
    return perfil


@router.patch("/{usuario_id}/perfil", response_model=Perfil)
async def actualizar_perfil(
        usuario_id: int,
        perfil_data: PerfilUpdate,
        session: SessionDep
):
    """
    Actualiza el perfil de un usuario.

    Args:
        usuario_id: ID del usuario
        perfil_data: Servicios a actualizar
        session: Sesión de base de datos

    Returns:
        Perfil: Perfil actualizado

    Raises:
        HTTPException 404: Si el usuario no existe o no tiene perfil
    """
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not usuario.perfil:
        raise HTTPException(
            status_code=404,
            detail="El usuario no tiene un perfil creado"
        )

    update_data = perfil_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(usuario.perfil, key, value)

    session.commit()
    session.refresh(usuario.perfil)
    return usuario.perfil


@router.get("/{usuario_id}/loncheras")
async def obtener_loncheras_usuario(usuario_id: int, session: SessionDep):
    """
    Obtiene todas las loncheras creadas por un usuario.

    Args:
        usuario_id: ID del usuario
        session: Sesión de base de datos

    Returns:
        dict: Usuario con lista de loncheras

    Raises:
        HTTPException 404: Si el usuario no existe
    """
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    loncheras = [
        {
            "id": l.id,
            "nombre": l.nombre,
            "calorias": l.calorias,
            "precio": l.precio,
            "fecha_creacion": l.fecha_creacion,
            "is_active": l.is_active
        }
        for l in usuario.loncheras
    ]

    return {
        "usuario_id": usuario.id,
        "nombre_completo": f"{usuario.nombre} {usuario.apellido}",
        "total_loncheras": len(loncheras),
        "loncheras": loncheras
    }


@router.get("/{usuario_id}/pedidos")
async def obtener_pedidos_usuario(usuario_id: int, session: SessionDep):
    """
    Obtiene todos los pedidos realizados por un usuario.

    Args:
        usuario_id: ID del usuario
        session: Sesión de base de datos

    Returns:
        dict: Usuario con lista de pedidos

    Raises:
        HTTPException 404: Si el usuario no existe
    """
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    pedidos = [
        {
            "id": p.id,
            "fecha": p.fecha,
            "total": p.total,
            "estado": p.estado
        }
        for p in usuario.pedidos
    ]

    return {
        "usuario_id": usuario.id,
        "nombre_completo": f"{usuario.nombre} {usuario.apellido}",
        "total_pedidos": len(pedidos),
        "pedidos": pedidos
    }