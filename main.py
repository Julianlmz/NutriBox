from fastapi import FastAPI
from db import create_tables
import Usuario, Lonchera, Producto, Pedido, Reporte

app = FastAPI(title="NutriBox API")

@app.on_event("startup")
def on_startup():
    create_tables(app)

app.include_router(Usuario.router)
app.include_router(Lonchera.router)
app.include_router(Producto.router)
app.include_router(Pedido.router)
app.include_router(Reporte.router)
@app.get("/")
async def root():
    return {"message": "API de NutriBox funcionando"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hola {name}, bienvenido a NutriBox 👋"}
