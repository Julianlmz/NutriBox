// ========================================
// HIJOS.JS - Gestión de Perfiles de Hijos
// ========================================

// Variable global para almacenar hijos
window.hijos = [];

// ========================================
// FUNCIÓN: Cargar Hijos desde la API
// ========================================
async function loadHijos() {
    try {
        console.log("Cargando hijos...");

        const response = await fetch("/hijo/", {
            method: 'GET',
            headers: AUTH_HEADERS
        });

        if (!response.ok) {
            throw new Error('Error al cargar hijos');
        }

        window.hijos = await response.json();
        console.log("Hijos cargados:", window.hijos);

        renderHijos();

    } catch (error) {
        console.error("Error al cargar hijos:", error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudieron cargar los perfiles de hijos'
        });
    }
}

// ========================================
// FUNCIÓN: Renderizar Hijos en el DOM
// ========================================
function renderHijos() {
    const container = document.getElementById("hijosContainer");

    if (!container) {
        console.error("Contenedor hijosContainer no encontrado");
        return;
    }

    if (!window.hijos || window.hijos.length === 0) {
        container.innerHTML = `
            <div class="col-12 empty-state">
                <i class="fas fa-child empty-icon"></i>
                <h5>No tienes hijos registrados</h5>
                <button class="btn btn-outline-success rounded-pill mt-3" onclick="showAddChildModal()">Agregar Primero</button>
            </div>`;
        return;
    }

    container.innerHTML = window.hijos.map(hijo => `
        <div class="col-xl-3 col-lg-4 col-md-6">
            <div class="child-card">
                <div class="child-header">
                    <div class="child-avatar"><i class="fas fa-user"></i></div>
                    <div class="child-info">
                        <h5>${hijo.nombre} ${hijo.apellido || ''}</h5>
                        <span>${hijo.edad || '?'} años</span>
                    </div>
                </div>
                <div class="child-actions">
                    <a href="crear-lonchera.html?hijoId=${hijo.id}" class="btn-action-main">
                        <i class="fas fa-utensils me-1"></i> Lonchera
                    </a>
                    <button class="btn-icon btn-delete" onclick="deleteHijo(${hijo.id})">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </div>
        </div>
    `).join("");
}

// ========================================
// FUNCIÓN: Eliminar Hijo
// ========================================
async function deleteHijo(hijoId) {
    try {
        const result = await Swal.fire({
            title: '¿Eliminar perfil?',
            text: "Esta acción no se puede deshacer",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        });

        if (result.isConfirmed) {
            const response = await fetch(`/hijo/${hijoId}`, {
                method: 'DELETE',
                headers: AUTH_HEADERS
            });

            if (response.ok || response.status === 204) {
                Swal.fire({
                    icon: 'success',
                    title: 'Eliminado',
                    text: 'El perfil ha sido eliminado',
                    timer: 1500,
                    showConfirmButton: false
                });

                await loadHijos();
            } else {
                throw new Error('Error al eliminar');
            }
        }
    } catch (error) {
        console.error("Error al eliminar hijo:", error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudo eliminar el perfil'
        });
    }
}

// ========================================
// FUNCIÓN: Guardar/Crear Hijo
// ========================================
async function guardarHijo(event) {
    event.preventDefault();

    const nombre = document.getElementById('hijo-nombre').value;
    const apellido = document.getElementById('hijo-apellido')?.value || '';
    const edad = parseInt(document.getElementById('hijo-edad').value);
    const genero = document.getElementById('hijo-genero')?.value || '';

    // Generar un email único para el hijo (requerido por el backend)
    const email = `hijo_${nombre.toLowerCase()}_${Date.now()}@nutribox.local`;
    const password = `password123`; // Password por defecto

    try {
        const response = await fetch("/hijo/", {
            method: 'POST',
            headers: AUTH_HEADERS,
            body: JSON.stringify({
                nombre: nombre,
                apellido: apellido,
                email: email,
                password: password
                // Si tu modelo Hijo tiene más campos, agrégalos aquí
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error al guardar');
        }

        const nuevoHijo = await response.json();
        console.log("Hijo creado:", nuevoHijo);

        // Cerrar modal
        const modalElement = document.getElementById('modalHijo');
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) modal.hide();

        // Limpiar formulario
        document.getElementById('form-hijo').reset();

        // Mostrar éxito
        Swal.fire({
            icon: 'success',
            title: '¡Guardado!',
            text: 'Perfil creado correctamente',
            timer: 1500,
            showConfirmButton: false
        });

        // Recargar lista
        await loadHijos();

    } catch (error) {
        console.error("Error al guardar hijo:", error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'No se pudo guardar el perfil'
        });
    }
}

// ========================================
// FUNCIÓN: Mostrar Modal para Agregar
// ========================================
function showAddChildModal() {
    const form = document.getElementById('form-hijo');
    if (form) form.reset();

    document.getElementById('hijo-id').value = '';
    document.getElementById('modalTitle').innerText = 'Nuevo Perfil';

    const modalElement = document.getElementById('modalHijo');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

// ========================================
// FUNCIÓN: Logout
// ========================================
function logout() {
    localStorage.removeItem("access_token");
    Swal.fire({
        icon: 'success',
        title: '¡Hasta luego!',
        timer: 1500,
        showConfirmButton: false
    }).then(() => {
        window.location.href = "login.html";
    });
}

// ========================================
// INICIALIZACIÓN
// ========================================
document.addEventListener("DOMContentLoaded", function() {
    console.log("hijos.js inicializado");

    // Cargar hijos al inicio
    loadHijos();

    // Configurar logout
    setupLogoutButton();
});