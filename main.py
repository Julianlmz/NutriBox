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
from Datos import Alimento as AlimentoRouter
from Datos import Restriccion as RestriccionRouter
from Alergias import Producto as ProductoRouter
from Alergias import Pedido as PedidoRouter
from Alergias import Inventario as InventarioRouter
from Alergias import Historial as HistorialRouter
from Alergias import Reporte as ReporteRouter

app = FastAPI(
    title="NutriBox API",
    description="API para gestión de loncheras saludables",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """Crea las tablas al iniciar la aplicación"""
    create_tables(app)
    print("✅ Base de datos inicializada")

# Incluir todos los routers
app.include_router(UsuarioRouter.router)
app.include_router(LoncheraRouter.router)
app.include_router(AlimentoRouter.router)
app.include_router(RestriccionRouter.router)
app.include_router(ProductoRouter.router)
app.include_router(PedidoRouter.router)
app.include_router(InventarioRouter.router)
app.include_router(HistorialRouter.router)
app.include_router(ReporteRouter.router)

@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz de la API"""
    return {
        "message": "API de NutriBox funcionando",
        "version": "2.0.0",
        "endpoints": {
            "usuarios": "/usuarios",
            "loncheras": "/loncheras",
            "productos": "/productos",
            "pedidos": "/pedidos",
            "alimentos": "/alimentos",
            "restricciones": "/restricciones",
            "inventario": "/inventario",
            "historial": "/historial",
            "reportes": "/reportes",
            "docs": "/docs"
        }
    }

@app.get("/hello/{name}", tags=["Root"])
async def say_hello(name: str):
    """Saludo personalizado"""
    return {"message": f"Hola {name}, bienvenido a NutriBox 👋"}

@app.get("/health", tags=["Health"])
async def health_check():
    """Verifica el estado de la API"""
    return {
        "status": "healthy",
        "service": "NutriBox API",
        "version": "2.0.0"
    }
