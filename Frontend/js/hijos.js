// ========================================
// HIJOS.JS - Gestión de Perfiles de Hijos
// ========================================

window.hijos = [];

// --- Utilidades Visuales ---
function toggleImageInput(tipo) {
    const containerUrl = document.getElementById('input-url-container');
    const containerFile = document.getElementById('input-file-container');

    if (!containerUrl || !containerFile) return;

    if (tipo === 'url') {
        containerUrl.style.display = 'block';
        containerFile.style.display = 'none';
        const fileInput = document.getElementById('hijo-imagen-archivo');
        if(fileInput) fileInput.value = "";
    } else {
        containerUrl.style.display = 'none';
        containerFile.style.display = 'block';
    }
}

function showAddChildModal() {
    const form = document.getElementById('form-hijo');
    if(form) form.reset();
    document.getElementById('hijo-id').value = '';

    const title = document.getElementById('modalTitle');
    if(title) title.innerHTML = 'Nuevo Perfil';

    const radioUrl = document.getElementById('option-url');
    if(radioUrl) {
        radioUrl.checked = true;
        toggleImageInput('url');
    }

    new bootstrap.Modal(document.getElementById('modalHijo')).show();
}

function showEditChildModal(id) {
    const hijo = window.hijos.find(h => h.id === id);
    if (!hijo) return;

    document.getElementById('hijo-id').value = hijo.id;
    document.getElementById('hijo-nombre').value = hijo.nombre;
    document.getElementById('hijo-apellido').value = hijo.apellido || '';
    document.getElementById('hijo-edad').value = hijo.edad || '';

    let genero = "Otro";
    // Extraer género de la bio si existe
    if (hijo.genero) genero = hijo.genero;

    const generoSelect = document.getElementById('hijo-genero');
    if(generoSelect) generoSelect.value = genero;

    // Foto
    const currentFoto = hijo.foto_perfil || "";
    document.getElementById('hijo-imagen-url').value = currentFoto;

    document.getElementById('modalTitle').innerHTML = 'Editar Perfil';
    new bootstrap.Modal(document.getElementById('modalHijo')).show();
}

// --- Carga de Datos ---
async function loadHijos() {
    try {
        const response = await fetch("/hijo/", { method: 'GET', headers: AUTH_HEADERS });
        if (response.ok) {
            window.hijos = await response.json();
            renderHijos();
        } else {
            console.warn("No se pudieron cargar hijos. Status:", response.status);
        }
    } catch (error) {
        console.error("Error red:", error);
    }
}

// --- Renderizado ---
function renderHijos() {
    const container = document.getElementById("hijosContainer");
    if (!container) return;

    if (!window.hijos || window.hijos.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="fas fa-child fa-3x text-muted opacity-25 mb-3"></i>
                <h5 class="text-muted">No tienes hijos registrados</h5>
                <button class="btn btn-success rounded-pill mt-3 px-4" onclick="showAddChildModal()">
                    <i class="fas fa-plus me-2"></i>Agregar Primero
                </button>
            </div>`;
        return;
    }

    container.innerHTML = window.hijos.map(hijo => `
        <div class="col-md-6 col-lg-4 col-xl-3">
            <div class="child-card h-100">
                <div class="child-header">
                    <div class="child-avatar">
                        <img src="${hijo.foto_perfil || 'https://cdn-icons-png.flaticon.com/512/3011/3011270.png'}" 
                             style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">
                    </div>
                    <div class="child-info">
                        <h5>${hijo.nombre} ${hijo.apellido || ''}</h5>
                        <span>${hijo.edad ? hijo.edad + ' años' : ''}</span>
                    </div>
                </div>
                <div class="child-actions">
                    <a href="crear-lonchera.html?hijoId=${hijo.id}" class="btn-action-main text-decoration-none">
                        Lonchera
                    </a>
                    <button class="btn-icon" onclick="showEditChildModal(${hijo.id})">
                        <i class="fas fa-pen text-primary"></i>
                    </button>
                    <button class="btn-icon btn-delete" onclick="deleteHijo(${hijo.id})">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </div>
        </div>
    `).join("");
}

// --- Guardar (FormData) ---
async function guardarHijo(event) {
    event.preventDefault();

    const id = document.getElementById('hijo-id').value;
    const isEdit = !!id;

    const formData = new FormData();
    formData.append('nombre', document.getElementById('hijo-nombre').value.trim());
    formData.append('apellido', document.getElementById('hijo-apellido').value.trim() || 'Apellido');
    formData.append('edad', document.getElementById('hijo-edad').value);
    formData.append('genero', document.getElementById('hijo-genero').value);

    if (!isEdit) {
        formData.append('email', `hijo_${Date.now()}@nutribox.local`);
        formData.append('password', 'password123');
    }

    // Imagen
    const tipoImagen = document.querySelector('input[name="tipoImagen"]:checked').value;
    formData.append('tipo_imagen', tipoImagen);

    if (tipoImagen === 'url') {
        const urlVal = document.getElementById('hijo-imagen-url').value;
        formData.append('imagen_url', urlVal);
    } else {
        const fileInput = document.getElementById('hijo-imagen-archivo');
        if (fileInput.files[0]) {
            formData.append('imagen_archivo', fileInput.files[0]);
        }
    }

    try {
        const url = isEdit ? `/hijo/${id}` : "/hijo/";
        const method = isEdit ? "PUT" : "POST";
        const token = localStorage.getItem("access_token");

        Swal.fire({ title: 'Guardando...', didOpen: () => Swal.showLoading() });

        const response = await fetch(url, {
            method: method,
            headers: { 'Authorization': `Bearer ${token}` }, // FormData maneja su propio Content-Type
            body: formData
        });

        // --- MANEJO DE ERRORES ROBUSTO ---
        if (!response.ok) {
            const text = await response.text(); // Leemos texto crudo primero
            let errorMsg = 'Error en el servidor';
            try {
                const json = JSON.parse(text);
                errorMsg = json.detail || errorMsg;
            } catch (e) {
                // Si falla el parseo, es HTML o Texto plano (Error 500 duro)
                console.error("Respuesta no JSON:", text);
                errorMsg = "Error interno del servidor (Revisar logs)";
            }
            throw new Error(errorMsg);
        }

        // Éxito
        const modal = bootstrap.Modal.getInstance(document.getElementById('modalHijo'));
        if(modal) modal.hide();

        Swal.fire({ icon: 'success', title: '¡Guardado!', timer: 1500, showConfirmButton: false });
        loadHijos();

    } catch (error) {
        console.error(error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message
        });
    }
}

async function deleteHijo(id) {
    const result = await Swal.fire({
        title: '¿Estás seguro?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: 'Sí, eliminar'
    });

    if (result.isConfirmed) {
        try {
            await fetch(`/hijo/${id}`, { method: 'DELETE', headers: AUTH_HEADERS });
            Swal.fire('Eliminado', '', 'success');
            loadHijos();
        } catch (e) { Swal.fire('Error', 'No se pudo eliminar', 'error'); }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (!localStorage.getItem("access_token")) {
        window.location.href = "login.html";
        return;
    }

    const form = document.getElementById("form-hijo");
    if(form) {
        // Evitar listeners duplicados
        const newForm = form.cloneNode(true);
        form.parentNode.replaceChild(newForm, form);
        newForm.addEventListener("submit", guardarHijo);
    }

    loadHijos();
    if(typeof setupLogoutButton === 'function') setupLogoutButton();
});