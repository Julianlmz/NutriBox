from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from typing import List, Optional
from Datos.models import Producto, ProductoCreate
from Aplicacion.db import SessionDep

router = APIRouter(prefix="/productos", tags=["Productos"])


# ========================================
# RELACIÓN N:M - Producto ↔ Pedido
# Un producto puede estar en MUCHOS pedidos
# Un pedido puede tener MUCHOS productos
# Tabla intermedia: PedidoProducto
# (Se gestiona desde el router de Pedido)
# ========================================


@router.post("/", response_model=Producto, status_code=status.HTTP_201_CREATED)
async def crear_producto(producto: ProductoCreate, session: SessionDep):
    """
    Crea un nuevo producto.
    Los productos se pueden agregar a pedidos (RELACIÓN N:M).
    """
    nuevo_producto = Producto(**producto.model_dump())
    session.add(nuevo_producto)
    session.commit()
    session.refresh(nuevo_producto)
    return nuevo_producto


@router.get("/", response_model=List[Producto])
async def listar_productos(
        session: SessionDep,
        incluir_inactivos: bool = False,
        stock_bajo: bool = False,
        limite_stock: int = 10
):
    """
    Lista todos los productos con filtros opcionales.
    """
    query = select(Producto)

    if not incluir_inactivos:
        query = query.where(Producto.is_active == True)

    if stock_bajo:
        query = query.where(Producto.stock_actual < limite_stock)

    productos = session.exec(query).all()
    return productos


@router.get("/{producto_id}", response_model=Producto)
async def obtener_producto(producto_id: int, session: SessionDep):
    """Obtiene un producto por ID"""
    producto = session.get(Producto, producto_id)
    if not producto or not producto.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado o inactivo"
        )
    return producto


@router.put("/{producto_id}", response_model=Producto)
async def actualizar_producto(
        producto_id: int,
        data: ProductoCreate,
        session: SessionDep
):
    """
    Actualiza un producto existente.
    ✅ NUEVO: Endpoint PUT agregado para completar el CRUD.
    """
    producto = session.get(Producto, producto_id)
    if not producto or not producto.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado o inactivo"
        )

    # Actualizar campos
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(producto, key, value)

    session.add(producto)
    session.commit()
    session.refresh(producto)
    return producto


@router.patch("/{producto_id}/stock")
async def actualizar_stock(
        producto_id: int,
        cantidad: int,
        session: SessionDep
):
    """
    Actualiza el stock de un producto (suma o resta la cantidad).
    Útil para ajustes de inventario.
    """
    producto = session.get(Producto, producto_id)
    if not producto or not producto.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )

    nuevo_stock = producto.stock_actual + cantidad
    if nuevo_stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente. Stock actual: {producto.stock_actual}"
        )

    producto.stock_actual = nuevo_stock
    session.add(producto)
    session.commit()
    session.refresh(producto)

    return {
        "producto_id": producto_id,
        "stock_anterior": producto.stock_actual - cantidad,
        "ajuste": cantidad,
        "stock_nuevo": producto.stock_actual
    }


@router.delete("/{producto_id}", status_code=status.HTTP_200_OK)
async def eliminar_producto(
        producto_id: int,
        session: SessionDep,
        hard_delete: bool = False
):
    """
    Elimina un producto (soft delete por defecto).
    ✅ NUEVO: Endpoint DELETE agregado para completar el CRUD.

    - hard_delete=False: Desactiva el producto (soft delete) - RECOMENDADO
    - hard_delete=True: Elimina físicamente el registro

    NOTA: Los productos con pedidos asociados NO se pueden eliminar físicamente.
    """
    producto = session.get(Producto, producto_id)
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )

    if hard_delete:
        # Verificar si tiene pedidos asociados (RELACIÓN N:M)
        if len(producto.pedidos) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede eliminar. El producto tiene {len(producto.pedidos)} pedidos asociados. Use soft delete."
            )
        session.delete(producto)
        mensaje = "Producto eliminado permanentemente"
    else:
        # Soft delete - solo desactivar
        producto.is_active = False
        session.add(producto)
        mensaje = "Producto desactivado correctamente"

    session.commit()
    return {"message": mensaje, "id": producto_id}


@router.post("/{producto_id}/reactivar", response_model=Producto)
async def reactivar_producto(producto_id: int, session: SessionDep):
    """Reactiva un producto previamente desactivado"""
    producto = session.get(Producto, producto_id)
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )

    producto.is_active = True
    session.add(producto)
    session.commit()
    session.refresh(producto)
    return producto


@router.get("/{producto_id}/pedidos")
async def obtener_pedidos_producto(producto_id: int, session: SessionDep):
    """
    Obtiene todos los pedidos que contienen este producto.
    Muestra la RELACIÓN N:M entre Producto y Pedido.
    """
    producto = session.get(Producto, producto_id)
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )

    pedidos_info = []
    for pp in producto.pedidos:
        pedidos_info.append({
            "pedido_id": pp.pedido_id,
            "cantidad": pp.cantidad,
            "precio_unitario": pp.precio_unitario,
            "subtotal": pp.subtotal,
            "fecha_pedido": pp.pedido.fecha,
            "estado_pedido": pp.pedido.estado,
            "usuario": {
                "id": pp.pedido.usuario.id,
                "nombre": f"{pp.pedido.usuario.nombre} {pp.pedido.usuario.apellido}"
            }
        })

    return {
        "producto_id": producto_id,
        "nombre_producto": producto.nombre,
        "total_pedidos": len(pedidos_info),
        "pedidos": pedidos_info
    }


@router.get("/estadisticas/resumen")
async def estadisticas_productos(session: SessionDep):
    """Genera estadísticas generales de productos"""
    productos = session.exec(
        select(Producto).where(Producto.is_active == True)
    ).all()

    total_productos = len(productos)
    valor_inventario = sum(p.precio * p.stock_actual for p in productos)
    sin_stock = sum(1 for p in productos if p.stock_actual == 0)
    stock_bajo = sum(1 for p in productos if 0 < p.stock_actual < 10)

    return {
        "total_productos_activos": total_productos,
        "valor_total_inventario": round(valor_inventario, 2),
        "productos_sin_stock": sin_stock,
        "productos_stock_bajo": stock_bajo,
        "precio_promedio": round(sum(p.precio for p in productos) / total_productos, 2) if total_productos > 0 else 0
    }