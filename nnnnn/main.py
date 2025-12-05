from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import create_tables
import jugador
import partido
import estadistica

app = FastAPI(
    title="Sigmotoa FC API",
    description="Sistema de gestión de jugadores, partidos y estadísticas",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear tablas al iniciar
create_tables()

# Incluir routers
app.include_router(jugador.router)
app.include_router(partido.router)
app.include_router(estadistica.router)

@app.get("/")
async def root():
    return {
        "message": "Sigmotoa FC - Sistema de Gestión Deportiva",
        "version": "1.0.0",
        "endpoints": {
            "jugadores": "/jugador",
            "partidos": "/partido",
            "estadisticas": "/estadistica",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "API funcionando correctamente"}