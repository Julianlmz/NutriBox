from db import SessionDep
from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from models import Usuario, UsuarioCreate

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.post("/", response_model=Usuario, status_code=201 )
async def crear_usuario(new_usuario:UsuarioCreate, session:SessionDep):
    usuario = Usuario(**new_usuario.model_dump())
    session.add(usuario)
    try:
        session.commit()
        session.refresh(usuario)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=400,
            detail="La cedula ya esta registrada"
        )
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

@router.get("/", response_model=list[Usuario])
async def obtener_usuarios(session: SessionDep):
    usuarios = session.query(Usuario).all()
    if not usuarios:
        raise HTTPException(status_code=404, detail="No hay usuarios registrados")
    return usuarios

@router.get("/{id_usuario}", response_model=Usuario)
async def obtener_usuario(id_usuario:int, session:SessionDep):
    usuario_db = session.get(Usuario, id_usuario)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return usuario_db

@router.put("/{id_usuario}", response_model=Usuario)
async def actualizar_usuario(id_usuario:int, new_usuario:UsuarioCreate, session:SessionDep):
    usuario_db = session.get(Usuario, id_usuario)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuario not found")
    for key, value in new_usuario.model_dump().items():
        setattr(usuario_db, key, value)
    try:
        session.add(usuario_db)
        session.commit()
        session.refresh(usuario_db)
        return usuario_db
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail="La cédula ya está registrada")
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")


@router.delete("/{id_usuario}")
async def eliminar_usuario(id_usuario:int, session:SessionDep):
    usuario_db = session.get(Usuario, id_usuario)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuario not found")
    session.delete(usuario_db)
    session.commit()
    return { "message": "Usuario eliminado correctamente" }