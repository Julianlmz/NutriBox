const API_BASE_URL = "";

// Función para obtener headers con token
function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}

// ✅ NUEVA: Función para obtener el ID del usuario
function getUserId() {
    return localStorage.getItem('user_id');
}

// Variable global para almacenar direcciones
window.direcciones = [];

// ============================================
// 1. CARGAR DIRECCIONES
// ============================================
async function loadDirecciones() {
    try {
        const userId = getUserId();

        if (!userId) {
            throw new Error('Usuario no autenticado');
        }

        const response = await fetch(`${API_BASE_URL}/direcciones/?usuario_id=${userId}`, {
            method: 'GET',
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error(`Error al cargar direcciones: ${response.status}`);
        }

        window.direcciones = await response.json();
        renderDirecciones();

    } catch (error) {
        console.error("Error:", error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudieron cargar las direcciones'
        });
    }
}

// ============================================
// 2. RENDERIZAR DIRECCIONES
// ============================================
function renderDirecciones() {
    const container = document.getElementById("direccionesContainer");

    if (!window.direcciones || window.direcciones.length === 0) {
        container.innerHTML = `
            <div class="col-12 empty-state">
                <i class="fas fa-map-marker-alt empty-icon"></i>
                <h5>No tienes direcciones registradas</h5>
                <p class="text-muted">Agrega tu primera dirección de entrega</p>
                <button class="btn btn-outline-success rounded-pill mt-3" onclick="showAddDireccionModal()">
                    <i class="fas fa-plus me-2"></i>Agregar Primera Dirección
                </button>
            </div>`;
        return;
    }

    container.innerHTML = window.direcciones.map(direccion => `
        <div class="col-lg-6">
            <div class="address-card">
                <div class="address-header">
                    <div class="address-icon">
                        <i class="fas fa-map-marker-alt"></i>
                    </div>
                    <div class="address-info">
                        <h5>${direccion.nombre || 'Dirección'}</h5>
                        ${direccion.principal ? '<span class="badge bg-success">Principal</span>' : ''}
                    </div>
                </div>
                <div class="address-body">
                    <p class="mb-2"><i class="fas fa-home me-2 text-muted"></i>${direccion.direccion}</p>
                    ${direccion.ciudad ? `<p class="mb-0"><i class="fas fa-city me-2 text-muted"></i>${direccion.ciudad}</p>` : ''}
                </div>
                <div class="address-actions">
                    ${!direccion.principal ? `
                        <button class="btn btn-sm btn-outline-success rounded-pill" onclick="setPrincipal(${direccion.id})">
                            <i class="fas fa-star me-1"></i>Hacer Principal
                        </button>
                    ` : '<div></div>'}
                    <div class="d-flex gap-2">
                        <button class="btn-icon btn-edit" onclick="editDireccion(${direccion.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon btn-delete" onclick="deleteDireccion(${direccion.id})">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join("");
}

// ============================================
// 3. GUARDAR DIRECCIÓN (Crear/Editar)
// ============================================
async function guardarDireccion(event) {
    event.preventDefault();

    const direccionId = document.getElementById('direccion-id').value;
    const nombre = document.getElementById('direccion-nombre').value;
    const direccion = document.getElementById('direccion-direccion').value;
    const ciudad = document.getElementById('direccion-ciudad').value || "Bogotá";
    const principal = document.getElementById('direccion-principal').checked;

    const data = {
        nombre: nombre,
        direccion: direccion,
        ciudad: ciudad,
        principal: principal
    };

    try {
        const url = direccionId
            ? `${API_BASE_URL}/direcciones/${direccionId}`
            : `${API_BASE_URL}/usuarios/${getUserId()}/direcciones`;

        const method = direccionId ? 'PATCH' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: getAuthHeaders(),
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error al guardar');
        }

        // Cerrar modal
        const modalElement = document.getElementById('modalDireccion');
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) modal.hide();

        // Limpiar formulario
        document.getElementById('form-direccion').reset();
        document.getElementById('direccion-ciudad').value = "Bogotá";

        // Mostrar éxito
        await Swal.fire({
            icon: 'success',
            title: direccionId ? 'Dirección actualizada' : 'Dirección agregada',
            showConfirmButton: false,
            timer: 1500
        });

        // Recargar lista
        loadDirecciones();

    } catch (error) {
        console.error("Error:", error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'No se pudo guardar la dirección'
        });
    }
}

// ============================================
// 4. ELIMINAR DIRECCIÓN
// ============================================
async function deleteDireccion(direccionId) {
    const result = await Swal.fire({
        title: '¿Eliminar dirección?',
        text: 'Esta acción no se puede deshacer',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef5350',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    });

    if (!result.isConfirmed) return;

    try {
        const response = await fetch(`${API_BASE_URL}/direcciones/${direccionId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });

        if (response.status === 204 || response.ok) {
            await Swal.fire({
                icon: 'success',
                title: 'Dirección eliminada',
                showConfirmButton: false,
                timer: 1500
            });
            loadDirecciones();
        } else {
            throw new Error('Error al eliminar');
        }

    } catch (error) {
        console.error("Error:", error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudo eliminar la dirección'
        });
    }
}

// ============================================
// 5. EDITAR DIRECCIÓN
// ============================================
function editDireccion(direccionId) {
    const direccion = window.direcciones.find(d => d.id === direccionId);
    if (!direccion) return;

    // Llenar el formulario
    document.getElementById('direccion-id').value = direccion.id;
    document.getElementById('direccion-nombre').value = direccion.nombre || '';
    document.getElementById('direccion-direccion').value = direccion.direccion;
    document.getElementById('direccion-ciudad').value = direccion.ciudad || 'Bogotá';
    document.getElementById('direccion-principal').checked = direccion.principal || false;

    // Cambiar título del modal
    document.getElementById('modalTitle').innerText = 'Editar Dirección';

    // Mostrar modal
    const modalElement = document.getElementById('modalDireccion');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

// ============================================
// 6. ESTABLECER DIRECCIÓN PRINCIPAL
// ============================================
async function setPrincipal(direccionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/direcciones/${direccionId}/principal`, {
            method: 'POST',
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error('Error al establecer dirección principal');
        }

        await Swal.fire({
            icon: 'success',
            title: 'Dirección principal actualizada',
            showConfirmButton: false,
            timer: 1500
        });

        loadDirecciones();

    } catch (error) {
        console.error("Error:", error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudo establecer como principal'
        });
    }
}

// ============================================
// 7. MOSTRAR MODAL NUEVA DIRECCIÓN
// ============================================
function showAddDireccionModal() {
    const form = document.getElementById('form-direccion');
    if (form) form.reset();

    document.getElementById('direccion-id').value = '';
    document.getElementById('direccion-ciudad').value = 'Bogotá';
    document.getElementById('modalTitle').innerText = 'Nueva Dirección';

    const modalElement = document.getElementById('modalDireccion');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

// ============================================
// 8. INICIALIZACIÓN
// ============================================
document.addEventListener("DOMContentLoaded", function() {
    loadDirecciones();

    // Configurar formulario
    const form = document.getElementById('form-direccion');
    if (form) {
        form.addEventListener('submit', guardarDireccion);
    }
});