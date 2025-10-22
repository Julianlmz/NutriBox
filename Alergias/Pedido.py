from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from typing import List, Optional
from Datos.models import Pedido, PedidoCreate, PedidoProducto, Producto, Usuario
from Aplicacion.db import SessionDep

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.post("/", response_model=Pedido, status_code=status.HTTP_201_CREATED)
async def crear_pedido(pedido_data: PedidoCreate, session: SessionDep):
    """Crea un nuevo pedido vacío"""
    # Verificar que el usuario existe
    usuario = session.get(Usuario, pedido_data.usuario_id)
    if not usuario or not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado o inactivo"
        )

    pedido = Pedido(**pedido_data.model_dump())
    session.add(pedido)
    session.commit()
    session.refresh(pedido)
    return pedido


@router.post("/{pedido_id}/productos/{producto_id}", status_code=status.HTTP_201_CREATED)
async def agregar_producto_a_pedido(
        pedido_id: int,
        producto_id: int,
        cantidad: int = 1,
        session: SessionDep = None
):
    """Agrega un producto a un pedido existente"""
    # Validar cantidad
    if cantidad < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cantidad debe ser mayor a 0"
        )

    # Verificar que existen pedido y producto
    pedido = session.get(Pedido, pedido_id)
    producto = session.get(Producto, producto_id)

    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )

    if not producto or not producto.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado o inactivo"
        )

    # Verificar stock disponible
    if producto.stock_actual < cantidad:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente. Disponible: {producto.stock_actual}"
        )

    # Verificar si el producto ya está en el pedido
    existing = session.exec(
        select(PedidoProducto).where(
            PedidoProducto.pedido_id == pedido_id,
            PedidoProducto.producto_id == producto_id
        )
    ).first()

    if existing:
        # Actualizar cantidad
        nueva_cantidad = existing.cantidad + cantidad
        if producto.stock_actual < nueva_cantidad:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente para la cantidad total ({nueva_cantidad})"
            )
        existing.cantidad = nueva_cantidad
        existing.subtotal = producto.precio * nueva_cantidad
        session.add(existing)
    else:
        # Crear nueva asociación
        subtotal = producto.precio * cantidad
        assoc = PedidoProducto(
            pedido_id=pedido_id,
            producto_id=producto_id,
            cantidad=cantidad,
            precio_unitario=producto.precio,
            subtotal=subtotal
        )
        session.add(assoc)

    # Actualizar total del pedido
    pedido.total = sum(
        pp.subtotal for pp in pedido.productos
    ) + (producto.precio * cantidad if not existing else 0)

    session.add(pedido)
    session.commit()

    return {
        "message": "Producto agregado al pedido",
        "pedido_id": pedido_id,
        "producto_id": producto_id,
        "cantidad": cantidad,
        "subtotal": producto.precio * cantidad,
        "total_pedido": pedido.total
    }


@router.delete("/{pedido_id}/productos/{producto_id}", status_code=status.HTTP_200_OK)
async def quitar_producto_de_pedido(
        pedido_id: int,
        producto_id: int,
        session: SessionDep
):
    """Quita un producto del pedido"""
    pedido = session.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )

    # Buscar la asociación
    assoc = session.exec(
        select(PedidoProducto).where(
            PedidoProducto.pedido_id == pedido_id,
            PedidoProducto.producto_id == producto_id
        )
    ).first()

    if not assoc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado en el pedido"
        )

    # Eliminar asociación
    session.delete(assoc)

    # Recalcular total del pedido
    pedido.total = sum(pp.subtotal for pp in pedido.productos if pp.producto_id != producto_id)
    session.add(pedido)
    session.commit()

    return {"message": "Producto eliminado del pedido"}


@router.get("/", response_model=List[Pedido])
async def listar_pedidos(
        session: SessionDep,
        usuario_id: Optional[int] = None,
        estado: Optional[str] = None
):
    """Lista todos los pedidos con filtros opcionales"""
    query = select(Pedido)

    if usuario_id:
        query = query.where(Pedido.usuario_id == usuario_id)

    if estado:
        query = query.where(Pedido.estado == estado)

    query = query.order_by(Pedido.fecha.desc())
    pedidos = session.exec(query).all()
    return pedidos


@router.get("/{pedido_id}", response_model=Pedido)
async def obtener_pedido(pedido_id: int, session: SessionDep):
    """Obtiene un pedido específico con sus productos"""
    pedido = session.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    return pedido


@router.get("/{pedido_id}/detalle")
async def obtener_detalle_pedido(pedido_id: int, session: SessionDep):
    """Obtiene el detalle completo de un pedido con información de productos"""
    pedido = session.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )

    productos_detalle = []
    for pp in pedido.productos:
        productos_detalle.append({
            "producto_id": pp.producto_id,
            "nombre": pp.producto.nombre,
            "descripcion": pp.producto.descripcion,
            "cantidad": pp.cantidad,
            "precio_unitario": pp.precio_unitario,
            "subtotal": pp.subtotal
        })

    return {
        "pedido_id": pedido.id,
        "usuario_id": pedido.usuario_id,
        "usuario_nombre": f"{pedido.usuario.nombre} {pedido.usuario.apellido}" if pedido.usuario else None,
        "fecha": pedido.fecha,
        "estado": pedido.estado,
        "productos": productos_detalle,
        "total": pedido.total
    }


@router.put("/{pedido_id}/estado", response_model=Pedido)
async def actualizar_estado_pedido(
        pedido_id: int,
        nuevo_estado: str,
        session: SessionDep
):
    """
    Actualiza el estado de un pedido.
    Estados válidos: Pendiente, Confirmado, Entregado, Cancelado
    """
    estados_validos = ["Pendiente", "Confirmado", "Entregado", "Cancelado"]

    if nuevo_estado not in estados_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estado inválido. Estados válidos: {', '.join(estados_validos)}"
        )

    pedido = session.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )

    pedido.estado = nuevo_estado
    session.add(pedido)
    session.commit()
    session.refresh(pedido)

    return pedido


@router.post("/{pedido_id}/confirmar", response_model=Pedido)
async def confirmar_pedido(pedido_id: int, session: SessionDep):
    """
    Confirma un pedido y descuenta el stock de los productos.
    Solo se puede confirmar un pedido en estado 'Pendiente'
    """
    pedido = session.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )

    if pedido.estado != "Pendiente":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Solo se pueden confirmar pedidos pendientes. Estado actual: {pedido.estado}"
        )

    # Verificar y descontar stock
    for pp in pedido.productos:
        producto = session.get(Producto, pp.producto_id)
        if producto.stock_actual < pp.cantidad:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock_actual}"
            )

        # Descontar stock
        producto.stock_actual -= pp.cantidad
        session.add(producto)

    # Cambiar estado
    pedido.estado = "Confirmado"
    session.add(pedido)
    session.commit()
    session.refresh(pedido)

    return pedido


@router.delete("/{pedido_id}", status_code=status.HTTP_200_OK)
async def cancelar_pedido(pedido_id: int, session: SessionDep):
    """Cancela un pedido (cambia estado a Cancelado)"""
    pedido = session.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )

    if pedido.estado == "Entregado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede cancelar un pedido ya entregado"
        )

    pedido.estado = "Cancelado"
    session.add(pedido)
    session.commit()

    return {"message": "Pedido cancelado exitosamente", "pedido_id": pedido_id}