from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import date

class UsuarioBase(SQLModel):
    nombre: str = Field(description="Nombre del usuario")
    apellido: str = Field(description="Apellido del usuario")
    localidad: str = Field(description="Localidad del usuario")
    edad: int = Field(description="Edad")
    rol: str = Field(description="Rol del usuario (Padre o Hijo)")
    cedula: int = Field(unique=True, description="Cédula del usuario")

class Usuario(UsuarioBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    loncheras: List["Lonchera"] = Relationship(back_populates="usuario")


class UsuarioCreate(UsuarioBase):
    pass

class LoncheraBase(SQLModel):
    nombre: str = Field(description="Nombre de la lonchera")
    descripcion: str = Field(description="Descripcion de la lonchera")
    calorias: int = Field(description="Calorias de la lonchera")
    precio: float = Field(description="Precio de la lonchera")
    fecha_creacion: Optional[date] = Field(default_factory=date.today, description="Fecha de creacion de la lonchera")

class Lonchera(LoncheraBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuario.id")
    usuario: Optional["Usuario"] = Relationship(back_populates="loncheras")

class LoncheraCreate(LoncheraBase):
    usuario_id: Optional[int] = Field(default=None, description="Id del creador")

Usuario.update_forward_refs()
Lonchera.update_forward_refs()
