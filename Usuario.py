from db import SessionDep
from fastapi import APIRouter, HTTPException
from models import Usuario, UsuarioCreate

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.post("/", response_model=Usuario, status_code=201 )
async def crear_usuario(new_usuario:UsuarioCreate, session:SessionDep):
    usuario = Usuario(**new_usuario.model_dump())
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario

@router.get("/", response_model=list[Usuario])
async def obtener_usuarios(session: SessionDep):
    return session.query(Usuario).all()

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
    session.add(usuario_db)
    session.commit()
    session.refresh(usuario_db)
    return usuario_db

@router.delete("/{id_usuario}")
async def eliminar_usuario(id_usuario:int, session:SessionDep):
    usuario_db = session.get(Usuario, id_usuario)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuario not found")
    session.delete(usuario_db)
    session.commit()
    return { "message": "Usuario eliminado" }