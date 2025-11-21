from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Annotated
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from Core.database import SessionDep
from Core.seguridad import verificar_password
from Modulos.models import Usuario

SECRET_KEY = "A]m42[GBVb.59=!"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"]
)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user(session: AsyncSession, email: str) -> Usuario | None:
    statement = select(Usuario).where(Usuario.email == email)
    result = await session.execute(statement)
    return result.scalars().first()

async def authenticate_user(session: AsyncSession, email: str, password: str) -> Usuario | None:
    usuario = await get_user(session, email)
    if not usuario:
        return None
    if not verificar_password(password, usuario.hashed_password):
        return None
    return usuario

@router.post("/token")
async def login_para_access_token(
        session: SessionDep,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    email = form_data.username
    password = form_data.password

    usuario = await authenticate_user(session, email, password)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": usuario.email},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(
        session: SessionDep,
        token: Annotated[str, Depends(oauth2_scheme)]
) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    usuario = await get_user(session, email=email)
    if usuario is None:
        raise credentials_exception

    return usuario