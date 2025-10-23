from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from typing import List
from Datos.models import Restriccion, RestriccionCreate, RestriccionAlimento, Alimento
from Aplicacion.db import SessionDep

router = APIRouter(prefix="/restricciones", tags=["Restricciones y Alergias"])


@router.post("/", response_model=Restriccion, status_code=status.HTTP_201_CREATED)
async def crear_restriccion(data: RestriccionCreate, session: SessionDep):
    restriccion = Restriccion(**data.model_dump())
    session.add(restriccion)
    try:
        session.commit()
        session.refresh(restriccion)
        return restriccion
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear restricción: {str(e)}"
        )


@router.get("/", response_model=List[Restriccion])
async def listar_restricciones(session: SessionDep):
    restricciones = session.exec(select(Restriccion)).all()
    return restricciones


@router.get("/{restriccion_id}", response_model=Restriccion)
async def obtener_restriccion(restriccion_id: int, session: SessionDep):
    restriccion = session.get(Restriccion, restriccion_id)
    if not restriccion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restricción no encontrada"
        )
    return restriccion


@router.post("/{restriccion_id}/alimentos/{alimento_id}", status_code=status.HTTP_201_CREATED)
async def asociar_alimento_restriccion(
        restriccion_id: int,
        alimento_id: int,
        session: SessionDep
):
    restriccion = session.get(Restriccion, restriccion_id)
    alimento = session.get(Alimento, alimento_id)

    if not restriccion or not alimento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restricción o Alimento no encontrado"
        )

    existe = session.exec(
        select(RestriccionAlimento).where(
            RestriccionAlimento.restriccion_id == restriccion_id,
            RestriccionAlimento.alimento_id == alimento_id
        )
    ).first()

    if existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta asociación ya existe"
        )

    asociacion = RestriccionAlimento(
        restriccion_id=restriccion_id,
        alimento_id=alimento_id
    )
    session.add(asociacion)
    session.commit()
    return {"message": "Alimento asociado a restricción exitosamente"}


@router.delete("/{restriccion_id}/alimentos/{alimento_id}", status_code=status.HTTP_200_OK)
async def desasociar_alimento_restriccion(
        restriccion_id: int,
        alimento_id: int,
        session: SessionDep
):
    asociacion = session.exec(
        select(RestriccionAlimento).where(
            RestriccionAlimento.restriccion_id == restriccion_id,
            RestriccionAlimento.alimento_id == alimento_id
        )
    ).first()

    if not asociacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asociación no encontrada"
        )

    session.delete(asociacion)
    session.commit()
    return {"message": "Asociación eliminada exitosamente"}


@router.get("/{restriccion_id}/alimentos")
async def listar_alimentos_con_restriccion(restriccion_id: int, session: SessionDep):
    restriccion = session.get(Restriccion, restriccion_id)
    if not restriccion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restricción no encontrada"
        )

    return [
        {
            "id": a.alimento.id,
            "nombre": a.alimento.nombre,
            "categoria": a.alimento.categoria,
            "fecha_asociacion": a.fecha_asociacion
        }
        for a in restriccion.alimentos
    ]


@router.delete("/{restriccion_id}", status_code=status.HTTP_200_OK)
async def eliminar_restriccion(restriccion_id: int, session: SessionDep):
    restriccion = session.get(Restriccion, restriccion_id)
    if not restriccion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restricción no encontrada"
        )

    session.delete(restriccion)
    session.commit()
    return {"message": "Restricción eliminada exitosamente"}