from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Aplicacion.db import create_tables

from Datos.models import (
    Usuario, Lonchera, Perfil, Alimento, Restriccion, RestriccionAlimento,
    LoncheraAlimento, Producto, Pedido, PedidoProducto,
    MovimientoInventario, HistorialEliminacion
)

from Datos import Usuario as UsuarioRouter
from Datos import Lonchera as LoncheraRouter
from Datos import Perfil as PerfilRouter
from Datos import Alimento as AlimentoRouter
from Datos import Restriccion as RestriccionRouter
from Alergias import Producto as ProductoRouter
from Alergias import Pedido as PedidoRouter
from Alergias import Inventario as InventarioRouter
from Alergias import Historial as HistorialRouter
from Alergias import Reporte as ReporteRouter

app = FastAPI(
    title="NutriBox API",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """Crea las tablas al iniciar la aplicación"""
    create_tables(app)
    print("✅ Base de datos inicializada con 12 modelos")
    print("📊 Modelos registrados:")
    print("   1. Usuario (CRUD completo)")
    print("   2. Perfil (CRUD completo) - Relación 1:1 con Usuario ✅")
    print("   3. Lonchera (CRUD completo) - Relación 1:N con Usuario ✅")
    print("   4. Alimento (CRUD completo)")
    print("   5. Restriccion (CRUD completo)")
    print("   6. RestriccionAlimento - Tabla N:M (Alimento ↔ Restriccion) ✅")
    print("   7. LoncheraAlimento - Tabla N:M (Lonchera ↔ Alimento) ✅")
    print("   8. Producto (CRUD completo)")
    print("   9. Pedido (CRUD completo)")
    print("   10. PedidoProducto - Tabla N:M (Pedido ↔ Producto) ✅")
    print("   11. MovimientoInventario (Gestión de inventario)")
    print("   12. HistorialEliminacion (Auditoría)")

# ========================================
# INCLUIR TODOS LOS ROUTERS
# ========================================

# Routers de modelos principales
app.include_router(UsuarioRouter.router)
app.include_router(PerfilRouter.router)
app.include_router(LoncheraRouter.router)
app.include_router(AlimentoRouter.router)
app.include_router(RestriccionRouter.router)
app.include_router(ProductoRouter.router)
app.include_router(PedidoRouter.router)

# Routers de funcionalidades
app.include_router(InventarioRouter.router)
app.include_router(HistorialRouter.router)
app.include_router(ReporteRouter.router)

@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raíz de la API.
    Muestra todos los endpoints disponibles organizados por tipo de relación.
    """
    return {
        "message": "🎉 API de NutriBox funcionando correctamente",
        "version": "2.1.0",
        "modelos_totales": 12,
        "relaciones": {
            "1:1": [
                "Usuario ↔ Perfil (Un usuario tiene un perfil)"
            ],
            "1:N": [
                "Usuario → Loncheras (Un usuario tiene muchas loncheras)",
                "Usuario → Pedidos (Un usuario hace muchos pedidos)",
                "Alimento → MovimientosInventario (Un alimento tiene muchos movimientos)"
            ],
            "N:M": [
                "Lonchera ↔ Alimento (tabla: LoncheraAlimento)",
                "Alimento ↔ Restriccion (tabla: RestriccionAlimento)",
                "Pedido ↔ Producto (tabla: PedidoProducto)"
            ]
        },
        "endpoints": {
            "usuarios": "/usuarios - CRUD completo",
            "perfiles": "/perfiles - CRUD completo (Relación 1:1) ✅ NUEVO",
            "loncheras": "/loncheras - CRUD completo + gestión de alimentos (Relación N:M) ✅",
            "alimentos": "/alimentos - CRUD completo",
            "restricciones": "/restricciones - CRUD completo + asociación con alimentos",
            "productos": "/productos - CRUD completo ✅ MEJORADO",
            "pedidos": "/pedidos - CRUD completo + gestión de productos",
            "inventario": "/inventario - Gestión de movimientos de stock",
            "historial": "/historial - Auditoría de eliminaciones",
            "reportes": "/reportes - Generación de reportes CSV"
        },
        "documentacion": "/docs",
        "documentacion_alternativa": "/redoc"
    }


@app.get("/hello/{name}", tags=["Root"])
async def say_hello(name: str):
    """Saludo personalizado"""
    return {"message": f"👋 Hola {name}, bienvenido a NutriBox API v2.1.0"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Verifica el estado de la API"""
    return {
        "status": "healthy",
        "service": "NutriBox API",
        "version": "2.1.0",
        "database": "SQLite3",
        "modelos_activos": 12,
        "routers_activos": 10
    }


@app.get("/relaciones", tags=["Documentación"])
async def explicar_relaciones():
    """
    Explica las relaciones entre los modelos del sistema.
    Útil para entender la estructura de la base de datos.
    """
    return {
        "relaciones_1_a_1": {
            "descripcion": "Un registro en una tabla se relaciona con exactamente un registro en otra tabla",
            "ejemplos": [
                {
                    "modelo_a": "Usuario",
                    "modelo_b": "Perfil",
                    "explicacion": "Cada usuario tiene UN perfil único. Un perfil pertenece a UN usuario.",
                    "campo_clave": "usuario_id (unique=True en Perfil)",
                    "endpoints": [
                        "POST /perfiles - Crear perfil para un usuario",
                        "GET /perfiles/usuario/{usuario_id} - Obtener el perfil de un usuario"
                    ]
                }
            ]
        },
        "relaciones_1_a_N": {
            "descripcion": "Un registro en una tabla se relaciona con muchos registros en otra tabla",
            "ejemplos": [
                {
                    "modelo_a": "Usuario",
                    "modelo_b": "Lonchera",
                    "explicacion": "Un usuario puede crear MUCHAS loncheras. Una lonchera pertenece a UN usuario.",
                    "campo_clave": "usuario_id (foreign key en Lonchera)",
                    "endpoints": [
                        "GET /loncheras?usuario_id=1 - Ver todas las loncheras de un usuario",
                        "POST /loncheras - Crear nueva lonchera para un usuario"
                    ]
                },
                {
                    "modelo_a": "Usuario",
                    "modelo_b": "Pedido",
                    "explicacion": "Un usuario puede hacer MUCHOS pedidos. Un pedido pertenece a UN usuario.",
                    "campo_clave": "usuario_id (foreign key en Pedido)",
                    "endpoints": [
                        "GET /pedidos?usuario_id=1 - Ver todos los pedidos de un usuario"
                    ]
                }
            ]
        },
        "relaciones_N_a_M": {
            "descripcion": "Muchos registros en una tabla se relacionan con muchos registros en otra tabla (requiere tabla intermedia)",
            "ejemplos": [
                {
                    "modelo_a": "Lonchera",
                    "modelo_b": "Alimento",
                    "tabla_intermedia": "LoncheraAlimento",
                    "explicacion": "Una lonchera puede tener MUCHOS alimentos. Un alimento puede estar en MUCHAS loncheras.",
                    "campos_extra": "cantidad_gramos (en la tabla intermedia)",
                    "endpoints": [
                        "POST /loncheras/{id}/alimentos/{alimento_id} - Agregar alimento a lonchera",
                        "GET /loncheras/{id}/alimentos - Ver alimentos de una lonchera",
                        "DELETE /loncheras/{id}/alimentos/{alimento_id} - Quitar alimento"
                    ]
                },
                {
                    "modelo_a": "Alimento",
                    "modelo_b": "Restriccion",
                    "tabla_intermedia": "RestriccionAlimento",
                    "explicacion": "Un alimento puede tener MUCHAS restricciones. Una restricción aplica a MUCHOS alimentos.",
                    "campos_extra": "fecha_asociacion",
                    "endpoints": [
                        "POST /restricciones/{id}/alimentos/{alimento_id} - Asociar alergia a alimento",
                        "GET /restricciones/{id}/alimentos - Ver alimentos con una restricción"
                    ]
                },
                {
                    "modelo_a": "Pedido",
                    "modelo_b": "Producto",
                    "tabla_intermedia": "PedidoProducto",
                    "explicacion": "Un pedido puede tener MUCHOS productos. Un producto puede estar en MUCHOS pedidos.",
                    "campos_extra": "cantidad, precio_unitario, subtotal",
                    "endpoints": [
                        "POST /pedidos/{id}/productos/{producto_id} - Agregar producto a pedido",
                        "GET /pedidos/{id}/detalle - Ver productos de un pedido"
                    ]
                }
            ]
        },
        "nota_importante": "Las tablas intermedias (RestriccionAlimento, LoncheraAlimento, PedidoProducto) NO necesitan routers independientes porque se gestionan a través de los endpoints de los modelos principales."
    }


@app.get("/modelos", tags=["Documentación"])
async def listar_modelos():
    """Lista todos los modelos del sistema con su estado de CRUD"""
    return {
        "total_modelos": 12,
        "modelos": [
            {"id": 1, "nombre": "Usuario", "crud": "✅ Completo", "endpoint": "/usuarios"},
            {"id": 2, "nombre": "Perfil", "crud": "✅ Completo", "endpoint": "/perfiles", "nuevo": True},
            {"id": 3, "nombre": "Lonchera", "crud": "✅ Completo + N:M", "endpoint": "/loncheras", "mejorado": True},
            {"id": 4, "nombre": "Alimento", "crud": "✅ Completo", "endpoint": "/alimentos"},
            {"id": 5, "nombre": "Restriccion", "crud": "✅ Completo", "endpoint": "/restricciones"},
            {"id": 6, "nombre": "RestriccionAlimento", "crud": "⚙️ Tabla N:M", "gestionado_desde": "/restricciones"},
            {"id": 7, "nombre": "LoncheraAlimento", "crud": "⚙️ Tabla N:M", "gestionado_desde": "/loncheras", "mejorado": True},
            {"id": 8, "nombre": "Producto", "crud": "✅ Completo", "endpoint": "/productos", "mejorado": True},
            {"id": 9, "nombre": "Pedido", "crud": "✅ Completo + N:M", "endpoint": "/pedidos"},
            {"id": 10, "nombre": "PedidoProducto", "crud": "⚙️ Tabla N:M", "gestionado_desde": "/pedidos"},
            {"id": 11, "nombre": "MovimientoInventario", "crud": "✅ Completo", "endpoint": "/inventario"},
            {"id": 12, "nombre": "HistorialEliminacion", "crud": "✅ Completo", "endpoint": "/historial"}
        ],
        "leyenda": {
            "✅ Completo": "Tiene todos los endpoints CRUD (CREATE, READ, UPDATE, DELETE)",
            "⚙️ Tabla N:M": "Tabla intermedia gestionada a través de otros endpoints",
            "nuevo": "Router agregado en v2.1.0",
            "mejorado": "Endpoints mejorados en v2.1.0"
        }
    }