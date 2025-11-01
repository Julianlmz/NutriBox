from fastapi import FastAPI
from Aplicacion.database import create_tables
from Datos import Usuario, Alimento, Lonchera, Restriccion, Pedido

app = FastAPI(
    title="NutriBox API",
    description="Sistema de gestión de loncheras saludables con control de alergias y restricciones alimentarias",
)

create_tables()

app.include_router(Usuario.router)
app.include_router(Alimento.router)
app.include_router(Lonchera.router)
app.include_router(Restriccion.router)
app.include_router(Pedido.router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Bienvenido a NutriBox API",
        "docs": "/docs",
        "redoc": "/redoc"
    }