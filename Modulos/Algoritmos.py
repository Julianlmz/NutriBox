from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

# Prefijo para todas las rutas de algoritmos
router = APIRouter(prefix="/algoritmos", tags=["Algoritmos"])

# Configuramos la carpeta de templates
templates = Jinja2Templates(directory="Templates")

# 1. Ruta para NutriSort
@router.get("/nutrisort")
async def ver_nutrisort(request: Request):
    return templates.TemplateResponse("Algoritmos/nutrisort.html", {"request": request})

# 2. Ruta para NutriCost
@router.get("/nutricost")
async def ver_nutricost(request: Request):
    return templates.TemplateResponse("Algoritmos/nutricost.html", {"request": request})

# 3. Ruta para Sugeridor
@router.get("/sugeridor")
async def ver_sugeridor(request: Request):
    return templates.TemplateResponse("Algoritmos/sugeridor.html", {"request": request})

# 4. Ruta para NutriBucket
@router.get("/nutribucket")
async def ver_nutribucket(request: Request):
    return templates.TemplateResponse("Algoritmos/nutribucket.html", {"request": request})

# 5. Ruta para NutriTop (¡ESTA ES LA QUE TE FALTA!)
@router.get("/nutritop")
async def ver_nutritop(request: Request):
    return templates.TemplateResponse("Algoritmos/nutritop.html", {"request": request})