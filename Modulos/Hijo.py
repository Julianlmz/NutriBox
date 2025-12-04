from fastapi import APIRouter, HTTPException, status, Form, UploadFile, File, Depends
from typing import List, Optional, Annotated
from sqlmodel import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from Core.database import SessionDep
from Core.seguridad import hashear_password
from Core.supabase_client import upload_to_bucket
from Modulos.models import Usuario, Perfil, Restriccion, RestriccionHijo
from Core.auth import get_current_user

router = APIRouter(tags=["Hijos"], prefix="/hijo")


# --- Modelo de respuesta ---
class HijoResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: Optional[str] = None
    edad: int
    genero: str
    foto_perfil: Optional[str] = None


# --- Helper ---
def procesar_hijo(usuario: Usuario) -> HijoResponse:
    edad = 0
    genero = "Otro"
    foto = "https://cdn-icons-png.flaticon.com/512/3011/3011270.png"

    if usuario.perfil:
        if usuario.perfil.foto_url:
            foto = usuario.perfil.foto_url

        if usuario.perfil.bio:
            partes = usuario.perfil.bio.split("|")
            for p in partes:
                if "Edad:" in p:
                    try:
                        edad = int(p.split(":")[1])
                    except:
                        pass
                if "Genero:" in p:
                    genero = p.split(":")[1]

    return HijoResponse(
        id=usuario.id,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        edad=edad,
        genero=genero,
        foto_perfil=foto
    )


@router.post("/", response_model=HijoResponse, status_code=201)
async def crear_hijo(
        session: SessionDep,
        current_user: Annotated[Usuario, Depends(get_current_user)],  # <--- Exigimos usuario autenticado
        nombre: str = Form(...),
        apellido: str = Form(...),
        edad: int = Form(5),
        genero: str = Form("Otro"),
        email: str = Form(...),
        password: str = Form(...),
        tipo_imagen: str = Form("url"),
        imagen_url: Optional[str] = Form(None),
        imagen_archivo: Optional[UploadFile] = File(None)
):
    # 1. Validar Email
    query = select(Usuario).where(Usuario.email == email)
    result = await session.execute(query)
    if result.scalars().first():
        raise HTTPException(status_code=409, detail="Este email ya existe")

    # 2. Imagen
    foto_final = "https://cdn-icons-png.flaticon.com/512/3011/3011270.png"
    try:
        if tipo_imagen == "archivo" and imagen_archivo:
            url = await upload_to_bucket(imagen_archivo)
            if url: foto_final = url
        elif tipo_imagen == "url" and imagen_url:
            foto_final = imagen_url
    except Exception as e:
        print(f"Error imagen: {e}")

    # 3. Crear Usuario Base (HIJO)
    password_hash = hashear_password(password)
    nuevo_hijo = Usuario(
        nombre=nombre,
        apellido=apellido,
        email=email,
        hashed_password=password_hash,
        padre_id=current_user.id  # <--- VINCULAMOS AL PADRE
    )

    session.add(nuevo_hijo)
    await session.commit()
    await session.refresh(nuevo_hijo)

    # 4. Crear Perfil con datos extra
    bio_data = f"Edad:{edad}|Genero:{genero}"
    nuevo_perfil = Perfil(
        usuario_id=nuevo_hijo.id,
        foto_url=foto_final,
        bio=bio_data
    )
    session.add(nuevo_perfil)
    await session.commit()

    # Cargar perfil para la respuesta
    query_final = select(Usuario).where(Usuario.id == nuevo_hijo.id).options(
        selectinload(Usuario.perfil)
    )
    result_final = await session.execute(query_final)
    hijo_completo = result_final.scalars().first()

    return procesar_hijo(hijo_completo)


@router.get("/", response_model=List[HijoResponse])
async def listar_hijos(
        session: SessionDep,
        current_user: Annotated[Usuario, Depends(get_current_user)]  # <--- Exigimos usuario autenticado
):
    # FILTRAR POR PADRE_ID
    query = select(Usuario).where(
        Usuario.is_active == True,
        Usuario.padre_id == current_user.id  # <--- SOLO HIJOS DE ESTE USUARIO
    ).options(
        selectinload(Usuario.perfil)
    )
    result = await session.execute(query)
    usuarios = result.scalars().all()

    hijos = []
    for u in usuarios:
        # Ya no necesitamos filtrar por email "hijo_" porque tenemos padre_id
        hijos.append(procesar_hijo(u))
    return hijos


@router.put("/{hijo_id}", response_model=HijoResponse)
async def actualizar_hijo(
        hijo_id: int,
        session: SessionDep,
        current_user: Annotated[Usuario, Depends(get_current_user)],  # Seguridad
        nombre: str = Form(...),
        apellido: str = Form(...),
        edad: int = Form(...),
        genero: str = Form("Otro"),
        tipo_imagen: str = Form("url"),
        imagen_url: Optional[str] = Form(None),
        imagen_archivo: Optional[UploadFile] = File(None)
):
    # Buscar hijo asegurando que sea del usuario actual
    query = select(Usuario).where(
        Usuario.id == hijo_id,
        Usuario.padre_id == current_user.id  # Seguridad extra
    ).options(selectinload(Usuario.perfil))

    result = await session.execute(query)
    hijo = result.scalars().first()

    if not hijo:
        raise HTTPException(status_code=404, detail="Hijo no encontrado")

    # Asegurar que el perfil existe
    perfil = hijo.perfil
    if not perfil:
        q_p = select(Perfil).where(Perfil.usuario_id == hijo.id)
        res_p = await session.execute(q_p)
        perfil = res_p.scalars().first()

        if not perfil:
            perfil = Perfil(usuario_id=hijo.id)
            session.add(perfil)

    # Actualizar datos
    hijo.nombre = nombre
    hijo.apellido = apellido

    if tipo_imagen == "archivo" and imagen_archivo:
        try:
            url = await upload_to_bucket(imagen_archivo)
            if url: perfil.foto_url = url
        except:
            pass
    elif tipo_imagen == "url" and imagen_url:
        perfil.foto_url = imagen_url

    perfil.bio = f"Edad:{edad}|Genero:{genero}"

    session.add(hijo)
    session.add(perfil)
    await session.commit()

    # Recargar completo
    query_reload = select(Usuario).where(Usuario.id == hijo.id).options(selectinload(Usuario.perfil))
    res_reload = await session.execute(query_reload)
    hijo_actualizado = res_reload.scalars().first()

    return procesar_hijo(hijo_actualizado)


@router.delete("/{hijo_id}", status_code=204)
async def eliminar_hijo(
        hijo_id: int,
        session: SessionDep,
        current_user: Annotated[Usuario, Depends(get_current_user)]
):
    hijo = await session.get(Usuario, hijo_id)

    # Validar que sea hijo del usuario actual
    if not hijo or hijo.padre_id != current_user.id:
        raise HTTPException(status_code=404, detail="Hijo no encontrado")

    hijo.is_active = False
    session.add(hijo)
    await session.commit()
    return


# ===== ENDPOINTS PARA RESTRICCIONES =====

@router.post("/{hijo_id}/restriccion/{restriccion_id}", status_code=201)
async def asociar_restriccion(
        hijo_id: int,
        restriccion_id: int,
        session: SessionDep,
        current_user: Annotated[Usuario, Depends(get_current_user)]
):
    """Asociar una restricción a un hijo"""
    # Verificar que el hijo existe y es del usuario
    hijo = await session.get(Usuario, hijo_id)
    if not hijo or hijo.padre_id != current_user.id:
        raise HTTPException(status_code=404, detail="Hijo no encontrado")

    # Verificar que la restricción existe
    restriccion = await session.get(Restriccion, restriccion_id)
    if not restriccion:
        raise HTTPException(status_code=404, detail="Restricción no encontrada")

    # Verificar si ya existe la asociación
    query = select(RestriccionHijo).where(
        RestriccionHijo.hijo_id == hijo_id,
        RestriccionHijo.restriccion_id == restriccion_id
    )
    result = await session.execute(query)
    existe = result.scalars().first()

    if existe:
        raise HTTPException(status_code=409, detail="La restricción ya está asociada a este hijo")

    # Crear la asociación
    asociacion = RestriccionHijo(hijo_id=hijo_id, restriccion_id=restriccion_id)
    session.add(asociacion)
    await session.commit()

    return {"message": "Restricción asociada correctamente"}


@router.delete("/{hijo_id}/restriccion/{restriccion_id}", status_code=204)
async def desasociar_restriccion(
        hijo_id: int,
        restriccion_id: int,
        session: SessionDep,
        current_user: Annotated[Usuario, Depends(get_current_user)]
):
    """Desasociar una restricción de un hijo"""
    # Verificar propiedad del hijo (aunque la query fallaría igual si no existe, es mejor validar)
    hijo = await session.get(Usuario, hijo_id)
    if not hijo or hijo.padre_id != current_user.id:
        raise HTTPException(status_code=404, detail="Hijo no encontrado")

    query = select(RestriccionHijo).where(
        RestriccionHijo.hijo_id == hijo_id,
        RestriccionHijo.restriccion_id == restriccion_id
    )
    result = await session.execute(query)
    asociacion = result.scalars().first()

    if not asociacion:
        raise HTTPException(status_code=404, detail="Restricción no asociada a este hijo")

    await session.delete(asociacion)
    await session.commit()
    return


@router.get("/{hijo_id}/restricciones", response_model=List[dict])
async def listar_restricciones_hijo(
        hijo_id: int,
        session: SessionDep,
        current_user: Annotated[Usuario, Depends(get_current_user)]
):
    """Listar todas las restricciones de un hijo"""
    # Verificar propiedad
    hijo = await session.get(Usuario, hijo_id)
    if not hijo or hijo.padre_id != current_user.id:
        raise HTTPException(status_code=404, detail="Hijo no encontrado")

    # Obtener restricciones
    query = (
        select(Restriccion)
        .join(RestriccionHijo, Restriccion.id == RestriccionHijo.restriccion_id)
        .where(RestriccionHijo.hijo_id == hijo_id)
    )
    result = await session.execute(query)
    restricciones = result.scalars().all()

    return [
        {
            "id": r.id,
            "nombre": r.nombre,
            "descripcion": r.descripcion,
            "nivel_severidad": r.nivel_severidad
        }
        for r in restricciones
    ]