from fastapi import FastAPI
from Aplicacion.database import create_tables
from Datos import Usuario, Alimento, Lonchera, Restriccion, Pedido
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="NutriBox API",
    description="Sistema de gestión de loncheras saludables con control de alergias y restricciones alimentarias",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#create_tables()

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