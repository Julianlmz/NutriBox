from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class RolUsuario(str, Enum):
    PADRE = "Padre"
    HIJO = "Hijo"

class TipoMovimiento(str, Enum):
    ENTRADA = "Entrada"
    SALIDA = "Salida"
    AJUSTE = "Ajuste"

class CategoriaAlimento(str, Enum):
    FRUTAS = "Frutas"
    VEGETALES = "Vegetales"
    PROTEINAS = "Proteínas"
    LACTEOS = "Lácteos"
    CEREALES = "Cereales"
    SNACKS = "Snacks"
    BEBIDAS = "Bebidas"

class UsuarioBase(SQLModel):
    nombre: str = Field(description="Nombre del usuario")
    apellido: str = Field(description="Apellido del usuario")
    localidad: str = Field(description="Localidad del usuario")
    edad: int = Field(description="Edad", ge=1, le=120)
    rol: RolUsuario = Field(description="Rol del usuario (Padre o Hijo)")
    cedula: str = Field(unique=True, index=True, description="Cédula del usuario")


class Usuario(UsuarioBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    is_active: bool = Field(default=True, description="Indica si el usuario está activo")
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    fecha_modificacion: Optional[datetime] = Field(default=None)

    # Relaciones
    loncheras: List["Lonchera"] = Relationship(back_populates="usuario")
    perfil: Optional["Perfil"] = Relationship(back_populates="usuario")
    pedidos: List["Pedido"] = Relationship(back_populates="usuario")
    historial: List["HistorialEliminacion"] = Relationship(back_populates="usuario_eliminador")


class UsuarioCreate(UsuarioBase):
    pass


class UsuarioUpdate(SQLModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    localidad: Optional[str] = None
    edad: Optional[int] = Field(default=None, ge=1, le=120)
    rol: Optional[RolUsuario] = None

class LoncheraBase(SQLModel):
    nombre: str = Field(description="Nombre de la lonchera", min_length=1, max_length=100)
    descripcion: str = Field(description="Descripcion de la lonchera")
    calorias: int = Field(description="Calorias de la lonchera", ge=0)
    precio: float = Field(description="Precio de la lonchera", ge=0)

class Lonchera(LoncheraBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id")
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True)

    usuario: Optional["Usuario"] = Relationship(back_populates="loncheras")
    alimentos: List["LoncheraAlimento"] = Relationship(back_populates="lonchera")


class LoncheraCreate(LoncheraBase):
    usuario_id: int = Field(description="Id del creador")

class Perfil(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", unique=True)
    bio: Optional[str] = Field(default=None, max_length=500)
    telefono: Optional[str] = Field(default=None, max_length=20)
    foto_url: Optional[str] = Field(default=None)

    usuario: Optional[Usuario] = Relationship(back_populates="perfil")

class AlimentoBase(SQLModel):
    nombre: str = Field(index=True, description="Nombre del alimento")
    categoria: CategoriaAlimento
    calorias_por_100g: float = Field(ge=0)
    proteinas_por_100g: float = Field(ge=0)
    carbohidratos_por_100g: float = Field(ge=0)
    grasas_por_100g: float = Field(ge=0)
    precio_unitario: float = Field(ge=0)


class Alimento(AlimentoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    stock_actual: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)
    fecha_creacion: datetime = Field(default_factory=datetime.now)

    restricciones: List["RestriccionAlimento"] = Relationship(back_populates="alimento")
    loncheras: List["LoncheraAlimento"] = Relationship(back_populates="alimento")
    movimientos: List["MovimientoInventario"] = Relationship(back_populates="alimento")


class AlimentoCreate(AlimentoBase):
    stock_inicial: int = Field(default=0, ge=0)


class RestriccionBase(SQLModel):
    nombre: str = Field(description="Nombre de la restricción/alergia", unique=True)
    descripcion: Optional[str] = None
    nivel_severidad: str = Field(description="Bajo, Medio, Alto")


class Restriccion(RestriccionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha_creacion: datetime = Field(default_factory=datetime.now)

    alimentos: List["RestriccionAlimento"] = Relationship(back_populates="restriccion")


class RestriccionCreate(RestriccionBase):
    pass


class RestriccionAlimento(SQLModel, table=True):
    restriccion_id: int = Field(foreign_key="restriccion.id", primary_key=True)
    alimento_id: int = Field(foreign_key="alimento.id", primary_key=True)
    fecha_asociacion: datetime = Field(default_factory=datetime.now)

    restriccion: Optional[Restriccion] = Relationship(back_populates="alimentos")
    alimento: Optional[Alimento] = Relationship(back_populates="restricciones")

class LoncheraAlimento(SQLModel, table=True):
    lonchera_id: int = Field(foreign_key="lonchera.id", primary_key=True)
    alimento_id: int = Field(foreign_key="alimento.id", primary_key=True)
    cantidad_gramos: float = Field(ge=0, description="Cantidad en gramos")

    lonchera: Optional[Lonchera] = Relationship(back_populates="alimentos")
    alimento: Optional[Alimento] = Relationship(back_populates="loncheras")

class ProductoBase(SQLModel):
    nombre: str = Field(description="Nombre del producto")
    descripcion: Optional[str] = None
    precio: float = Field(ge=0)
    stock_actual: int = Field(default=0, ge=0)


class Producto(ProductoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    is_active: bool = Field(default=True)
    fecha_creacion: datetime = Field(default_factory=datetime.now)

    pedidos: List["PedidoProducto"] = Relationship(back_populates="producto")


class ProductoCreate(ProductoBase):
    pass


class PedidoBase(SQLModel):
    fecha: datetime = Field(default_factory=datetime.now)
    usuario_id: int = Field(foreign_key="usuario.id")
    total: float = Field(default=0.0, ge=0)
    estado: str = Field(default="Pendiente")  # Pendiente, Confirmado, Entregado, Cancelado


class Pedido(PedidoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    productos: List["PedidoProducto"] = Relationship(back_populates="pedido")
    usuario: Optional[Usuario] = Relationship(back_populates="pedidos")


class PedidoCreate(SQLModel):
    usuario_id: int


class PedidoProducto(SQLModel, table=True):
    pedido_id: int = Field(foreign_key="pedido.id", primary_key=True)
    producto_id: int = Field(foreign_key="producto.id", primary_key=True)
    cantidad: int = Field(ge=1)
    precio_unitario: float = Field(ge=0, description="Precio al momento del pedido")
    subtotal: float = Field(ge=0)

    pedido: Optional[Pedido] = Relationship(back_populates="productos")
    producto: Optional[Producto] = Relationship(back_populates="pedidos")


class MovimientoInventarioBase(SQLModel):
    alimento_id: int = Field(foreign_key="alimento.id")
    tipo_movimiento: TipoMovimiento
    cantidad: int = Field(description="Cantidad movida (positivo o negativo)")
    motivo: Optional[str] = Field(default=None, max_length=200)


class MovimientoInventario(MovimientoInventarioBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha: datetime = Field(default_factory=datetime.now)
    stock_anterior: int = Field(ge=0)
    stock_nuevo: int = Field(ge=0)
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuario.id")

    alimento: Optional[Alimento] = Relationship(back_populates="movimientos")


class MovimientoInventarioCreate(MovimientoInventarioBase):
    usuario_id: int


class HistorialEliminacionBase(SQLModel):
    tabla_nombre: str = Field(description="Nombre de la tabla (usuario, lonchera, etc)")
    registro_id: int = Field(description="ID del registro eliminado")
    datos_json: str = Field(description="JSON con los datos del registro eliminado")
    motivo: Optional[str] = Field(default=None, max_length=500)


class HistorialEliminacion(HistorialEliminacionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha_eliminacion: datetime = Field(default_factory=datetime.now)
    usuario_eliminador_id: Optional[int] = Field(default=None, foreign_key="usuario.id")

    usuario_eliminador: Optional[Usuario] = Relationship(back_populates="historial")


class HistorialEliminacionCreate(HistorialEliminacionBase):
    usuario_eliminador_id: int


Usuario.model_rebuild()
Lonchera.model_rebuild()
Perfil.model_rebuild()
Alimento.model_rebuild()
Restriccion.model_rebuild()
RestriccionAlimento.model_rebuild()
LoncheraAlimento.model_rebuild()
Producto.model_rebuild()
Pedido.model_rebuild()
PedidoProducto.model_rebuild()
MovimientoInventario.model_rebuild()
HistorialEliminacion.model_rebuild()
