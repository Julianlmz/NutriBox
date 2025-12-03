// crear-lonchera.js
const API_URL = 'http://127.0.0.1:8000';

let hijoSeleccionado = null;
let restriccionesHijo = [];
let alimentosDisponibles = [];
let alimentosEnLonchera = [];

document.addEventListener('DOMContentLoaded', () => {
    cargarHijos();
    cargarAlimentos();
});

// Cargar hijos
async function cargarHijos() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL}/hijo/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const hijos = await response.json();
            const select = document.getElementById('select-hijo');
            select.innerHTML = '<option value="">Selecciona un hijo</option>';

            hijos.forEach(hijo => {
                const option = document.createElement('option');
                option.value = hijo.id;
                option.textContent = `${hijo.nombre} ${hijo.apellido || ''}`.trim();
                select.appendChild(option);
            });

            select.addEventListener('change', async (e) => {
                hijoSeleccionado = e.target.value;
                if (hijoSeleccionado) {
                    await cargarRestriccionesHijo(hijoSeleccionado);
                    renderizarAlimentos();
                } else {
                    restriccionesHijo = [];
                    renderizarAlimentos();
                }
            });
        }
    } catch (error) {
        console.error('Error al cargar hijos:', error);
    }
}

// Cargar restricciones del hijo
async function cargarRestriccionesHijo(hijoId) {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL}/hijo/${hijoId}/restricciones`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            restriccionesHijo = await response.json();
            console.log('Restricciones del hijo:', restriccionesHijo);
        } else {
            restriccionesHijo = [];
        }
    } catch (error) {
        console.error('Error al cargar restricciones:', error);
        restriccionesHijo = [];
    }
}

// Cargar todos los alimentos
async function cargarAlimentos() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL}/alimento/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            alimentosDisponibles = await response.json();
            renderizarAlimentos();
        }
    } catch (error) {
        console.error('Error al cargar alimentos:', error);
        document.getElementById('lista-alimentos').innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Error al cargar alimentos</p>
            </div>
        `;
    }
}

// Verificar si un alimento tiene restricciones para el hijo
function tieneRestriccion(alimento) {
    // Aquí deberías verificar si el alimento está asociado a alguna restricción del hijo
    // Por ahora retornamos false, pero deberías implementar el endpoint para obtener
    // los alimentos asociados a cada restricción
    return false;
}

// Renderizar lista de alimentos
function renderizarAlimentos() {
    const container = document.getElementById('lista-alimentos');

    if (alimentosDisponibles.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-box-open"></i>
                <p>No hay alimentos disponibles. <a href="alimentos.html">Crear alimento</a></p>
            </div>
        `;
        return;
    }

    container.innerHTML = alimentosDisponibles.map(alimento => {
        const tieneRestr = tieneRestriccion(alimento);
        const yaAgregado = alimentosEnLonchera.some(a => a.id === alimento.id);
        const deshabilitado = tieneRestr || yaAgregado;

        return `
            <div class="alimento-card ${deshabilitado ? 'disabled' : ''}" data-id="${alimento.id}">
                <div class="d-flex align-items-center">
                    <img src="${alimento.imagen_url || 'https://via.placeholder.com/80'}" alt="${alimento.nombre}" class="alimento-img">
                    <div class="flex-grow-1 alimento-info">
                        <h5>${alimento.nombre}</h5>
                        <div class="mb-2">
                            <span class="alimento-badge badge-categoria">${alimento.categoria}</span>
                            <span class="alimento-badge badge-calorias">${alimento.calorias_por_100g} cal/100g</span>
                            <span class="alimento-badge badge-precio">$${alimento.precio_unitario}</span>
                            ${tieneRestr ? '<span class="alimento-badge badge-restriccion"><i class="fas fa-exclamation-triangle"></i> Restricción</span>' : ''}
                        </div>
                        <p>Stock: ${alimento.stock_actual} unidades</p>
                    </div>
                    <div class="alimento-actions">
                        <button class="btn-add-alimento" onclick="agregarAlimento(${alimento.id})" ${deshabilitado ? 'disabled' : ''}>
                            <i class="fas fa-plus me-1"></i> ${yaAgregado ? 'Agregado' : 'Agregar'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Agregar alimento a la lonchera
function agregarAlimento(alimentoId) {
    const alimento = alimentosDisponibles.find(a => a.id === alimentoId);
    if (!alimento) return;

    // Agregar directamente 1 unidad (100g por defecto)
    const cantidad = 100; // gramos por defecto
    const factor = cantidad / 100;
    const calorias = Math.round(alimento.calorias_por_100g * factor);
    const precio = alimento.precio_unitario;

    alimentosEnLonchera.push({
        id: alimento.id,
        nombre: alimento.nombre,
        cantidad: cantidad,
        calorias: calorias,
        precio: precio,
        imagen_url: alimento.imagen_url
    });

    actualizarResumen();
    renderizarAlimentosLonchera();
    renderizarAlimentos();

    Swal.fire({
        icon: 'success',
        title: '¡Agregado!',
        text: `${alimento.nombre} agregado a la lonchera`,
        timer: 1000,
        showConfirmButton: false
    });
}

// Eliminar alimento de la lonchera
function eliminarAlimento(alimentoId) {
    alimentosEnLonchera = alimentosEnLonchera.filter(a => a.id !== alimentoId);
    actualizarResumen();
    renderizarAlimentosLonchera();
    renderizarAlimentos();
}

// Renderizar alimentos en la lonchera
function renderizarAlimentosLonchera() {
    const container = document.getElementById('alimentos-lonchera');

    if (alimentosEnLonchera.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-box-open"></i>
                <p>Aún no has agregado alimentos</p>
            </div>
        `;
        return;
    }

    container.innerHTML = alimentosEnLonchera.map(alimento => `
        <div class="alimento-lonchera">
            <div>
                <strong>${alimento.nombre}</strong>
                <div style="font-size: 0.85rem; color: #7f8c8d;">
                    ${alimento.cantidad}g • ${alimento.calorias} cal • $${alimento.precio}
                </div>
            </div>
            <button class="btn-remove" onclick="eliminarAlimento(${alimento.id})">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `).join('');
}

// Actualizar resumen
function actualizarResumen() {
    const totalAlimentos = alimentosEnLonchera.length;
    const totalCalorias = alimentosEnLonchera.reduce((sum, a) => sum + a.calorias, 0);
    const totalPrecio = alimentosEnLonchera.reduce((sum, a) => sum + a.precio, 0);

    document.getElementById('total-alimentos').textContent = totalAlimentos;
    document.getElementById('total-calorias').textContent = totalCalorias;
    document.getElementById('total-precio').textContent = totalPrecio.toFixed(2);
}

// Crear lonchera
async function crearLonchera() {
    try {
        // Validaciones
        if (!hijoSeleccionado) {
            Swal.fire('Error', 'Debes seleccionar un hijo', 'error');
            return;
        }

        const nombreLonchera = document.getElementById('nombre-lonchera').value.trim();
        if (!nombreLonchera) {
            Swal.fire('Error', 'Debes ingresar un nombre para la lonchera', 'error');
            return;
        }

        if (alimentosEnLonchera.length === 0) {
            Swal.fire('Error', 'Debes agregar al menos un alimento', 'error');
            return;
        }

        Swal.fire({
            title: 'Creando lonchera...',
            allowOutsideClick: false,
            didOpen: () => Swal.showLoading()
        });

        const token = localStorage.getItem('access_token');

        // Obtener el usuario autenticado (padre)
        const userResponse = await fetch(`${API_URL}/usuario/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!userResponse.ok) {
            throw new Error('No se pudo obtener usuario autenticado');
        }

        const currentUser = await userResponse.json();
        console.log('Usuario autenticado:', currentUser);

        // Calcular totales
        const totalCalorias = alimentosEnLonchera.reduce((sum, a) => sum + a.calorias, 0);
        const totalPrecio = alimentosEnLonchera.reduce((sum, a) => sum + a.precio, 0);

        // 1. Crear lonchera con el ID del PADRE autenticado
        const dataLonchera = {
            nombre: nombreLonchera,
            descripcion: `Lonchera para ${document.getElementById('select-hijo').selectedOptions[0].text}`,
            calorias: totalCalorias,
            precio: parseFloat(totalPrecio.toFixed(2)),
            usuario_id: currentUser.id  // ID del PADRE, no del hijo
        };

        console.log('Datos de lonchera a crear:', dataLonchera);

        const responseLonchera = await fetch(`${API_URL}/lonchera/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dataLonchera)
        });

        console.log('Response status:', responseLonchera.status);
        console.log('Response ok:', responseLonchera.ok);

        if (!responseLonchera.ok) {
            const errorData = await responseLonchera.json();
            console.error('Error al crear:', errorData);
            throw new Error(errorData.detail || 'Error al crear lonchera');
        }

        const loncheraCreada = await responseLonchera.json();
        console.log('Lonchera creada:', loncheraCreada);

        // 2. Agregar alimentos a la lonchera
        for (const alimento of alimentosEnLonchera) {
            const dataAlimento = {
                alimento_id: alimento.id,
                cantidad_gramos: alimento.cantidad
            };

            await fetch(`${API_URL}/lonchera/${loncheraCreada.id}/alimento`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(dataAlimento)
            });
        }

        Swal.close();

        Swal.fire({
            icon: 'success',
            title: '¡Lonchera creada!',
            text: 'La lonchera se ha creado exitosamente',
            confirmButtonColor: '#4CAF50'
        }).then(() => {
            window.location.href = 'loncheras.html';
        });

    } catch (error) {
        Swal.close();
        console.error('Error:', error);
        Swal.fire('Error', 'No se pudo crear la lonchera', 'error');
    }
}