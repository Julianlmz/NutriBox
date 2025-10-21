from fastapi import FastAPI
from db import create_tables
import Usuario, Lonchera

app = FastAPI(title="NutriBox API")

@app.on_event("startup")
def on_startup():
    create_tables(app)

app.include_router(Usuario.router, tags=["Usuarios"], prefix="/usuarios")
app.include_router(Lonchera.router)
@app.get("/")
async def root():
    return {"message": "API de NutriBox funcionando"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hola {name}, bienvenido a NutriBox 👋"}
