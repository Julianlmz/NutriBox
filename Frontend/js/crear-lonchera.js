const API_URL = 'http://127.0.0.1:8000';

let hijoSeleccionado = null;
let restriccionesHijo = [];
let alimentosDisponibles = [];
let alimentosEnLonchera = [];

document.addEventListener('DOMContentLoaded', () => {
    cargarHijos();
    cargarDirecciones();
    cargarAlimentos();
});

// --- CARGAR HIJOS ---
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

// --- CARGAR DIRECCIONES ---
async function cargarDirecciones() {
    try {
        const token = localStorage.getItem('access_token');
        const userId = localStorage.getItem('user_id');

        if (!userId) {
            console.error("No se encontró el ID de usuario");
            return;
        }

        const response = await fetch(`${API_URL}/direcciones/?usuario_id=${userId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        const select = document.getElementById('select-direccion');

        if (response.ok) {
            const direcciones = await response.json();

            if (direcciones.length === 0) {
                select.innerHTML = '<option value="">Sin direcciones registradas</option>';
                Swal.fire({
                    icon: 'warning',
                    title: 'Faltan datos',
                    text: 'Debes registrar al menos una dirección antes de crear una lonchera.',
                    confirmButtonText: 'Ir a Direcciones',
                    showCancelButton: true
                }).then((result) => {
                    if (result.isConfirmed) window.location.href = 'direcciones.html';
                });
                return;
            }

            select.innerHTML = '<option value="">Selecciona una dirección</option>';
            direcciones.forEach(dir => {
                const option = document.createElement('option');
                option.value = dir.id;
                const principalTexto = dir.principal ? ' (Principal)' : '';
                option.textContent = `${dir.nombre || 'Casa'} - ${dir.direccion}${principalTexto}`;
                select.appendChild(option);
            });

        } else {
            console.error("Error backend:", await response.text());
            select.innerHTML = '<option value="">Error al cargar</option>';
        }
    } catch (error) {
        console.error('Error direcciones:', error);
        const select = document.getElementById('select-direccion');
        if(select) select.innerHTML = '<option value="">Error de conexión</option>';
    }
}

// --- CARGAR RESTRICCIONES ---
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

// --- CARGAR ALIMENTOS ---
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

function tieneRestriccion(alimento) {
    return false; // Lógica visual de restricción
}

// --- RENDERIZAR ALIMENTOS ---
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

// --- FUNCIONES GLOBALES ---
window.agregarAlimento = function(alimentoId) {
    const alimento = alimentosDisponibles.find(a => a.id === alimentoId);
    if (!alimento) return;

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

    // Se ejecutan en orden: Calcular -> Renderizar lista -> Renderizar botones
    actualizarResumen();
    renderizarAlimentosLonchera();
    renderizarAlimentos();

    const Toast = Swal.mixin({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 1500,
        timerProgressBar: true
    });
    Toast.fire({ icon: 'success', title: 'Agregado' });
}

window.eliminarAlimento = function(alimentoId) {
    alimentosEnLonchera = alimentosEnLonchera.filter(a => a.id !== alimentoId);
    actualizarResumen();
    renderizarAlimentosLonchera();
    renderizarAlimentos();
}

// --- RENDERIZAR LISTA LATERAL ---
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

// --- CORRECCIÓN AQUÍ: Se agregaron los cálculos faltantes ---
function actualizarResumen() {
    const totalAlimentos = alimentosEnLonchera.length;
    // Estas líneas faltaban y causaban el error:
    const totalCalorias = alimentosEnLonchera.reduce((sum, a) => sum + a.calorias, 0);
    const totalPrecio = alimentosEnLonchera.reduce((sum, a) => sum + a.precio, 0);

    document.getElementById('total-alimentos').textContent = totalAlimentos;
    document.getElementById('total-calorias').textContent = totalCalorias;
    document.getElementById('total-precio').textContent = totalPrecio.toFixed(2);
}

// --- CREAR LONCHERA (FINAL) ---
window.crearLonchera = async function() {
    try {
        if (!hijoSeleccionado) {
            Swal.fire('Error', 'Debes seleccionar un hijo', 'error');
            return;
        }

        const selectDireccion = document.getElementById('select-direccion');
        const direccionId = selectDireccion.value;
        if (!direccionId) {
            Swal.fire('Error', 'Debes seleccionar una dirección de entrega', 'warning');
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
        const userId = localStorage.getItem('user_id');

        const dataLonchera = {
            nombre: nombreLonchera,
            descripcion: `Lonchera para ${document.getElementById('select-hijo').selectedOptions[0].text}`,
            calorias: 0,
            precio: 0,
            usuario_id: parseInt(userId),
            direccion_id: parseInt(direccionId)
        };

        const responseLonchera = await fetch(`${API_URL}/loncheras`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dataLonchera)
        });

        if (!responseLonchera.ok) {
            const errorData = await responseLonchera.json();
            throw new Error(errorData.detail || 'Error al crear lonchera');
        }

        const loncheraCreada = await responseLonchera.json();

        for (const alimento of alimentosEnLonchera) {
            await fetch(`${API_URL}/loncheras/${loncheraCreada.id}/alimentos`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    alimento_id: alimento.id,
                    cantidad_gramos: alimento.cantidad
                })
            });
        }

        Swal.close();
        Swal.fire({
            icon: 'success',
            title: '¡Lonchera creada!',
            text: 'Tu pedido ha sido registrado con éxito.',
            confirmButtonColor: '#4CAF50'
        }).then(() => {
            window.location.href = 'loncheras.html';
        });

    } catch (error) {
        Swal.close();
        console.error('Error:', error);
        Swal.fire('Error', error.message || 'No se pudo crear la lonchera', 'error');
    }
}