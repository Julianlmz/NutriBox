from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from Core.database import get_session
from Modulos.models import (
    Lonchera,
    LoncheraCreate,
    LoncheraUpdate,
    LoncheraConRelaciones,
    Usuario,
    UsuarioResumen,
    Alimento,
    LoncheraAlimento,
    AgregarAlimento,
    LoncheraAlimentoDetalle,
    Direccion
)

router = APIRouter()


# ====================================================================
# CREAR LONCHERA
# ====================================================================
@router.post("/loncheras", response_model=Lonchera, tags=["Loncheras"])
def crear_lonchera(lonchera: LoncheraCreate, session: Session = Depends(get_session)):
    """
    Crea una nueva lonchera para un usuario.
    """
    # Verificar que el usuario existe
    usuario_db = session.get(Usuario, lonchera.usuario_id)
    if not usuario_db:
        raise HTTPException(status_code=404, detail=f"Usuario con ID {lonchera.usuario_id} no encontrado")

    # Verificar que la dirección existe y pertenece al usuario
    if lonchera.direccion_id:
        direccion_db = session.get(Direccion, lonchera.direccion_id)
        if not direccion_db:
            raise HTTPException(status_code=404, detail=f"Dirección con ID {lonchera.direccion_id} no encontrada")
        if direccion_db.usuario_id != lonchera.usuario_id:
            raise HTTPException(
                status_code=400,
                detail="La dirección seleccionada no pertenece al usuario"
            )

    # Crear la lonchera
    nueva_lonchera = Lonchera(**lonchera.model_dump())
    session.add(nueva_lonchera)
    session.commit()
    session.refresh(nueva_lonchera)

    return nueva_lonchera


# ====================================================================
# LISTAR LONCHERAS
# ====================================================================
@router.get("/loncheras", response_model=List[Lonchera], tags=["Loncheras"])
def listar_loncheras(
        skip: int = 0,
        limit: int = 100,
        session: Session = Depends(get_session)
):
    """
    Lista todas las loncheras activas con paginación.
    """
    statement = select(Lonchera).where(Lonchera.is_active == True).offset(skip).limit(limit)
    loncheras = session.exec(statement).all()
    return loncheras


# ====================================================================
# OBTENER LONCHERA POR ID
# ====================================================================
@router.get("/loncheras/{lonchera_id}", response_model=LoncheraConRelaciones, tags=["Loncheras"])
def obtener_lonchera(lonchera_id: int, session: Session = Depends(get_session)):
    """
    Obtiene una lonchera específica con sus relaciones (usuario y alimentos).
    """
    lonchera = session.get(Lonchera, lonchera_id)

    if not lonchera or not lonchera.is_active:
        raise HTTPException(status_code=404, detail=f"Lonchera con ID {lonchera_id} no encontrada")

    # Obtener usuario
    usuario = session.get(Usuario, lonchera.usuario_id)
    usuario_resumen = UsuarioResumen(
        id=usuario.id,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        is_active=usuario.is_active
    )

    # Obtener alimentos de la lonchera
    alimentos_detalle = []
    for la in lonchera.alimentos:
        alimento = session.get(Alimento, la.alimento_id)
        if alimento:
            calorias_porcion = (alimento.calorias_por_100g * la.cantidad_gramos) / 100
            precio_porcion = (alimento.precio_unitario * la.cantidad_gramos) / 100

            alimentos_detalle.append(
                LoncheraAlimentoDetalle(
                    alimento_id=alimento.id,
                    nombre_alimento=alimento.nombre,
                    cantidad_gramos=la.cantidad_gramos,
                    calorias_porcion=round(calorias_porcion, 2),
                    precio_porcion=round(precio_porcion, 2)
                )
            )

    return LoncheraConRelaciones(
        id=lonchera.id,
        nombre=lonchera.nombre,
        descripcion=lonchera.descripcion,
        calorias=lonchera.calorias,
        precio=lonchera.precio,
        direccion_id=lonchera.direccion_id,
        usuario_id=lonchera.usuario_id,
        fecha_creacion=lonchera.fecha_creacion,
        usuario=usuario_resumen,
        alimentos=alimentos_detalle
    )


# ====================================================================
# ACTUALIZAR LONCHERA
# ====================================================================
@router.patch("/loncheras/{lonchera_id}", response_model=Lonchera, tags=["Loncheras"])
def actualizar_lonchera(
        lonchera_id: int,
        lonchera_data: LoncheraUpdate,
        session: Session = Depends(get_session)
):
    """
    Actualiza los datos básicos de una lonchera.
    """
    lonchera_db = session.get(Lonchera, lonchera_id)

    if not lonchera_db or not lonchera_db.is_active:
        raise HTTPException(status_code=404, detail=f"Lonchera con ID {lonchera_id} no encontrada")

    # Actualizar campos proporcionados
    datos_actualizacion = lonchera_data.model_dump(exclude_unset=True)
    for key, value in datos_actualizacion.items():
        setattr(lonchera_db, key, value)

    session.add(lonchera_db)
    session.commit()
    session.refresh(lonchera_db)

    return lonchera_db


# ====================================================================
# ELIMINAR LONCHERA (SOFT DELETE)
# ====================================================================
@router.delete("/loncheras/{lonchera_id}", tags=["Loncheras"])
def eliminar_lonchera(lonchera_id: int, session: Session = Depends(get_session)):
    """
    Elimina (desactiva) una lonchera.
    """
    lonchera_db = session.get(Lonchera, lonchera_id)

    if not lonchera_db or not lonchera_db.is_active:
        raise HTTPException(status_code=404, detail=f"Lonchera con ID {lonchera_id} no encontrada")

    lonchera_db.is_active = False
    session.add(lonchera_db)
    session.commit()

    return {"mensaje": f"Lonchera con ID {lonchera_id} eliminada exitosamente"}


# ====================================================================
# AGREGAR ALIMENTO A LONCHERA
# ====================================================================
@router.post("/loncheras/{lonchera_id}/alimentos", response_model=Lonchera, tags=["Loncheras"])
def agregar_alimento_a_lonchera(
        lonchera_id: int,
        alimento_data: AgregarAlimento,
        session: Session = Depends(get_session)
):
    """
    Agrega un alimento a una lonchera y recalcula calorías y precio.
    """
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera or not lonchera.is_active:
        raise HTTPException(status_code=404, detail=f"Lonchera con ID {lonchera_id} no encontrada")

    alimento = session.get(Alimento, alimento_data.alimento_id)
    if not alimento or not alimento.is_active:
        raise HTTPException(status_code=404, detail=f"Alimento con ID {alimento_data.alimento_id} no encontrado")

    # Verificar si el alimento ya está en la lonchera
    statement = select(LoncheraAlimento).where(
        LoncheraAlimento.lonchera_id == lonchera_id,
        LoncheraAlimento.alimento_id == alimento_data.alimento_id
    )
    relacion_existente = session.exec(statement).first()

    if relacion_existente:
        # Actualizar cantidad
        relacion_existente.cantidad_gramos += alimento_data.cantidad_gramos
        session.add(relacion_existente)
    else:
        # Crear nueva relación
        nueva_relacion = LoncheraAlimento(
            lonchera_id=lonchera_id,
            alimento_id=alimento_data.alimento_id,
            cantidad_gramos=alimento_data.cantidad_gramos
        )
        session.add(nueva_relacion)

    # Recalcular calorías y precio
    calorias_aporte = (alimento.calorias_por_100g * alimento_data.cantidad_gramos) / 100
    precio_aporte = (alimento.precio_unitario * alimento_data.cantidad_gramos) / 100

    lonchera.calorias = int(lonchera.calorias + calorias_aporte)
    lonchera.precio = round(lonchera.precio + precio_aporte, 2)

    session.add(lonchera)
    session.commit()
    session.refresh(lonchera)

    return lonchera


# ====================================================================
# ELIMINAR ALIMENTO DE LONCHERA
# ====================================================================
@router.delete("/loncheras/{lonchera_id}/alimentos/{alimento_id}", response_model=Lonchera, tags=["Loncheras"])
def eliminar_alimento_de_lonchera(
        lonchera_id: int,
        alimento_id: int,
        session: Session = Depends(get_session)
):
    """
    Elimina un alimento de una lonchera y recalcula calorías y precio.
    """
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera or not lonchera.is_active:
        raise HTTPException(status_code=404, detail=f"Lonchera con ID {lonchera_id} no encontrada")

    alimento = session.get(Alimento, alimento_id)
    if not alimento:
        raise HTTPException(status_code=404, detail=f"Alimento con ID {alimento_id} no encontrado")

    # Buscar la relación
    statement = select(LoncheraAlimento).where(
        LoncheraAlimento.lonchera_id == lonchera_id,
        LoncheraAlimento.alimento_id == alimento_id
    )
    relacion = session.exec(statement).first()

    if not relacion:
        raise HTTPException(
            status_code=404,
            detail=f"Alimento con ID {alimento_id} no está en la lonchera {lonchera_id}"
        )

    # Recalcular calorías y precio (restar)
    calorias_restar = (alimento.calorias_por_100g * relacion.cantidad_gramos) / 100
    precio_restar = (alimento.precio_unitario * relacion.cantidad_gramos) / 100

    lonchera.calorias = max(0, int(lonchera.calorias - calorias_restar))
    lonchera.precio = max(0.0, round(lonchera.precio - precio_restar, 2))

    # Eliminar la relación
    session.delete(relacion)
    session.add(lonchera)
    session.commit()
    session.refresh(lonchera)

    return lonchera


# ====================================================================
# LISTAR LONCHERAS POR USUARIO
# ====================================================================
@router.get("/usuarios/{usuario_id}/loncheras", response_model=List[Lonchera], tags=["Loncheras"])
def listar_loncheras_usuario(
        usuario_id: int,
        session: Session = Depends(get_session)
):
    """
    Lista todas las loncheras activas de un usuario específico.
    """
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail=f"Usuario con ID {usuario_id} no encontrado")

    statement = select(Lonchera).where(
        Lonchera.usuario_id == usuario_id,
        Lonchera.is_active == True
    )
    loncheras = session.exec(statement).all()

    return loncheras