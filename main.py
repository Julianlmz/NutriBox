from dotenv import load_dotenv
load_dotenv()
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from Core.database import create_tables
from Modulos import Usuario, Alimento, Lonchera, Pedido, Restriccion, Algoritmos, Hijo
from Servicios import Historial, Direccion
from Core import auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando base de datos...")
    await create_tables()
    yield
    print("Apagando aplicación...")

app = FastAPI(
    title="NutriBox API",
    description="Sistema de gestión de loncheras",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="Frontend"), name="static")

templates = Jinja2Templates(directory="Templates")

app.include_router(auth.router)
app.include_router(Usuario.router)
app.include_router(Alimento.router)
app.include_router(Lonchera.router)
app.include_router(Restriccion.router)
app.include_router(Pedido.router)
app.include_router(Algoritmos.router)
app.include_router(Hijo.router)
app.include_router(Historial.router)
app.include_router(Direccion.router)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/{page_name}.html", response_class=HTMLResponse)
async def render_page(request: Request, page_name: str):
    return templates.TemplateResponse(f"{page_name}.html", {"request": request})