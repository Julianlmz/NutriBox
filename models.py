from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship

class UsuarioBase(SQLModel):
    nombre: str = Field(description="Nombre del usuario")
    apellido: str = Field(description="Apellido del usuario")
    localidad: str = Field(description="Localidad del usuario")
    edad: int = Field(description="Edad")

class Usuario(UsuarioBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    cedula: int = Field(unique=True, description="Cédula del usuario")

class UsuarioCreate(UsuarioBase):
    cedula: str = Field(description="Cédula del usuario")

