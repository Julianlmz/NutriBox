import io
import pandas as pd
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlmodel import select
from Aplicacion.database import SessionDep
from Datos.models import Usuario, Lonchera

router = APIRouter(prefix="/reportes", tags=["Reportes"])

@router.get("/usuarios_csv")
async def usuarios_con_loncheras_csv(session: SessionDep):
    usuarios = session.exec(select(Usuario).where(Usuario.is_active==True)).all()
    rows = []
    for u in usuarios:
        loncheras = session.exec(select(Lonchera).where(Lonchera.usuario_id==u.id, Lonchera.is_active==True)).all()
        if loncheras:
            for l in loncheras:
                rows.append({
                    "usuario_id": u.id,
                    "nombre_usuario": f"{u.nombre} {u.apellido}",
                    "cedula": u.cedula,
                    "lonchera_id": l.id,
                    "lonchera_nombre": l.nombre,
                    "lonchera_descripcion": l.descripcion,
                    "lonchera_precio": l.precio,
                    "lonchera_calorias": l.calorias,
                    "fecha_creacion": l.fecha_creacion
                })
        else:
            rows.append({
                "usuario_id": u.id,
                "nombre_usuario": f"{u.nombre} {u.apellido}",
                "cedula": u.cedula,
                "lonchera_id": None,
                "lonchera_nombre": None,
                "lonchera_descripcion": None,
                "lonchera_precio": None,
                "lonchera_calorias": None,
                "fecha_creacion": None
            })
    df = pd.DataFrame(rows)
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)
    headers = {"Content-Disposition": "attachment; filename=usuarios_loncheras.csv"}
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers=headers)
