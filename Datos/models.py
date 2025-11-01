from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, date
from enum import Enum
from pydantic import field_validator
import re


class RolUsuario(str, Enum):
    """
    Roles disponibles para usuarios del sistema.

    - PADRE: Usuario padre/tutor con permisos completos
    - HIJO: Usuario hijo/estudiante con permisos limitados
    """
    PADRE = "Padre"
    HIJO = "Hijo"


class TipoMovimiento(str, Enum):
    """
    Tipos de movimientos de inventario.

    - ENTRADA: Ingreso de stock (compras, devoluciones)
    - SALIDA: Egreso de stock (ventas, consumo)
    - AJUSTE: Correcciones de inventario
    """
    ENTRADA = "Entrada"
    SALIDA = "Salida"
    AJUSTE = "Ajuste"


class CategoriaAlimento(str, Enum):
    """
    Categorías para clasificación de alimentos.
    """
    FRUTAS = "Frutas"
    VEGETALES = "Vegetales"
    PROTEINAS = "Proteínas"
    LACTEOS = "Lácteos"
    CEREALES = "Cereales"
    SNACKS = "Snacks"
    BEBIDAS = "Bebidas"


class NivelSeveridad(str, Enum):
    """
    Nivel de severidad para restricciones alimentarias.
    """
    BAJO = "Bajo"
    MEDIO = "Medio"
    ALTO = "Alto"


class EstadoPedido(str, Enum):
    """
    Estados posibles de un pedido.
    """
    PENDIENTE = "Pendiente"
    CONFIRMADO = "Confirmado"
    EN_PREPARACION = "En Preparación"
    ENTREGADO = "Entregado"
    CANCELADO = "Cancelado"


# ====================================================================
# USUARIO
# ====================================================================

class UsuarioBase(SQLModel):
    """
    Modelo base de Usuario con validaciones.

    Attributes:
        nombre: Nombre del usuario (3-50 caracteres, solo letras)
        apellido: Apellido del usuario (3-50 caracteres, solo letras)
        localidad: Localidad/ciudad del usuario
        edad: Edad del usuario (1-120 años)
        rol: Rol del usuario (Padre o Hijo)
        cedula: Cédula única del usuario (formato numérico)
        email: Email opcional del usuario
    """
    nombre: str = Field(min_length=3, max_length=50, description="Nombre del usuario")
    apellido: str = Field(min_length=3, max_length=50, description="Apellido del usuario")
    localidad: str = Field(min_length=3, max_length=100, description="Localidad del usuario")
    edad: int = Field(ge=1, le=120, description="Edad del usuario")
    rol: RolUsuario = Field(description="Rol del usuario (Padre o Hijo)")
    cedula: str = Field(unique=True, index=True, min_length=6, max_length=15, description="Cédula del usuario")
    email: Optional[str] = Field(default=None, max_length=100, description="Email del usuario")

    @field_validator('nombre', 'apellido')
    @classmethod
    def validar_solo_letras(cls, v: str) -> str:
        """Valida que nombre y apellido contengan solo letras y espacios."""
        patron = r"^[a-zA-ZñÑáéíóúÁÉÍÓÚüÜ\s]+$"
        if not re.match(patron, v):
            raise ValueError(f"El campo debe contener solo letras y espacios. Valor recibido: '{v}'")
        return v.strip()

    @field_validator('cedula')
    @classmethod
    def validar_cedula(cls, v: str) -> str:
        """Valida formato de cédula (solo números y guiones)."""
        patron = r"^[0-9\-]+$"
        if not re.match(patron, v):
            raise ValueError(f"La cédula debe contener solo números y guiones. Valor recibido: '{v}'")
        return v.strip()


class Usuario(UsuarioBase, table=True):
    """
    Modelo de tabla Usuario con relaciones.

    Relaciones:
    - One-to-Many con Lonchera (loncheras creadas)
    - One-to-One con Perfil (información adicional)
    - One-to-Many con Pedido (pedidos realizados)
    - One-to-Many con HistorialEliminacion (registros de eliminaciones)

    Attributes:
        id: Identificador único
        is_active: Indica si el usuario está activo
        fecha_creacion: Fecha de creación del registro
        fecha_modificacion: Última fecha de modificación
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    is_active: bool = Field(default=True, description="Indica si el usuario está activo")
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    fecha_modificacion: Optional[datetime] = Field(default=None)

    # Relaciones
    loncheras: List["Lonchera"] = Relationship(back_populates="usuario")
    perfil: Optional["Perfil"] = Relationship(back_populates="usuario", sa_relationship_kwargs={"uselist": False})
    pedidos: List["Pedido"] = Relationship(back_populates="usuario")
    historial: List["HistorialEliminacion"] = Relationship(back_populates="usuario_eliminador")


class UsuarioCreate(UsuarioBase):
    """
    Esquema para crear un nuevo usuario.
    Hereda todas las validaciones de UsuarioBase.
    """
    pass


class UsuarioUpdate(SQLModel):
    """
    Esquema para actualización parcial de usuario.
    Todos los campos son opcionales.
    """
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=50)
    apellido: Optional[str] = Field(default=None, min_length=3, max_length=50)
    localidad: Optional[str] = Field(default=None, min_length=3, max_length=100)
    edad: Optional[int] = Field(default=None, ge=1, le=120)
    rol: Optional[RolUsuario] = None
    email: Optional[str] = Field(default=None, max_length=100)

    @field_validator('nombre', 'apellido')
    @classmethod
    def validar_solo_letras_opcional(cls, v: Optional[str]) -> Optional[str]:
        """Valida campos de texto si se proporcionan."""
        if v is None:
            return None
        patron = r"^[a-zA-ZñÑáéíóúÁÉÍÓÚüÜ\s]+$"
        if not re.match(patron, v):
            raise ValueError(f"El campo debe contener solo letras y espacios. Valor recibido: '{v}'")
        return v.strip()


class UsuarioResumen(SQLModel):
    """
    Esquema resumido de usuario para respuestas anidadas.
    """
    id: int
    nombre: str
    apellido: str
    rol: RolUsuario
    is_active: bool


class UsuarioConRelaciones(UsuarioBase):
    """
    Esquema de respuesta de usuario con sus relaciones.
    """
    id: int
    is_active: bool
    fecha_creacion: datetime
    loncheras: List["LoncheraResumen"] = []


# ====================================================================
# PERFIL
# ====================================================================

class PerfilBase(SQLModel):
    """
    Modelo base de Perfil de usuario.

    Attributes:
        bio: Biografía o descripción del usuario
        telefono: Número de teléfono de contacto
        foto_url: URL de la foto de perfil
    """
    bio: Optional[str] = Field(default=None, max_length=500)
    telefono: Optional[str] = Field(default=None, max_length=20)
    foto_url: Optional[str] = Field(default=None, max_length=500)

    @field_validator('telefono')
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        """Valida formato de teléfono."""
        if v is None:
            return None
        patron = r"^[\d\s\+\-\(\)]+$"
        if not re.match(patron, v):
            raise ValueError(f"Formato de teléfono inválido: '{v}'")
        return v.strip()


class Perfil(PerfilBase, table=True):
    """
    Modelo de tabla Perfil con relación One-to-One con Usuario.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", unique=True)

    usuario: Optional[Usuario] = Relationship(back_populates="perfil")


class PerfilCreate(PerfilBase):
    """
    Esquema para crear un perfil de usuario.
    """
    usuario_id: int


class PerfilUpdate(PerfilBase):
    """
    Esquema para actualización parcial de perfil.
    """
    pass


# ====================================================================
# ALIMENTO
# ====================================================================

class AlimentoBase(SQLModel):
    """
    Modelo base de Alimento con validaciones nutricionales.

    Attributes:
        nombre: Nombre del alimento
        categoria: Categoría del alimento
        calorias_por_100g: Calorías por 100 gramos
        proteinas_por_100g: Proteínas por 100 gramos
        carbohidratos_por_100g: Carbohidratos por 100 gramos
        grasas_por_100g: Grasas por 100 gramos
        precio_unitario: Precio por unidad/porción
    """
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
        """Redondea el precio a 2 decimales."""
        return round(v, 2)


class Alimento(AlimentoBase, table=True):
    """
    Modelo de tabla Alimento con gestión de stock.

    Relaciones:
    - Many-to-Many con Restriccion (restricciones alimentarias)
    - Many-to-Many con Lonchera (composición de loncheras)
    - One-to-Many con MovimientoInventario (historial de stock)
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    stock_actual: int = Field(default=0, ge=0, description="Stock disponible")
    is_active: bool = Field(default=True)
    fecha_creacion: datetime = Field(default_factory=datetime.now)

    restricciones: List["RestriccionAlimento"] = Relationship(back_populates="alimento")
    loncheras: List["LoncheraAlimento"] = Relationship(back_populates="alimento")
    movimientos: List["MovimientoInventario"] = Relationship(back_populates="alimento")


class AlimentoCreate(AlimentoBase):
    """
    Esquema para crear un nuevo alimento.
    """
    stock_inicial: int = Field(default=0, ge=0, description="Stock inicial del alimento")


class AlimentoUpdate(SQLModel):
    """
    Esquema para actualización parcial de alimento.
    """
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=100)
    categoria: Optional[CategoriaAlimento] = None
    calorias_por_100g: Optional[float] = Field(default=None, ge=0, le=1000)
    proteinas_por_100g: Optional[float] = Field(default=None, ge=0, le=100)
    carbohidratos_por_100g: Optional[float] = Field(default=None, ge=0, le=100)
    grasas_por_100g: Optional[float] = Field(default=None, ge=0, le=100)
    precio_unitario: Optional[float] = Field(default=None, ge=0)

    @field_validator('precio_unitario')
    @classmethod
    def redondear_precio_opcional(cls, v: Optional[float]) -> Optional[float]:
        """Redondea el precio a 2 decimales si se proporciona."""
        if v is not None:
            return round(v, 2)
        return None


class AlimentoResumen(SQLModel):
    """
    Esquema resumido de alimento para respuestas anidadas.
    """
    id: int
    nombre: str
    categoria: CategoriaAlimento
    precio_unitario: float
    stock_actual: int


# ====================================================================
# RESTRICCIÓN ALIMENTARIA / ALERGIA
# ====================================================================

class RestriccionBase(SQLModel):
    """
    Modelo base de Restricción alimentaria o alergia.

    Attributes:
        nombre: Nombre de la restricción (ej: "Alergia al maní")
        descripcion: Descripción detallada
        nivel_severidad: Nivel de severidad (Bajo, Medio, Alto)
    """
    nombre: str = Field(min_length=3, max_length=100, unique=True, description="Nombre de la restricción/alergia")
    descripcion: Optional[str] = Field(default=None, max_length=500, description="Descripción detallada")
    nivel_severidad: NivelSeveridad = Field(description="Nivel de severidad")


class Restriccion(RestriccionBase, table=True):
    """
    Modelo de tabla Restricción con relaciones.

    Relaciones:
    - Many-to-Many con Alimento (alimentos restringidos)
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha_creacion: datetime = Field(default_factory=datetime.now)

    alimentos: List["RestriccionAlimento"] = Relationship(back_populates="restriccion")


class RestriccionCreate(RestriccionBase):
    """
    Esquema para crear una nueva restricción.
    """
    pass


class RestriccionUpdate(SQLModel):
    """
    Esquema para actualización parcial de restricción.
    """
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=100)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    nivel_severidad: Optional[NivelSeveridad] = None


class RestriccionResumen(SQLModel):
    """
    Esquema resumido de restricción.
    """
    id: int
    nombre: str
    nivel_severidad: NivelSeveridad


# ====================================================================
# TABLA INTERMEDIA: RESTRICCIÓN - ALIMENTO
# ====================================================================

class RestriccionAlimento(SQLModel, table=True):
    """
    Tabla intermedia Many-to-Many entre Restricción y Alimento.

    Representa qué alimentos están asociados a cada restricción alimentaria.
    """
    restriccion_id: int = Field(foreign_key="restriccion.id", primary_key=True)
    alimento_id: int = Field(foreign_key="alimento.id", primary_key=True)
    fecha_asociacion: datetime = Field(default_factory=datetime.now)

    restriccion: Optional[Restriccion] = Relationship(back_populates="alimentos")
    alimento: Optional[Alimento] = Relationship(back_populates="restricciones")


# ====================================================================
# LONCHERA
# ====================================================================

class LoncheraBase(SQLModel):
    """
    Modelo base de Lonchera.

    Attributes:
        nombre: Nombre descriptivo de la lonchera
        descripcion: Descripción de la lonchera
        calorias: Total de calorías (calculado)
        precio: Precio total (calculado)
    """
    nombre: str = Field(min_length=3, max_length=100, description="Nombre de la lonchera")
    descripcion: str = Field(min_length=10, max_length=500, description="Descripción de la lonchera")
    calorias: int = Field(default=0, ge=0, description="Calorías totales")
    precio: float = Field(default=0, ge=0, description="Precio total")

    @field_validator('precio')
    @classmethod
    def redondear_precio(cls, v: float) -> float:
        """Redondea el precio a 2 decimales."""
        return round(v, 2)


class Lonchera(LoncheraBase, table=True):
    """
    Modelo de tabla Lonchera.

    Relaciones:
    - Many-to-One con Usuario (creador)
    - Many-to-Many con Alimento (composición)
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id")
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True)

    usuario: Optional["Usuario"] = Relationship(back_populates="loncheras")
    alimentos: List["LoncheraAlimento"] = Relationship(back_populates="lonchera")


class LoncheraCreate(LoncheraBase):
    """
    Esquema para crear una nueva lonchera.
    """
    usuario_id: int = Field(description="ID del usuario creador")


class LoncheraUpdate(SQLModel):
    """
    Esquema para actualización parcial de lonchera.
    """
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=100)
    descripcion: Optional[str] = Field(default=None, min_length=10, max_length=500)
    calorias: Optional[int] = Field(default=None, ge=0)
    precio: Optional[float] = Field(default=None, ge=0)

    @field_validator('precio')
    @classmethod
    def redondear_precio_opcional(cls, v: Optional[float]) -> Optional[float]:
        """Redondea el precio si se proporciona."""
        if v is not None:
            return round(v, 2)
        return None


class LoncheraResumen(SQLModel):
    """
    Esquema resumido de lonchera.
    """
    id: int
    nombre: str
    calorias: int
    precio: float


class LoncheraConRelaciones(LoncheraBase):
    """
    Esquema de respuesta de lonchera con relaciones completas.
    """
    id: int
    usuario_id: int
    fecha_creacion: datetime
    usuario: UsuarioResumen
    alimentos: List["LoncheraAlimentoDetalle"] = []


# ====================================================================
# TABLA INTERMEDIA: LONCHERA - ALIMENTO
# ====================================================================

class LoncheraAlimento(SQLModel, table=True):
    """
    Tabla intermedia Many-to-Many entre Lonchera y Alimento.

    Especifica la cantidad en gramos de cada alimento en la lonchera.
    """
    lonchera_id: int = Field(foreign_key="lonchera.id", primary_key=True)
    alimento_id: int = Field(foreign_key="alimento.id", primary_key=True)
    cantidad_gramos: float = Field(ge=0, description="Cantidad en gramos")

    lonchera: Optional[Lonchera] = Relationship(back_populates="alimentos")
    alimento: Optional[Alimento] = Relationship(back_populates="loncheras")


class LoncheraAlimentoDetalle(SQLModel):
    """
    Esquema para mostrar detalles de alimentos en lonchera.
    """
    alimento_id: int
    nombre_alimento: str
    cantidad_gramos: float
    calorias_porcion: float
    precio_porcion: float


class AgregarAlimento(SQLModel):
    """
    Esquema para agregar alimento a lonchera.
    """
    alimento_id: int = Field(description="ID del alimento")
    cantidad_gramos: float = Field(gt=0, description="Cantidad en gramos")


# ====================================================================
# PRODUCTO (para sistema de pedidos)
# ====================================================================

class ProductoBase(SQLModel):
    """
    Modelo base de Producto para pedidos.
    """
    nombre: str = Field(min_length=3, max_length=100, description="Nombre del producto")
    descripcion: Optional[str] = Field(default=None, max_length=500)
    precio: float = Field(ge=0, description="Precio del producto")
    stock_actual: int = Field(default=0, ge=0, description="Stock disponible")

    @field_validator('precio')
    @classmethod
    def redondear_precio(cls, v: float) -> float:
        """Redondea el precio a 2 decimales."""
        return round(v, 2)


class Producto(ProductoBase, table=True):
    """
    Modelo de tabla Producto.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    is_active: bool = Field(default=True)
    fecha_creacion: datetime = Field(default_factory=datetime.now)

    pedidos: List["PedidoProducto"] = Relationship(back_populates="producto")


class ProductoCreate(ProductoBase):
    """
    Esquema para crear un nuevo producto.
    """
    pass


class ProductoUpdate(SQLModel):
    """
    Esquema para actualización parcial de producto.
    """
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


# ====================================================================
# PEDIDO
# ====================================================================

class PedidoBase(SQLModel):
    """
    Modelo base de Pedido.
    """
    total: float = Field(default=0.0, ge=0, description="Total del pedido")
    estado: EstadoPedido = Field(default=EstadoPedido.PENDIENTE, description="Estado del pedido")

    @field_validator('total')
    @classmethod
    def redondear_total(cls, v: float) -> float:
        """Redondea el total a 2 decimales."""
        return round(v, 2)


class Pedido(PedidoBase, table=True):
    """
    Modelo de tabla Pedido.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id")
    fecha: datetime = Field(default_factory=datetime.now)

    productos: List["PedidoProducto"] = Relationship(back_populates="pedido")
    usuario: Optional[Usuario] = Relationship(back_populates="pedidos")


class PedidoCreate(SQLModel):
    """
    Esquema para crear un nuevo pedido.
    """
    usuario_id: int


class PedidoUpdate(SQLModel):
    """
    Esquema para actualizar un pedido.
    """
    estado: Optional[EstadoPedido] = None


# ====================================================================
# TABLA INTERMEDIA: PEDIDO - PRODUCTO
# ====================================================================

class PedidoProducto(SQLModel, table=True):
    """
    Tabla intermedia Many-to-Many entre Pedido y Producto.

    Almacena cantidad y precios al momento del pedido.
    """
    pedido_id: int = Field(foreign_key="pedido.id", primary_key=True)
    producto_id: int = Field(foreign_key="producto.id", primary_key=True)
    cantidad: int = Field(ge=1, description="Cantidad solicitada")
    precio_unitario: float = Field(ge=0, description="Precio al momento del pedido")
    subtotal: float = Field(ge=0, description="Subtotal calculado")

    pedido: Optional[Pedido] = Relationship(back_populates="productos")
    producto: Optional[Producto] = Relationship(back_populates="pedidos")


class AgregarProductoPedido(SQLModel):
    """
    Esquema para agregar producto a pedido.
    """
    producto_id: int
    cantidad: int = Field(ge=1)


# ====================================================================
# MOVIMIENTO DE INVENTARIO
# ====================================================================

class MovimientoInventarioBase(SQLModel):
    """
    Modelo base de Movimiento de inventario.
    """
    alimento_id: int = Field(foreign_key="alimento.id")
    tipo_movimiento: TipoMovimiento
    cantidad: int = Field(description="Cantidad movida (positivo para entrada, negativo para salida)")
    motivo: Optional[str] = Field(default=None, max_length=200, description="Motivo del movimiento")


class MovimientoInventario(MovimientoInventarioBase, table=True):
    """
    Modelo de tabla MovimientoInventario.

    Registra historial de cambios en stock de alimentos.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha: datetime = Field(default_factory=datetime.now)
    stock_anterior: int = Field(ge=0)
    stock_nuevo: int = Field(ge=0)
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuario.id")

    alimento: Optional[Alimento] = Relationship(back_populates="movimientos")


class MovimientoInventarioCreate(MovimientoInventarioBase):
    """
    Esquema para crear un movimiento de inventario.
    """
    usuario_id: int


# ====================================================================
# HISTORIAL DE ELIMINACIONES
# ====================================================================

class HistorialEliminacionBase(SQLModel):
    """
    Modelo base de Historial de eliminaciones.

    Registra todos los registros eliminados para auditoría.
    """
    tabla_nombre: str = Field(description="Nombre de la tabla (usuario, lonchera, etc)")
    registro_id: int = Field(description="ID del registro eliminado")
    datos_json: str = Field(description="JSON con los datos del registro eliminado")
    motivo: Optional[str] = Field(default=None, max_length=500, description="Motivo de la eliminación")


class HistorialEliminacion(HistorialEliminacionBase, table=True):
    """
    Modelo de tabla HistorialEliminacion.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha_eliminacion: date = Field(default_factory=date.today)
    usuario_eliminador_id: Optional[int] = Field(default=None, foreign_key="usuario.id")

    usuario_eliminador: Optional[Usuario] = Relationship(back_populates="historial")


class HistorialEliminacionCreate(HistorialEliminacionBase):
    """
    Esquema para crear registro de historial.
    """
    usuario_eliminador_id: int


# ====================================================================
# RECONSTRUCCIÓN DE MODELOS
# ====================================================================

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