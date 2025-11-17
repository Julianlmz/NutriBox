from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from sqlmodel import Session, select

from Aplicacion.database import SessionDep
from Aplicacion.seguridad import verificar_password
from Datos.models import Usuario

# --- Configuración de Seguridad para los Tokens ---

# ¡SECRETO! Cambia esto por una cadena larga y aleatoria.
# Puedes generar una con: openssl rand -hex 32
SECRET_KEY = "A]m42[GBVb.59=!"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Duración del token

# Creamos un router solo para la autenticación
router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"]
)


# --- Funciones Auxiliares ---

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Crea un nuevo token de acceso (JWT).
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Por defecto, expira en 15 minutos
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user(session: Session, email: str) -> Usuario | None:
    """
    Busca un usuario en la base de datos por su email.
    """
    statement = select(Usuario).where(Usuario.email == email)
    return session.exec(statement).first()


def authenticate_user(session: Session, email: str, password: str) -> Usuario | None:
    """
    Autentica a un usuario. Compara la contraseña plana con la hasheada.
    """
    usuario = get_user(session, email)
    if not usuario:
        # No se encontró el usuario
        return None

    if not verificar_password(password, usuario.hashed_password):
        # La contraseña es incorrecta
        return None

    # El usuario está autenticado
    return usuario


# --- Endpoint de Login ---

@router.post("/token")
async def login_para_access_token(
        session: SessionDep,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    """
    Endpoint de login. Recibe 'username' (email) y 'password' desde un formulario.
    """
    # Tu frontend usa 'email' para el login, pero OAuth2 usa 'username'
    # Así que, tratamos 'form_data.username' como si fuera el email
    email = form_data.username
    password = form_data.password

    usuario = authenticate_user(session, email, password)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Creamos el token de acceso
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": usuario.email},  # "sub" (subject) es el email del usuario
        expires_delta=access_token_expires
    )

    # Esto es lo que recibe tu login.js
    return {"access_token": access_token, "token_type": "bearer"}