// Nota: TOKEN y AUTH_HEADERS se definen globalmente en auth-guard.js

// --- 1. Funciones de Utilidad Visual (Globales) ---
function toggleImageInput(tipo) {
    const containerUrl = document.getElementById('input-url-container');
    const containerFile = document.getElementById('input-file-container');

    if (tipo === 'url') {
        containerUrl.style.display = 'block';
        containerFile.style.display = 'none';
        const fileInput = document.getElementById('alimento-imagen-file');
        if(fileInput) fileInput.value = ""; // Limpiar archivo si cambia a URL
    } else {
        containerUrl.style.display = 'none';
        containerFile.style.display = 'block';
    }
}
window.toggleImageInput = toggleImageInput;

function toggleEditImageInput(tipo) {
    const containerUrl = document.getElementById('edit-input-url-container');
    const containerFile = document.getElementById('edit-input-file-container');
    if (tipo === 'url') {
        containerUrl.style.display = 'block';
        containerFile.style.display = 'none';
        const fileInput = document.getElementById('edit-alimento-imagen-file');
        if(fileInput) fileInput.value = "";
    } else {
        containerUrl.style.display = 'none';
        containerFile.style.display = 'block';
    }
}
window.toggleEditImageInput = toggleEditImageInput;

// --- 2. Inicialización al Cargar DOM ---
document.addEventListener("DOMContentLoaded", function() {
    // Configurar botón de logout si existe
    if (typeof setupLogoutButton === 'function') setupLogoutButton();

    const ALIMENTO_BASE_URL = "/alimento/";
    const modalEditar = new bootstrap.Modal(document.getElementById('modalEditarAlimento'));
    const CATEGORIAS = ["Frutas", "Vegetales", "Proteínas", "Lácteos", "Cereales", "Snacks", "Bebidas"];

    // A. Llenar selects de categorías
    const selects = [document.getElementById("alimento-categoria"), document.getElementById("edit-alimento-categoria")];
    selects.forEach(select => {
        select.innerHTML = '<option value="">Seleccione Categoría</option>';
        CATEGORIAS.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat; opt.textContent = cat; select.appendChild(opt);
        });
    });

    // B. Inicializar estado visual del toggle
    if (document.getElementById('option-file')) toggleImageInput('file');

    // C. Cargar Datos Iniciales (Validando sesión primero)
    fetch("/usuario/me", { method: 'GET', headers: AUTH_HEADERS })
        .then(r => r.ok ? r.json() : Promise.reject())
        .then(() => cargarAlimentos())
        .catch(console.error);

    function cargarAlimentos() {
        fetch(ALIMENTO_BASE_URL, { method: 'GET', headers: AUTH_HEADERS })
        .then(r => r.json())
        .then(renderAlimentos)
        .catch(console.error);
    }

    function renderAlimentos(alimentos) {
        const container = document.getElementById("lista-alimentos");
        if (!container) return;

        if (alimentos.length === 0) {
            container.innerHTML = '<div class="text-center text-muted p-5">No hay alimentos aún.</div>';
            return;
        }

        // Agrupar alimentos por categoría
        const grupos = alimentos.reduce((acc, item) => {
            (acc[item.categoria] = acc[item.categoria] || []).push(item);
            return acc;
        }, {});

        let html = '';
        Object.keys(grupos).sort().forEach(cat => {
            html += `<h6 class="category-title">${cat} <span class="text-muted small">(${grupos[cat].length})</span></h6><div class="row g-3 mb-4">`;
            grupos[cat].forEach(item => {
                const img = item.imagen_url || 'https://via.placeholder.com/70?text=NB';
                html += `
                <div class="col-12">
                    <div class="card-alimento-item">
                        <img src="${img}" class="alimento-img" onerror="this.src='https://via.placeholder.com/70?text=Error'">
                        <div class="flex-grow-1">
                            <h6 class="mb-0 fw-bold text-dark">${item.nombre}</h6>
                            <div class="small text-muted">
                                <span class="me-3"><i class="fas fa-fire text-warning"></i> ${item.calorias_por_100g} kcal</span>
                                <span class="text-success fw-bold"><i class="fas fa-dollar-sign"></i> ${item.precio_unitario.toFixed(2)}</span>
                            </div>
                        </div>
                        <div class="d-flex gap-2">
                            <button class="btn btn-sm btn-light text-primary" onclick="abrirModalEditar(${item.id})"><i class="fas fa-edit"></i></button>
                            <button class="btn btn-sm btn-light text-danger" onclick="borrarAlimento(${item.id})"><i class="fas fa-trash"></i></button>
                        </div>
                    </div>
                </div>`;
            });
            html += `</div>`;
        });
        container.innerHTML = html;
    }

    // --- 3. CREAR ALIMENTO (Protegido contra Doble Submit y Espacios) ---
    document.getElementById("form-crear-alimento").addEventListener("submit", function(e) {
        e.preventDefault();

        // BLOQUEO DE BOTÓN: Evita el error 409 por doble clic
        const btnGuardar = this.querySelector('button[type="submit"]');
        const textoOriginal = btnGuardar.innerText;
        btnGuardar.disabled = true;
        btnGuardar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';

        const formData = new FormData();

        // Capturar tipo de imagen
        const tipoImagen = document.querySelector('input[name="tipoImagen"]:checked').value;
        formData.append("tipo_imagen", tipoImagen);

        // Capturar campos de texto
        formData.append("nombre", document.getElementById("alimento-nombre").value);
        formData.append("categoria", document.getElementById("alimento-categoria").value);
        formData.append("calorias_por_100g", document.getElementById("alimento-calorias").value);
        formData.append("proteinas_por_100g", document.getElementById("alimento-proteinas").value);
        formData.append("carbohidratos_por_100g", document.getElementById("alimento-carbohidratos").value);
        formData.append("grasas_por_100g", document.getElementById("alimento-grasas").value);
        formData.append("precio_unitario", document.getElementById("alimento-precio").value);
        formData.append("stock_inicial", 0);

        // Capturar imagen con limpieza (.trim)
        if (tipoImagen === 'url') {
            const urlVal = document.getElementById('alimento-imagen-url').value.trim();
            formData.append("imagen_url", urlVal);
        } else {
            const fileInput = document.getElementById("alimento-imagen-file");
            if (fileInput.files[0]) {
                formData.append("imagen", fileInput.files[0]);
            }
        }

        // Enviar al Backend
        fetch(ALIMENTO_BASE_URL, { method: 'POST', body: formData, headers: {'Authorization': `Bearer ${TOKEN}`} })
        .then(async r => {
            if (r.ok) return r.json();
            // Intentar leer error del backend (ej: duplicado)
            const errorData = await r.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Error desconocido al crear alimento');
        })
        .then(() => {
            Swal.fire({icon: 'success', title: 'Guardado', timer: 1500, showConfirmButton: false});
            e.target.reset();
            // Reset visual
            document.getElementById('option-file').checked = true;
            toggleImageInput('file');
            cargarAlimentos();
        })
        .catch(err => {
            console.error(err);
            Swal.fire('Atención', err.message, 'warning');
        })
        .finally(() => {
            // RESTAURAR BOTÓN SIEMPRE (Éxito o Error)
            btnGuardar.disabled = false;
            btnGuardar.innerText = textoOriginal;
        });
    });

    // --- 4. EDITAR ALIMENTO ---
    window.abrirModalEditar = function(id) {
        fetch(`${ALIMENTO_BASE_URL}${id}`, { headers: AUTH_HEADERS })
        .then(r => r.json())
        .then(item => {
            document.getElementById("edit-alimento-id").value = item.id;
            document.getElementById("edit-alimento-nombre").value = item.nombre;
            document.getElementById("edit-alimento-categoria").value = item.categoria;
            document.getElementById("edit-alimento-calorias").value = item.calorias_por_100g;
            document.getElementById("edit-alimento-proteinas").value = item.proteinas_por_100g;
            document.getElementById("edit-alimento-carbohidratos").value = item.carbohidratos_por_100g;
            document.getElementById("edit-alimento-grasas").value = item.grasas_por_100g;
            document.getElementById("edit-alimento-precio").value = item.precio_unitario;

            const img = item.imagen_url || '';
            document.getElementById("edit-alimento-imagen-preview").src = img || 'https://via.placeholder.com/100';

            // Configurar el toggle según lo que tenga el alimento
            if(img && img.startsWith('http') && !img.includes('supabase')) {
                document.getElementById('edit-option-url').checked = true;
                toggleEditImageInput('url');
                document.getElementById('edit-alimento-imagen-url').value = img;
            } else {
                document.getElementById('edit-option-file').checked = true;
                toggleEditImageInput('file');
            }

            modalEditar.show();
        });
    };

    document.getElementById("form-editar-alimento").addEventListener("submit", function(e) {
        e.preventDefault();
        const id = document.getElementById("edit-alimento-id").value;
        const tipoImagen = document.querySelector('input[name="editTipoImagen"]:checked').value;

        // También protegemos este botón
        const btnGuardar = this.querySelector('button[type="submit"]');
        btnGuardar.disabled = true;
        btnGuardar.innerText = 'Guardando...';

        const data = {
            nombre: document.getElementById("edit-alimento-nombre").value,
            categoria: document.getElementById("edit-alimento-categoria").value,
            calorias_por_100g: parseFloat(document.getElementById("edit-alimento-calorias").value),
            proteinas_por_100g: parseFloat(document.getElementById("edit-alimento-proteinas").value),
            carbohidratos_por_100g: parseFloat(document.getElementById("edit-alimento-carbohidratos").value),
            grasas_por_100g: parseFloat(document.getElementById("edit-alimento-grasas").value),
            precio_unitario: parseFloat(document.getElementById("edit-alimento-precio").value),
        };

        if (tipoImagen === 'url') {
            data.imagen_url = document.getElementById("edit-alimento-imagen-url").value.trim();
        }

        fetch(`${ALIMENTO_BASE_URL}${id}`, {
            method: 'PATCH',
            headers: { ...Object.fromEntries(AUTH_HEADERS), 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(async r => {
            if (!r.ok) throw new Error('Error al actualizar datos');

            // Si es archivo, subirlo por separado
            const file = document.getElementById("edit-alimento-imagen-file").files[0];
            if (tipoImagen === 'file' && file) {
                const fd = new FormData(); fd.append("imagen", file);
                await fetch(`${ALIMENTO_BASE_URL}${id}/upload-image`, { method: 'POST', body: fd, headers: {'Authorization': `Bearer ${TOKEN}`} });
            }
        })
        .then(() => {
            modalEditar.hide();
            Swal.fire({icon: 'success', title: 'Actualizado', timer: 1500, showConfirmButton: false});
            cargarAlimentos();
        })
        .catch((err) => {
            console.error(err);
            Swal.fire('Error', 'No se pudo actualizar el alimento', 'error');
        })
        .finally(() => {
            btnGuardar.disabled = false;
            btnGuardar.innerText = 'Guardar Cambios';
        });
    });

    // --- 5. BORRAR ALIMENTO ---
    window.borrarAlimento = function(id) {
        Swal.fire({
            title: '¿Borrar alimento?',
            text: "Esta acción no se puede deshacer",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Sí, borrar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#d33'
        }).then((result) => {
            if (result.isConfirmed) {
                fetch(`${ALIMENTO_BASE_URL}${id}`, { method: 'DELETE', headers: AUTH_HEADERS })
                .then(r => {
                    if (r.ok) {
                        cargarAlimentos();
                        Swal.fire('Borrado', 'El alimento ha sido eliminado', 'success');
                    } else {
                        Swal.fire('Error', 'No se pudo eliminar', 'error');
                    }
                });
            }
        });
    };
});