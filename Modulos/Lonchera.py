# --- COPIA Y PEGA TODO ESTE CÓDIGO EN Modulos/lonchera.py ---

from fastapi import APIRouter, HTTPException, Query, Depends
from Core.database import SessionDep
from Modulos.models import (
    Lonchera, LoncheraCreate, LoncheraUpdate, LoncheraAlimento,
    AgregarAlimento, Usuario, Alimento, RestriccionAlimento
)
# --- ¡Importaciones añadidas! ---
from typing import List, Annotated
from Core.auth import get_current_user

# ------------------------------

router = APIRouter(tags=["Loncheras"], prefix="/lonchera")


@router.post("/", response_model=Lonchera, status_code=201)
async def crear_lonchera(data: LoncheraCreate, session: SessionDep):
    """
    Crea una nueva lonchera para un usuario.
    """
    usuario = session.get(Usuario, data.usuario_id)
    if not usuario or not usuario.is_active:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado o inactivo"
        )

    lonchera = Lonchera(**data.model_dump())
    session.add(lonchera)
    session.commit()
    session.refresh(lonchera)
    return lonchera


# =============================================================
# --- ¡FUNCIÓN 100% CORREGIDA Y SEGURA! ---
# =============================================================
@router.get("/", response_model=List[Lonchera])
async def listar_loncheras_del_usuario_actual(
        session: SessionDep,  # <-- ¡ARREGLADO! (quitamos el = None)
        current_user: Annotated[Usuario, Depends(get_current_user)],  # <-- ¡MÁS SEGURO!
        incluir_inactivas: bool = Query(default=False)
):
    """
    Lista las loncheras del usuario actualmente autenticado.
    Filtra automáticamente las loncheras borradas (is_active=False).
    """
    # Filtra por el ID del usuario que viene en el token
    query = session.query(Lonchera).filter(Lonchera.usuario_id == current_user.id)

    # --- ¡ESTA ES LA LÍNEA QUE ARREGLA TU BUG! ---
    if not incluir_inactivas:
        query = query.filter(Lonchera.is_active == True)  # Solo muestra las activas
    # --------------------------------------------------

    loncheras = query.all()
    return loncheras


# =============================================================


@router.get("/{lonchera_id}", response_model=Lonchera)
async def obtener_lonchera(lonchera_id: int, session: SessionDep):
    """
    Obtiene una lonchera por ID, solo si está activa.
    """
    lonchera = session.get(Lonchera, lonchera_id)
    # Solo la encuentra si existe Y está activa
    if not lonchera or not lonchera.is_active:
        raise HTTPException(status_code=404, detail="Lonchera no encontrada")
    return lonchera


@router.patch("/{lonchera_id}", response_model=Lonchera)
async def actualizar_lonchera(
        lonchera_id: int,
        data: LoncheraUpdate,
        session: SessionDep
):
    """
    Actualiza parcialmente una lonchera.
    """
    # Usamos la función 'obtener_lonchera' para asegurar que existe y está activa
    lonchera = await obtener_lonchera(lonchera_id, session)

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No se proporcionaron datos para actualizar"
        )

    for key, value in update_data.items():
        setattr(lonchera, key, value)

    session.add(lonchera)
    session.commit()
    session.refresh(lonchera)
    return lonchera


# =============================================================
# --- ¡FUNCIÓN 100% CORREGIDA! ---
# =============================================================
@router.delete("/{lonchera_id}", status_code=204)
async def eliminar_lonchera(
        lonchera_id: int,
        session: SessionDep,  # <-- ¡ARREGLADO! (quitamos el = None)
        hard_delete: bool = Query(default=False)
):
    """
    Elimina (hard) o desactiva (soft) una lonchera.
    """
    lonchera = session.get(Lonchera, lonchera_id)
    if not lonchera:
        raise HTTPException(status_code=404, detail="Lonchera no encontrada")

    if hard_delete:
        session.delete(lonchera)
    else:
        # ¡Esta lógica está perfecta!
        lonchera.is_active = False
        session.add(lonchera)

    session.commit()
    return  # Devuelve 204 No Content


# =============================================================


@router.post("/{lonchera_id}/alimento", status_code=201)
async def agregar_alimento(
        lonchera_id: int,
        data: AgregarAlimento,
        session: SessionDep
):
    """
    Agrega un alimento a la lonchera con cantidad específica.
    """
    # Usamos la función 'obtener_lonchera' para asegurar que existe y está activa
    lonchera = await obtener_lonchera(lonchera_id, session)

    alimento = session.get(Alimento, data.alimento_id)
    if not alimento or not alimento.is_active:
        raise HTTPException(status_code=404, detail="Alimento no encontrado o inactivo")

    if data.cantidad_gramos <= 0:
        raise HTTPException(
            status_code=400,
            detail="La cantidad debe ser mayor a 0"
        )

    existing = session.query(LoncheraAlimento).filter(
        LoncheraAlimento.lonchera_id == lonchera_id,
        LoncheraAlimento.alimento_id == data.alimento_id
    ).first()

    if existing:
        existing.cantidad_gramos = data.cantidad_gramos
        mensaje = "Cantidad del alimento actualizada"
        session.add(existing)
    else:
        la = LoncheraAlimento(
            lonchera_id=lonchera_id,
            alimento_id=data.alimento_id,
            cantidad_gramos=data.cantidad_gramos
        )
        session.add(la)
        mensaje = "Alimento agregado a la lonchera"

    session.commit()  # Commit para guardar la relación LoncheraAlimento

    _recalcular_totales_lonchera(lonchera, session)  # Ahora recalcular

    factor = data.cantidad_gramos / 100
    calorias_alimento = factor * alimento.calorias_por_100g
    precio_alimento = factor * alimento.precio_unitario

    return {
        "message": mensaje,
        "lonchera_id": lonchera_id,
        "alimento": {
            "id": alimento.id,
            "nombre": alimento.nombre,
            "cantidad_gramos": data.cantidad_gramos,
            "calorias_aportadas": round(calorias_alimento, 2),
            "precio_aportado": round(precio_alimento, 2)
        },
        "totales_lonchera": {
            "calorias": lonchera.calorias,
            "precio": lonchera.precio
        }
    }


@router.delete("/{lonchera_id}/alimento/{alimento_id}", status_code=204)
async def quitar_alimento(
        lonchera_id: int,
        alimento_id: int,
        session: SessionDep
):
    """
    Quita un alimento de la lonchera.
    """
    lonchera = await obtener_lonchera(lonchera_id, session)

    la = session.query(LoncheraAlimento).filter(
        LoncheraAlimento.lonchera_id == lonchera_id,
        LoncheraAlimento.alimento_id == alimento_id
    ).first()

    if not la:
        raise HTTPException(
            status_code=404,
            detail="El alimento no está en la lonchera"
        )

    session.delete(la)
    session.commit()

    _recalcular_totales_lonchera(lonchera, session)
    return


@router.get("/{lonchera_id}/alimentos")
async def listar_alimentos_lonchera(lonchera_id: int, session: SessionDep):
    """
    Lista todos los alimentos de una lonchera con información nutricional detallada.
    """
    lonchera = await obtener_lonchera(lonchera_id, session)

    alimentos_info = []
    total_calorias = 0
    total_proteinas = 0
    total_carbohidratos = 0
    total_grasas = 0
    total_precio = 0

    for la in lonchera.alimentos:
        factor = la.cantidad_gramos / 100
        calorias = factor * la.alimento.calorias_por_100g
        proteinas = factor * la.alimento.proteinas_por_100g
        carbohidratos = factor * la.alimento.carbohidratos_por_100g
        grasas = factor * la.alimento.grasas_por_100g
        precio = factor * la.alimento.precio_unitario

        alimentos_info.append({
            "alimento_id": la.alimento_id,
            "nombre": la.alimento.nombre,
            "categoria": la.alimento.categoria,
            "cantidad_gramos": la.cantidad_gramos,
            "calorias": round(calorias, 2),
            "proteinas": round(proteinas, 2),
            "carbohidratos": round(carbohidratos, 2),
            "grasas": round(grasas, 2),
            "precio": round(precio, 2)
        })

        total_calorias += calorias
        total_proteinas += proteinas
        total_carbohidratos += carbohidratos
        total_grasas += grasas
        total_precio += precio

    return {
        "lonchera_id": lonchera_id,
        "nombre": lonchera.nombre,
        "descripcion": lonchera.descripcion,
        "alimentos": alimentos_info,
        "totales": {
            "calorias": round(total_calorias, 2),
            "proteinas": round(total_proteinas, 2),
            "carbohidratos": round(total_carbohidratos, 2),
            "grasas": round(total_grasas, 2),
            "precio": round(total_precio, 2)
        },
        "total_alimentos": len(alimentos_info)
    }


# =============================================================
# --- ¡FUNCIÓN CORREGIDA! (Campos borrados eliminados) ---
# =============================================================
@router.get("/{lonchera_id}/completo")
async def obtener_lonchera_completa(lonchera_id: int, session: SessionDep):
    """
    Obtiene información completa de la lonchera con usuario y alimentos.
    """
    lonchera = await obtener_lonchera(lonchera_id, session)

    usuario_info = {
        "id": lonchera.usuario.id,
        "nombre": lonchera.usuario.nombre,
        "apellido": lonchera.usuario.apellido
    }

    alimentos_info = []
    for la in lonchera.alimentos:
        alimentos_info.append({
            "id": la.alimento.id,
            "nombre": la.alimento.nombre,
            "cantidad_gramos": la.cantidad_gramos,
            "categoria": la.alimento.categoria
        })

    return {
        "lonchera": {
            "id": lonchera.id,
            "nombre": lonchera.nombre,
            "descripcion": lonchera.descripcion,
            "precio": lonchera.precio,
            "calorias": lonchera.calorias,
            "is_active": lonchera.is_active
        },
        "usuario": usuario_info,
        "alimentos": alimentos_info,
        "total_alimentos": len(alimentos_info)
    }


# =============================================================


# =============================================================
# --- ¡FUNCIÓN CORREGIDA! (Bug de session=None arreglado) ---
# =============================================================
@router.get("/{lonchera_id}/validar-restricciones")
async def validar_restricciones_lonchera(
        lonchera_id: int,
        session: SessionDep,  # <-- ¡ARREGLADO!
        restriccion_ids: List[int] = Query(default=[])
):
    """
    Valida si la lonchera contiene alimentos con restricciones específicas.
    """
    lonchera = await obtener_lonchera(lonchera_id, session)

    if not restriccion_ids:
        return {
            "lonchera_id": lonchera_id,
            "mensaje": "No se especificaron restricciones para validar",
            "es_segura": True,
            "alimentos_problematicos": []
        }

    alimentos_restringidos = {}
    for restriccion_id in restriccion_ids:
        asociaciones = session.query(RestriccionAlimento).filter(
            RestriccionAlimento.restriccion_id == restriccion_id
        ).all()
        for asoc in asociaciones:
            alimentos_restringidos[asoc.alimento_id] = restriccion_id

    alimentos_problematicos = []
    for la in lonchera.alimentos:
        if la.alimento_id in alimentos_restringidos:
            alimentos_problematicos.append({
                "alimento_id": la.alimento.id,
                "nombre": la.alimento.nombre,
                "cantidad_gramos": la.cantidad_gramos,
                "restriccion_id": alimentos_restringidos[la.alimento_id]
            })

    es_segura = len(alimentos_problematicos) == 0

    return {
        "lonchera_id": lonchera_id,
        "nombre_lonchera": lonchera.nombre,
        "es_segura": es_segura,
        "total_alimentos": len(lonchera.alimentos),
        "alimentos_problematicos": alimentos_problematicos,
        "mensaje": "Lonchera segura" if es_segura else "⚠️ Contiene alimentos con restricciones"
    }


# =============================================================


# =============================================================
# --- ¡FUNCIÓN CORREGIDA! (Más robusta) ---
# =============================================================
def _recalcular_totales_lonchera(lonchera: Lonchera, session: SessionDep):
    """
    Función auxiliar para recalcular calorías y precio total de una lonchera.
    """
    total_calorias = 0
    total_precio = 0

    # Forzar la carga de la relación 'alimentos' si no está cargada
    session.refresh(lonchera, ["alimentos"])

    for la in lonchera.alimentos:
        # Asegurarse de que el 'alimento' dentro de la relación esté cargado
        if la.alimento is None:
            session.refresh(la, ["alimento"])

        factor = la.cantidad_gramos / 100
        total_calorias += factor * la.alimento.calorias_por_100g
        total_precio += factor * la.alimento.precio_unitario

    lonchera.calorias = int(round(total_calorias))
    lonchera.precio = round(total_precio, 2)

    session.add(lonchera)  # Añadir al contexto de la sesión
    session.commit()  # Guardar los cambios en la BD
    session.refresh(lonchera)  # Refrescar la instancia
# =============================================================