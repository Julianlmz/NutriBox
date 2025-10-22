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
    is_active: bool = Field(default=True, description="Indica si el usuario está activo")
    loncheras: List["Lonchera"] = Relationship(back_populates="usuario")
    perfil: Optional["Perfil"] = Relationship(back_populates="usuario")

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

# 1:1 Perfil
class Perfil(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuario.id", unique=True)
    bio: Optional[str] = Field(default=None)
    telefono: Optional[str] = Field(default=None)
    usuario: Optional[Usuario] = Relationship(back_populates="perfil")

# N:M: Pedido <-> Producto con tabla asociativa PedidoProducto
class ProductoBase(SQLModel):
    nombre: str = Field(description="Nombre del producto")
    precio: float = Field(default=0.0)

class Producto(ProductoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pedidos: List["PedidoProducto"] = Relationship(back_populates="producto")

class PedidoBase(SQLModel):
    fecha: Optional[date] = Field(default_factory=date.today)
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuario.id")

class Pedido(PedidoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    productos: List["PedidoProducto"] = Relationship(back_populates="pedido")
    usuario: Optional[Usuario] = Relationship()

class PedidoProducto(SQLModel, table=True):
    pedido_id: Optional[int] = Field(default=None, foreign_key="pedido.id", primary_key=True)
    producto_id: Optional[int] = Field(default=None, foreign_key="producto.id", primary_key=True)
    cantidad: int = Field(default=1)
    pedido: Optional[Pedido] = Relationship(back_populates="productos")
    producto: Optional[Producto] = Relationship(back_populates="pedidos")

# Forward refs
Usuario.update_forward_refs()
Lonchera.update_forward_refs()
Perfil.update_forward_refs()
Producto.update_forward_refs()
Pedido.update_forward_refs()
PedidoProducto.update_forward_refs()

