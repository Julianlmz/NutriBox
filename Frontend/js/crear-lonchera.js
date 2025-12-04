const API_URL = '';

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
        const response = await fetch(`${API_URL}/hijo/`, { headers: { 'Authorization': `Bearer ${token}` } });
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
    } catch (error) { console.error('Error al cargar hijos:', error); }
}

// --- CARGAR DIRECCIONES ---
async function cargarDirecciones() {
    try {
        const token = localStorage.getItem('access_token');
        const userId = localStorage.getItem('user_id');
        if (!userId) return;
        const response = await fetch(`${API_URL}/direcciones/?usuario_id=${userId}`, { headers: { 'Authorization': `Bearer ${token}` } });
        const select = document.getElementById('select-direccion');
        if (response.ok) {
            const direcciones = await response.json();
            if (direcciones.length === 0) {
                select.innerHTML = '<option value="">Sin direcciones</option>';
                return;
            }
            select.innerHTML = '<option value="">Selecciona una dirección</option>';
            direcciones.forEach(dir => {
                const option = document.createElement('option');
                option.value = dir.id;
                option.textContent = `${dir.nombre || 'Casa'} - ${dir.direccion}`;
                select.appendChild(option);
            });
        }
    } catch (error) { console.error('Error direcciones:', error); }
}

// --- CARGAR RESTRICCIONES ---
async function cargarRestriccionesHijo(hijoId) {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL}/hijo/${hijoId}/restricciones`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (response.ok) {
            restriccionesHijo = await response.json();
            console.log('⚠️ Restricciones del Hijo (IDs):', restriccionesHijo.map(r => r.id));
        } else {
            restriccionesHijo = [];
        }
    } catch (error) { console.error('Error restricciones:', error); restriccionesHijo = []; }
}

// --- CARGAR ALIMENTOS ---
async function cargarAlimentos() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL}/alimento/`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (response.ok) {
            alimentosDisponibles = await response.json();
            console.log('🍎 Alimentos cargados:', alimentosDisponibles.length);
            renderizarAlimentos();
        }
    } catch (error) { console.error('Error alimentos:', error); }
}

// --- VALIDAR RESTRICCIÓN ---
function tieneRestriccion(alimento) {
    if (!hijoSeleccionado || !restriccionesHijo || restriccionesHijo.length === 0) return false;

    // DEBUG: Ver si el alimento trae restricciones
    if (alimento.restricciones && alimento.restricciones.length > 0) {
        // console.log(`Revisando ${alimento.nombre}:`, alimento.restricciones);
    }

    if (!alimento.restricciones || alimento.restricciones.length === 0) return false;

    // IDs de restricciones del hijo
    const idsHijo = restriccionesHijo.map(r => r.id);

    // Verificar coincidencia
    const esAlergico = alimento.restricciones.some(r => idsHijo.includes(r.restriccion_id));

    if (esAlergico) {
        console.log(`🚫 ALERTA: ${alimento.nombre} tiene restricción conflictiva para el hijo.`);
    }

    return esAlergico;
}

// --- RENDERIZAR ALIMENTOS ---
function renderizarAlimentos() {
    const container = document.getElementById('lista-alimentos');
    if (alimentosDisponibles.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No hay alimentos.</p></div>';
        return;
    }

    container.innerHTML = alimentosDisponibles.map(alimento => {
        const restringido = tieneRestriccion(alimento);
        const yaAgregado = alimentosEnLonchera.some(a => a.id === alimento.id);
        const deshabilitado = restringido || yaAgregado;

        let cardClass = 'alimento-card';
        let badgeHTML = '';
        let btnTexto = yaAgregado ? 'Agregado' : 'Agregar';
        let btnClass = 'btn-primary-nb';
        let btnIcon = 'fa-plus';

        if (restringido) {
            cardClass += ' border-danger bg-danger-subtle';
            badgeHTML = `<span class="badge bg-danger text-white ms-1"><i class="fas fa-ban me-1"></i>Alergia</span>`;
            btnTexto = 'Prohibido';
            btnClass = 'btn-outline-danger';
            btnIcon = 'fa-ban';
        } else if (yaAgregado) {
            cardClass += ' disabled';
            btnClass = 'btn-secondary';
            btnIcon = 'fa-check';
        }

        return `
            <div class="${cardClass}" data-id="${alimento.id}" style="${restringido ? 'opacity: 0.8;' : ''}">
                <div class="d-flex align-items-center p-2">
                    <img src="${alimento.imagen_url || 'https://via.placeholder.com/80'}" alt="${alimento.nombre}" class="alimento-img">
                    <div class="flex-grow-1 alimento-info">
                        <div class="d-flex align-items-center mb-1">
                            <h5 class="mb-0 me-2 ${restringido ? 'text-danger' : ''}">${alimento.nombre}</h5>
                            ${badgeHTML}
                        </div>
                        <div class="mb-1">
                            <span class="badge bg-light text-dark border">${alimento.categoria}</span>
                            <span class="badge bg-success-subtle text-success">$${alimento.precio_unitario}</span>
                        </div>
                        <small class="text-muted">${alimento.calorias_por_100g} kcal / 100g</small>
                    </div>
                    <div class="alimento-actions">
                        <button class="btn btn-sm ${btnClass}" 
                                onclick="agregarAlimento(${alimento.id})" 
                                ${deshabilitado ? 'disabled' : ''}>
                            <i class="fas ${btnIcon} me-1"></i> ${btnTexto}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// --- AGREGAR ---
window.agregarAlimento = function(alimentoId) {
    const alimento = alimentosDisponibles.find(a => a.id === alimentoId);
    if (!alimento) return;

    if (tieneRestriccion(alimento)) {
        Swal.fire('¡Cuidado!', 'Este alimento contiene alérgenos peligrosos para tu hijo.', 'error');
        return;
    }

    const cantidad = 100;
    const factor = cantidad / 100;
    const calorias = Math.round(alimento.calorias_por_100g * factor);

    alimentosEnLonchera.push({
        id: alimento.id,
        nombre: alimento.nombre,
        cantidad: cantidad,
        calorias: calorias,
        precio: alimento.precio_unitario,
        imagen_url: alimento.imagen_url
    });

    actualizarResumen();
    renderizarAlimentosLonchera();
    renderizarAlimentos();

    const Toast = Swal.mixin({ toast: true, position: 'top-end', showConfirmButton: false, timer: 1500, timerProgressBar: true });
    Toast.fire({ icon: 'success', title: 'Agregado' });
}

window.eliminarAlimento = function(alimentoId) {
    alimentosEnLonchera = alimentosEnLonchera.filter(a => a.id !== alimentoId);
    actualizarResumen();
    renderizarAlimentosLonchera();
    renderizarAlimentos();
}

function renderizarAlimentosLonchera() {
    const container = document.getElementById('alimentos-lonchera');
    if (alimentosEnLonchera.length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-box-open"></i><p>Aún no has agregado alimentos</p></div>';
        return;
    }
    container.innerHTML = alimentosEnLonchera.map(alimento => `
        <div class="alimento-lonchera">
            <div><strong>${alimento.nombre}</strong><div style="font-size: 0.85rem; color: #7f8c8d;">${alimento.cantidad}g • ${alimento.calorias} cal • $${alimento.precio}</div></div>
            <button class="btn-remove" onclick="eliminarAlimento(${alimento.id})"><i class="fas fa-trash"></i></button>
        </div>
    `).join('');
}

function actualizarResumen() {
    const totalAlimentos = alimentosEnLonchera.length;
    const totalCalorias = alimentosEnLonchera.reduce((sum, a) => sum + a.calorias, 0);
    const totalPrecio = alimentosEnLonchera.reduce((sum, a) => sum + a.precio, 0);
    document.getElementById('total-alimentos').textContent = totalAlimentos;
    document.getElementById('total-calorias').textContent = totalCalorias;
    document.getElementById('total-precio').textContent = totalPrecio.toFixed(2);
}

// --- CREAR LONCHERA (Backend) ---
window.crearLonchera = async function() {
    try {
        if (!hijoSeleccionado) { Swal.fire('Error', 'Selecciona un hijo', 'error'); return; }
        const selectDireccion = document.getElementById('select-direccion');
        if (!selectDireccion.value) { Swal.fire('Error', 'Selecciona dirección', 'warning'); return; }
        const nombreLonchera = document.getElementById('nombre-lonchera').value.trim();
        if (!nombreLonchera) { Swal.fire('Error', 'Ponle nombre a la lonchera', 'error'); return; }
        if (alimentosEnLonchera.length === 0) { Swal.fire('Error', 'Agrega alimentos', 'error'); return; }

        Swal.fire({ title: 'Creando...', didOpen: () => Swal.showLoading() });
        const token = localStorage.getItem('access_token');
        const userId = localStorage.getItem('user_id');

        const dataLonchera = {
            nombre: nombreLonchera,
            descripcion: `Lonchera para ${document.getElementById('select-hijo').selectedOptions[0].text}`,
            calorias: 0, precio: 0, usuario_id: parseInt(userId), direccion_id: parseInt(selectDireccion.value)
        };

        const resLonchera = await fetch(`${API_URL}/loncheras`, {
            method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify(dataLonchera)
        });

        if (!resLonchera.ok) throw new Error('Error al crear lonchera base');
        const lonchera = await resLonchera.json();

        for (const alimento of alimentosEnLonchera) {
            await fetch(`${API_URL}/loncheras/${lonchera.id}/alimentos`, {
                method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                body: JSON.stringify({ alimento_id: alimento.id, cantidad_gramos: alimento.cantidad })
            });
        }

        Swal.close();
        Swal.fire({ icon: 'success', title: '¡Creada!', showConfirmButton: false, timer: 1500 }).then(() => window.location.href = 'loncheras.html');
    } catch (error) {
        Swal.close(); console.error(error); Swal.fire('Error', 'No se pudo crear la lonchera', 'error');
    }
}