from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, date
from enum import Enum
from pydantic import field_validator
import re


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


class NivelSeveridad(str, Enum):
    BAJO = "Bajo"
    MEDIO = "Medio"
    ALTO = "Alto"


class EstadoPedido(str, Enum):
    PENDIENTE = "Pendiente"
    CONFIRMADO = "Confirmado"
    EN_PREPARACION = "En Preparación"
    ENTREGADO = "Entregado"
    CANCELADO = "Cancelado"

# ====================================================================
# DIRECCIÓN
# ====================================================================

class DireccionBase(SQLModel):
    nombre: Optional[str] = Field(default=None, max_length=100)
    direccion: str = Field(min_length=5, max_length=200)
    ciudad: Optional[str] = Field(default="Bogotá", max_length=100)
    principal: bool = Field(default=False)

class Direccion(DireccionBase, table=True):
    __tablename__ = "direcciones_v2"
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id")
    fecha_creacion: datetime = Field(default_factory=datetime.now)

    usuario: Optional["Usuario"] = Relationship(back_populates="direcciones")
    loncheras: List["Lonchera"] = Relationship(back_populates="direccion")

class DireccionCreate(DireccionBase):
    pass

class DireccionUpdate(SQLModel):
    nombre: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    principal: Optional[bool] = None

# ====================================================================
# USUARIO
# ====================================================================

class UsuarioBase(SQLModel):
    nombre: str = Field(min_length=3, max_length=50, description="Nombre del usuario")
    apellido: str = Field(min_length=3, max_length=50, description="Apellido del usuario")
    email: Optional[str] = Field(default=None, max_length=100, description="Email del usuario")

    @field_validator('nombre', 'apellido')
    @classmethod
    def validar_solo_letras(cls, v: str) -> str:
        patron = r"^[a-zA-ZñÑáéíóúÁÉÍÓÚüÜ\s]+$"
        if not re.match(patron, v):
            raise ValueError(f"El campo debe contener solo letras y espacios. Valor recibido: '{v}'")
        return v.strip()


class Usuario(UsuarioBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(index=True)
    is_active: bool = Field(default=True, description="Indica si el usuario está activo")

    loncheras: List["Lonchera"] = Relationship(back_populates="usuario")
    perfil: Optional["Perfil"] = Relationship(back_populates="usuario", sa_relationship_kwargs={"uselist": False})
    pedidos: List["Pedido"] = Relationship(back_populates="usuario")
    historial: List["HistorialEliminacion"] = Relationship(back_populates="usuario_eliminador")
    direcciones: List["Direccion"] = Relationship(back_populates="usuario")


class UsuarioCreate(UsuarioBase):
    password: str


class UsuarioUpdate(SQLModel):
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=50)
    apellido: Optional[str] = Field(default=None, min_length=3, max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)

    @field_validator('nombre', 'apellido')
    @classmethod
    def validar_solo_letras_opcional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        patron = r"^[a-zA-ZñÑáéíóúÁÉÍÓÚüÜ\s]+$"
        if not re.match(patron, v):
            raise ValueError(f"El campo debe contener solo letras y espacios. Valor recibido: '{v}'")
        return v.strip()


class UsuarioResumen(SQLModel):
    id: int
    nombre: str
    apellido: str
    is_active: bool


class UsuarioConRelaciones(UsuarioBase):
    id: int
    is_active: bool
    loncheras: List["LoncheraResumen"] = []


# ====================================================================
# PERFIL / ALIMENTO / RESTRICCIÓN
# ====================================================================

class PerfilBase(SQLModel):
    bio: Optional[str] = Field(default=None, max_length=500)
    telefono: Optional[str] = Field(default=None, max_length=20)
    foto_url: Optional[str] = Field(default=None, max_length=500)

    @field_validator('telefono')
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        patron = r"^[\d\s\+\-\(\)]+$"
        if not re.match(patron, v):
            raise ValueError(f"Formato de teléfono inválido: '{v}'")
        return v.strip()


class Perfil(PerfilBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", unique=True)
    usuario: Optional[Usuario] = Relationship(back_populates="perfil")
    foto_url: Optional[str] = Field(default=None)


class PerfilCreate(PerfilBase):
    usuario_id: int


class PerfilUpdate(PerfilBase):
    pass


class AlimentoBase(SQLModel):
    nombre: str = Field(min_length=2, max_length=100, index=True, description="Nombre del alimento")
    categoria: CategoriaAlimento
    calorias_por_100g: float = Field(ge=0, le=1000, description="Calorías por 100g")
    proteinas_por_100g: float = Field(ge=0, le=100, description="Proteínas por 100g")
    carbohidratos_por_100g: float = Field(ge=0, le=100, description="Carbohidratos por 100g")
    grasas_por_100g: float = Field(ge=0, le=100, description="Grasas por 100g")
    precio_unitario: float = Field(ge=0, description="Precio unitario")

    @field_validator('precio_unitario')
    @classmethod
    def redondear_precio(cls, v: float) -> float:
        return round(v, 2)


class Alimento(AlimentoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    imagen_url: Optional[str] = Field(default=None, description="URL de la imagen del alimento")
    stock_actual: int = Field(default=0, ge=0, description="Stock disponible")
    is_active: bool = Field(default=True)

    restricciones: List["RestriccionAlimento"] = Relationship(back_populates="alimento")
    loncheras: List["LoncheraAlimento"] = Relationship(back_populates="alimento")
    movimientos: List["MovimientoInventario"] = Relationship(back_populates="alimento")


class AlimentoCreate(AlimentoBase):
    stock_inicial: int = Field(default=0, ge=0, description="Stock inicial del alimento")


class AlimentoUpdate(SQLModel):
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=100)
    categoria: Optional[CategoriaAlimento] = None
    calorias_por_100g: Optional[float] = Field(default=None, ge=0, le=1000)
    proteinas_por_100g: Optional[float] = Field(default=None, ge=0, le=100)
    carbohidratos_por_100g: Optional[float] = Field(default=None, ge=0, le=100)
    grasas_por_100g: Optional[float] = Field(default=None, ge=0, le=100)
    precio_unitario: Optional[float] = Field(default=None, ge=0)
    imagen_url: Optional[str] = Field(default=None, max_length=500, description="URL de la imagen del alimento")

    @field_validator('precio_unitario')
    @classmethod
    def redondear_precio_opcional(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            return round(v, 2)
        return None


class AlimentoResumen(SQLModel):
    id: int
    nombre: str
    categoria: CategoriaAlimento
    precio_unitario: float
    stock_actual: int


class RestriccionBase(SQLModel):
    nombre: str = Field(min_length=3, max_length=100, unique=True, description="Nombre de la restricción/alergia")
    descripcion: Optional[str] = Field(default=None, max_length=500, description="Descripción detallada")
    nivel_severidad: NivelSeveridad = Field(description="Nivel de severidad")


class Restriccion(RestriccionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha_creacion: datetime = Field(default_factory=datetime.now)

    alimentos: List["RestriccionAlimento"] = Relationship(back_populates="restriccion")


class RestriccionCreate(RestriccionBase):
    pass


class RestriccionUpdate(SQLModel):
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=100)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    nivel_severidad: Optional[NivelSeveridad] = None


class RestriccionResumen(SQLModel):
    id: int
    nombre: str
    nivel_severidad: NivelSeveridad


class RestriccionAlimento(SQLModel, table=True):
    restriccion_id: int = Field(foreign_key="restriccion.id", primary_key=True)
    alimento_id: int = Field(foreign_key="alimento.id", primary_key=True)
    fecha_asociacion: datetime = Field(default_factory=datetime.now)

    restriccion: Optional[Restriccion] = Relationship(back_populates="alimentos")
    alimento: Optional[Alimento] = Relationship(back_populates="restricciones")


class RestriccionHijo(SQLModel, table=True):
    __tablename__ = "restriccion_hijo"

    hijo_id: int = Field(foreign_key="usuario.id", primary_key=True)
    restriccion_id: int = Field(foreign_key="restriccion.id", primary_key=True)
    fecha_asociacion: datetime = Field(default_factory=datetime.now)

# ====================================================================
# LONCHERA
# ====================================================================

class LoncheraBase(SQLModel):
    nombre: str = Field(min_length=3, max_length=100, description="Nombre de la lonchera")
    descripcion: str = Field(min_length=10, max_length=500, description="Descripción de la lonchera")
    calorias: int = Field(default=0, ge=0, description="Calorías totales")
    precio: float = Field(default=0, ge=0, description="Precio total")

    @field_validator('precio')
    @classmethod
    def redondear_precio(cls, v: float) -> float:
        return round(v, 2)


class Lonchera(LoncheraBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id")
    direccion_id: Optional[int] = Field(default=None, foreign_key="direcciones_v2.id")
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True)

    usuario: Optional["Usuario"] = Relationship(back_populates="loncheras")
    alimentos: List["LoncheraAlimento"] = Relationship(back_populates="lonchera")
    direccion: Optional["Direccion"] = Relationship(back_populates="loncheras")

class LoncheraCreate(LoncheraBase):
    usuario_id: int = Field(description="ID del usuario creador")
    direccion_id: int = Field(description="ID de la dirección de entrega obligatoria")


class LoncheraUpdate(SQLModel):
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=100)
    descripcion: Optional[str] = Field(default=None, min_length=10, max_length=500)
    calorias: Optional[int] = Field(default=None, ge=0)
    precio: Optional[float] = Field(default=None, ge=0)

    @field_validator('precio')
    @classmethod
    def redondear_precio_opcional(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            return round(v, 2)
        return None


class LoncheraResumen(SQLModel):
    id: int
    nombre: str
    calorias: int
    precio: float


class LoncheraConRelaciones(LoncheraBase):
    id: int
    usuario_id: int
    fecha_creacion: datetime
    usuario: UsuarioResumen
    alimentos: List["LoncheraAlimentoDetalle"] = []


# ====================================================================
# TABLA INTERMEDIA: LONCHERA - ALIMENTO
# ====================================================================

class LoncheraAlimento(SQLModel, table=True):
    lonchera_id: int = Field(foreign_key="lonchera.id", primary_key=True)
    alimento_id: int = Field(foreign_key="alimento.id", primary_key=True)
    cantidad_gramos: float = Field(ge=0, description="Cantidad en gramos")

    lonchera: Optional[Lonchera] = Relationship(back_populates="alimentos")
    alimento: Optional[Alimento] = Relationship(back_populates="loncheras")


class LoncheraAlimentoDetalle(SQLModel):
    alimento_id: int
    nombre_alimento: str
    cantidad_gramos: float
    calorias_porcion: float
    precio_porcion: float


class AgregarAlimento(SQLModel):
    alimento_id: int = Field(description="ID del alimento")
    cantidad_gramos: float = Field(gt=0, description="Cantidad en gramos")


# ====================================================================
# PRODUCTO / PEDIDO / INVENTARIO / HISTORIAL
# ====================================================================

class ProductoBase(SQLModel):
    nombre: str = Field(min_length=3, max_length=100, description="Nombre del producto")
    descripcion: Optional[str] = Field(default=None, max_length=500)
    precio: float = Field(ge=0, description="Precio del producto")
    stock_actual: int = Field(default=0, ge=0, description="Stock disponible")

    @field_validator('precio')
    @classmethod
    def redondear_precio(cls, v: float) -> float:
        return round(v, 2)


class Producto(ProductoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    is_active: bool = Field(default=True)
    fecha_creacion: datetime = Field(default_factory=datetime.now)

    pedidos: List["PedidoProducto"] = Relationship(back_populates="producto")


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(SQLModel):
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=100)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    precio: Optional[float] = Field(default=None, ge=0)
    stock_actual: Optional[int] = Field(default=None, ge=0)

    @field_validator('precio')
    @classmethod
    def redondear_precio_opcional(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            return round(v, 2)
        return None


class PedidoBase(SQLModel):
    total: float = Field(default=0.0, ge=0, description="Total del pedido")
    estado: EstadoPedido = Field(default=EstadoPedido.PENDIENTE, description="Estado del pedido")

    @field_validator('total')
    @classmethod
    def redondear_total(cls, v: float) -> float:
        return round(v, 2)


class Pedido(PedidoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id")
    fecha: datetime = Field(default_factory=datetime.now)

    productos: List["PedidoProducto"] = Relationship(back_populates="pedido")
    usuario: Optional[Usuario] = Relationship(back_populates="pedidos")


class PedidoCreate(SQLModel):
    usuario_id: int


class PedidoUpdate(SQLModel):
    estado: Optional[EstadoPedido] = None


class PedidoProducto(SQLModel, table=True):
    pedido_id: int = Field(foreign_key="pedido.id", primary_key=True)
    producto_id: int = Field(foreign_key="producto.id", primary_key=True)
    cantidad: int = Field(ge=1, description="Cantidad solicitada")
    precio_unitario: float = Field(ge=0, description="Precio al momento del pedido")
    subtotal: float = Field(ge=0, description="Subtotal calculado")

    pedido: Optional[Pedido] = Relationship(back_populates="productos")
    producto: Optional[Producto] = Relationship(back_populates="pedidos")


class AgregarProductoPedido(SQLModel):
    producto_id: int
    cantidad: int = Field(ge=1)


class MovimientoInventarioBase(SQLModel):
    alimento_id: int = Field(foreign_key="alimento.id")
    tipo_movimiento: TipoMovimiento
    cantidad: int = Field(description="Cantidad movida (positivo para entrada, negativo para salida)")
    motivo: Optional[str] = Field(default=None, max_length=200, description="Motivo del movimiento")


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
    motivo: Optional[str] = Field(default=None, max_length=500, description="Motivo de la eliminación")


class HistorialEliminacion(HistorialEliminacionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha_eliminacion: date = Field(default_factory=date.today)
    usuario_eliminador_id: Optional[int] = Field(default=None, foreign_key="usuario.id")

    usuario_eliminador: Optional[Usuario] = Relationship(back_populates="historial")


class HistorialEliminacionCreate(HistorialEliminacionBase):
    usuario_eliminador_id: int


# ====================================================================
# SCHEMAS DE LECTURA (PARA RESPUESTAS JSON CON RELACIONES)
# ====================================================================

class RestriccionAlimentoRead(SQLModel):
    restriccion_id: int
    alimento_id: int
    fecha_asociacion: datetime

class AlimentoRead(AlimentoBase):
    id: int
    imagen_url: Optional[str] = None
    stock_actual: int
    is_active: bool
    # Esto es lo que permite ver las restricciones en el JSON
    restricciones: List[RestriccionAlimentoRead] = []


# ====================================================================
# RECONSTRUCCIÓN DE MODELOS
# ====================================================================

Usuario.model_rebuild()
Lonchera.model_rebuild()
Perfil.model_rebuild()
Alimento.model_rebuild()
Restriccion.model_rebuild()
RestriccionAlimento.model_rebuild()
RestriccionHijo.model_rebuild()
LoncheraAlimento.model_rebuild()
Producto.model_rebuild()
Pedido.model_rebuild()
PedidoProducto.model_rebuild()
MovimientoInventario.model_rebuild()
HistorialEliminacion.model_rebuild()
Direccion.model_rebuild()