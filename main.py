from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from starlette.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from Core.database import create_tables
from Modulos import Usuario, Alimento, Lonchera, Pedido, Restriccion
from Core import auth
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

create_tables()

app.include_router(auth.router)
app.include_router(Usuario.router)
app.include_router(Alimento.router)
app.include_router(Lonchera.router)
app.include_router(Restriccion.router)
app.include_router(Pedido.router)


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend_static")