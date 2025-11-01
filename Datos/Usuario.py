from fastapi import APIRouter, HTTPException, Query
from Aplicacion.database import SessionDep
from Datos.models import (
    Usuario, UsuarioCreate, UsuarioUpdate, UsuarioConRelaciones,
    RolUsuario, Perfil, PerfilCreate, PerfilUpdate
)
from typing import List
from datetime import datetime

router = APIRouter(tags=["Usuarios"], prefix="/usuario")


@router.post("/", response_model=Usuario, status_code=201)
async def crear_usuario(nuevo_usuario: UsuarioCreate, session: SessionDep):
    """
    Crea un nuevo usuario en el sistema.

    Args:
        nuevo_usuario: Datos del usuario (nombre, apellido, edad, rol, cédula)
        session: Sesión de base de datos

    Returns:
        Usuario: Usuario creado con su ID asignado

    Raises:
        HTTPException 409: Si la cédula ya está registrada
        HTTPException 400: Si los datos son inválidos
    """
    # Verificar si la cédula ya existe
    usuarios = session.query(Usuario).filter(Usuario.cedula == nuevo_usuario.cedula).all()
    if usuarios:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe un usuario con la cédula '{nuevo_usuario.cedula}'"
        )

    usuario = Usuario.model_validate(nuevo_usuario)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@router.get("/", response_model=List[Usuario])
async def listar_usuarios(
        rol: RolUsuario = Query(default=None),
        activo: bool = Query(default=None),
        localidad: str = Query(default=""),
        session: SessionDep = None
):
    """
    Lista usuarios con filtros opcionales.

    Args:
        rol: Filtrar por rol (Padre o Hijo)
        activo: Filtrar por estado activo/inactivo
        localidad: Filtrar por localidad (búsqueda parcial)
        session: Sesión de base de datos

    Returns:
        List[Usuario]: Lista de usuarios que cumplen los filtros

    Examples:
        - GET /usuario/ - Todos los usuarios
        - GET /usuario/?rol=Padre - Solo padres
        - GET /usuario/?activo=true - Solo usuarios activos
        - GET /usuario/?localidad=Bogotá - Usuarios de Bogotá
    """
    query = session.query(Usuario)

    if rol:
        query = query.filter(Usuario.rol == rol)
    if activo is not None:
        query = query.filter(Usuario.is_active == activo)
    if localidad:
        query = query.filter(Usuario.localidad.contains(localidad))

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

    # Verificar cédula duplicada solo si cambió
    if usuario.cedula != datos_actualizados.cedula:
        usuarios_existentes = session.query(Usuario).filter(
            Usuario.cedula == datos_actualizados.cedula
        ).all()
        if usuarios_existentes:
            raise HTTPException(
                status_code=409,
                detail=f"La cédula '{datos_actualizados.cedula}' ya está en uso"
            )

    # Actualizar campos
    usuario.nombre = datos_actualizados.nombre
    usuario.apellido = datos_actualizados.apellido
    usuario.localidad = datos_actualizados.localidad
    usuario.edad = datos_actualizados.edad
    usuario.rol = datos_actualizados.rol
    usuario.cedula = datos_actualizados.cedula
    usuario.email = datos_actualizados.email
    usuario.fecha_modificacion = datetime.now()

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

    usuario.fecha_modificacion = datetime.now()

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
    usuario.fecha_modificacion = datetime.now()

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
        perfil_data: Datos del perfil (bio, teléfono, foto)
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
        perfil_data: Datos a actualizar
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