// restricciones.js
const API_URL = 'http://127.0.0.1:8000';
let hijoSeleccionado = null;

// Cargar hijos al iniciar
document.addEventListener('DOMContentLoaded', () => {
    cargarHijos();
});

// Cargar hijos del usuario
async function cargarHijos() {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = 'login.html';
            return;
        }

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
                // Mostrar nombre completo
                option.textContent = `${hijo.nombre} ${hijo.apellido || ''}`.trim();
                select.appendChild(option);
            });

            // Listener para cambio de hijo
            select.addEventListener('change', (e) => {
                hijoSeleccionado = e.target.value;
                if (hijoSeleccionado) {
                    cargarRestriccionesHijo(hijoSeleccionado);
                } else {
                    mostrarEstadoVacio();
                }
            });
        }
    } catch (error) {
        console.error('Error al cargar hijos:', error);
        Swal.fire('Error', 'No se pudieron cargar los hijos', 'error');
    }
}

// Cargar restricciones de un hijo
async function cargarRestriccionesHijo(hijoId) {
    try {
        Swal.fire({ title: 'Cargando...', allowOutsideClick: false, didOpen: () => Swal.showLoading() });

        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL}/hijo/${hijoId}/restricciones`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        Swal.close();

        if (response.ok) {
            const restricciones = await response.json();
            renderizarRestricciones(restricciones);
        } else {
            mostrarEstadoVacio();
        }
    } catch (error) {
        Swal.close();
        console.error('Error:', error);
        mostrarEstadoVacio();
    }
}

// Renderizar restricciones
function renderizarRestricciones(restricciones) {
    const container = document.getElementById('lista-restricciones');
    const count = document.getElementById('count-restricciones');

    count.textContent = restricciones.length;

    if (restricciones.length === 0) {
        mostrarEstadoVacio();
        return;
    }

    container.innerHTML = restricciones.map(r => `
        <div class="restriccion-item">
            <div class="restriccion-content">
                <div class="restriccion-name">${r.nombre}</div>
                <p class="restriccion-desc">${r.descripcion || 'Sin descripción'}</p>
                <span class="restriccion-badge badge-${r.nivel_severidad.toLowerCase()}">${r.nivel_severidad}</span>
            </div>
            <button class="btn-delete-restriccion" onclick="eliminarRestriccion(${r.id})">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `).join('');
}

// Mostrar estado vacío
function mostrarEstadoVacio() {
    const container = document.getElementById('lista-restricciones');
    const count = document.getElementById('count-restricciones');
    count.textContent = '0';

    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon"><i class="fas fa-check-circle"></i></div>
            <h4 class="empty-title">Sin restricciones</h4>
            <p class="empty-subtitle">Todo seguro por ahora.</p>
        </div>
    `;
}

// Crear restricción
document.getElementById('form-restriccion')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!hijoSeleccionado) {
        Swal.fire('Atención', 'Debes seleccionar un hijo primero', 'warning');
        return;
    }

    const datos = {
        nombre: document.getElementById('nombre-restriccion').value.trim(),
        descripcion: document.getElementById('descripcion-restriccion').value.trim(),
        nivel_severidad: document.getElementById('severidad-restriccion').value
    };

    try {
        Swal.fire({ title: 'Guardando...', allowOutsideClick: false, didOpen: () => Swal.showLoading() });

        const token = localStorage.getItem('access_token');

        // 1. Crear restricción
        const responseRestriccion = await fetch(`${API_URL}/restriccion/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datos)
        });

        if (!responseRestriccion.ok) {
            const error = await responseRestriccion.json();
            throw new Error(error.detail || 'Error al crear restricción');
        }

        const restriccionCreada = await responseRestriccion.json();

        // 2. Asociar al hijo
        const responseAsociar = await fetch(`${API_URL}/hijo/${hijoSeleccionado}/restriccion/${restriccionCreada.id}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!responseAsociar.ok) {
            throw new Error('Error al asociar restricción');
        }

        Swal.close();
        Swal.fire('¡Éxito!', 'Restricción agregada correctamente', 'success');

        // Cerrar modal y recargar
        const modalElement = document.getElementById('modalRestriccion');
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) modal.hide();

        document.getElementById('form-restriccion').reset();
        cargarRestriccionesHijo(hijoSeleccionado);

    } catch (error) {
        Swal.close();
        console.error('Error:', error);
        Swal.fire('Error', error.message || 'No se pudo guardar la restricción', 'error');
    }
});

// Eliminar restricción
async function eliminarRestriccion(restriccionId) {
    const result = await Swal.fire({
        title: '¿Eliminar restricción?',
        text: 'Esta acción no se puede deshacer',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e74c3c',
        cancelButtonColor: '#95a5a6',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    });

    if (!result.isConfirmed) return;

    try {
        Swal.fire({ title: 'Eliminando...', allowOutsideClick: false, didOpen: () => Swal.showLoading() });

        const token = localStorage.getItem('access_token');

        // Desasociar del hijo
        const response = await fetch(`${API_URL}/hijo/${hijoSeleccionado}/restriccion/${restriccionId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        Swal.close();

        if (response.ok) {
            Swal.fire('Eliminada', 'Restricción eliminada correctamente', 'success');
            cargarRestriccionesHijo(hijoSeleccionado);
        } else {
            throw new Error('Error al eliminar');
        }
    } catch (error) {
        Swal.close();
        console.error('Error:', error);
        Swal.fire('Error', 'No se pudo eliminar la restricción', 'error');
    }
}