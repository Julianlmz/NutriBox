document.addEventListener("DOMContentLoaded", function() {

    // 1. Setup inicial
    setupLogoutButton();
    const mobileLogout = document.getElementById("logout-button-mobile");
    if (mobileLogout) {
        mobileLogout.addEventListener("click", () => {
             document.getElementById("logout-button").click();
        });
    }

    // El endpoint base para Alimentos (Ruta relativa correcta)
    const ALIMENTO_BASE_URL = "/alimento/";

    // Referencias a elementos del DOM
    const listaDiv = document.getElementById("lista-alimentos");
    const modalElement = document.getElementById('modalEditarAlimento');
    const modalEditar = new bootstrap.Modal(modalElement);
    const formCrearAlimento = document.getElementById("form-crear-alimento");
    const formEditarAlimento = document.getElementById("form-editar-alimento");

    // Datos de la categoría
    const CATEGORIAS = [
        "Frutas", "Vegetales", "Proteínas", "Lácteos", "Cereales", "Snacks", "Bebidas"
    ];

    // Llenamos selectores inmediatamente
    llenarSelectoresCategoria();

    function llenarSelectoresCategoria() {
        const selects = [
            document.getElementById("alimento-categoria"),
            document.getElementById("edit-alimento-categoria")
        ];

        selects.forEach(select => {
            select.innerHTML = '<option value="">Seleccione Categoría</option>';
            CATEGORIAS.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat;
                option.textContent = cat;
                select.appendChild(option);
            });
        });
    }

    // --- CORRECCIÓN CRÍTICA AQUÍ ---
    // Antes decía: fetch("http://127.0.0.1:8000/usuario/me", ...)
    // Ahora usa ruta relativa para que funcione en Render:
    fetch("/usuario/me", { method: 'GET', headers: AUTH_HEADERS })
        .then(response => {
            if (response.ok) { return response.json(); }
            else { throw new Error('Token inválido o expirado.'); }
        })
        .then(usuario => {
            const loadingElem = document.getElementById("alimentos-loading");
            if(loadingElem) loadingElem.textContent = `Cargando alimentos...`;
            cargarAlimentos();
        })
        .catch(gestionarErrorDeAutenticacion);


    // ==============================================
    // FUNCIÓN 2: Cargar Alimentos (Read)
    // ==============================================
    function cargarAlimentos() {
        const loadingText = document.getElementById("alimentos-loading");
        if (loadingText) { loadingText.style.display = "block"; }
        listaDiv.innerHTML = "";

        fetch(ALIMENTO_BASE_URL, { method: 'GET', headers: AUTH_HEADERS })
        .then(response => {
            if (!response.ok) { throw new Error('Error al cargar alimentos'); }
            return response.json();
        })
        .then(alimentos => {
            if (loadingText) { loadingText.style.display = "none"; }

            if (alimentos.length === 0) {
                listaDiv.innerHTML = '<div class="text-center text-muted p-4">No hay alimentos aún.</div>';
                return;
            }

            alimentos.forEach(alimento => {
                const card = document.createElement('div');
                card.className = 'card-alimento-item';

                const imageUrl = alimento.imagen_url || 'https://via.placeholder.com/60/E8F5E9/4CAF50?text=Nb';

                card.innerHTML = `
                    <img src="${imageUrl}" class="alimento-img" alt="${alimento.nombre}">
                    
                    <div class="flex-grow-1">
                        <h6 class="mb-0 fw-bold text-dark">${alimento.nombre}</h6>
                        <div class="small text-muted mt-1">
                            <span class="badge bg-light text-secondary border me-1">${alimento.categoria}</span>
                            <span><i class="fas fa-fire text-warning me-1"></i>${alimento.calorias_por_100g} kcal</span>
                        </div>
                    </div>
                    
                    <div class="d-flex gap-2">
                        <button class="btn btn-sm btn-outline-primary btn-editar-alimento border-0 bg-light text-primary" 
                                data-id="${alimento.id}" title="Editar">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger btn-borrar-alimento border-0 bg-light text-danger" 
                                data-id="${alimento.id}" title="Borrar">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                `;
                listaDiv.appendChild(card);
            });
        })
        .catch(error => {
            console.error("Error al cargar alimentos:", error);
            if (loadingText) { loadingText.textContent = "Error al cargar los alimentos."; }
        });
    }

    // ==============================================
    // FUNCIÓN 3: Crear Alimento (Create)
    // ==============================================
    formCrearAlimento.addEventListener("submit", function(event) {
        event.preventDefault();

        const formData = new FormData(formCrearAlimento);

        formData.append("nombre", document.getElementById("alimento-nombre").value);
        formData.append("categoria", document.getElementById("alimento-categoria").value);
        formData.append("calorias_por_100g", document.getElementById("alimento-calorias").value);
        formData.append("proteinas_por_100g", document.getElementById("alimento-proteinas").value);
        formData.append("carbohidratos_por_100g", document.getElementById("alimento-carbohidratos").value);
        formData.append("grasas_por_100g", document.getElementById("alimento-grasas").value);

        formData.append("precio_unitario", document.getElementById("alimento-precio").value || 0);
        formData.append("stock_inicial", document.getElementById("alimento-stock").value || 0);

        const fileInput = document.getElementById("alimento-imagen");
        if (fileInput.files.length > 0) {
            formData.append("imagen", fileInput.files[0]);
        }

        fetch(ALIMENTO_BASE_URL, {
            method: 'POST',
            body: formData,
            headers: {
                'Authorization': `Bearer ${TOKEN}`
            }
        })
        .then(response => {
            if (response.ok) { return response.json(); }
            else {
                 return response.json().then(error => { throw new Error(error.detail || 'Error al crear.'); });
            }
        })
        .then(nuevoAlimento => {
            Swal.fire({
                icon: 'success',
                title: '¡Guardado!',
                text: `${nuevoAlimento.nombre} añadido correctamente.`,
                timer: 1500,
                showConfirmButton: false,
                confirmButtonColor: '#4CAF50'
            });
            formCrearAlimento.reset();
            cargarAlimentos();
        })
        .catch(error => {
            Swal.fire('Error', error.message, 'error');
        });
    });


    // ==============================================
    // FUNCIÓN 4: Borrar Alimento
    // ==============================================
    listaDiv.addEventListener("click", function(event) {
        const btnBorrar = event.target.closest(".btn-borrar-alimento");
        if (btnBorrar) {
            const alimentoId = btnBorrar.dataset.id;

            Swal.fire({
                title: '¿Borrar alimento?',
                text: "Esta acción no se puede deshacer.",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#f8f9fa',
                cancelButtonText: '<span style="color: #555">Cancelar</span>',
                confirmButtonText: 'Sí, borrar'
            }).then((result) => {
                if (result.isConfirmed) {
                    fetch(`${ALIMENTO_BASE_URL}${alimentoId}`, {
                        method: 'DELETE',
                        headers: { 'Authorization': `Bearer ${TOKEN}` }
                    })
                    .then(response => {
                        if (response.status === 204) {
                            Swal.fire({
                                icon: 'success',
                                title: '¡Borrado!',
                                text: 'El alimento ha sido eliminado.',
                                showConfirmButton: false,
                                timer: 1500
                            });
                            cargarAlimentos();
                        } else {
                            throw new Error('Error al borrar.');
                        }
                    })
                    .catch(error => {
                        Swal.fire('Error', 'No se pudo borrar el alimento.', 'error');
                    });
                }
            });
        }

        const btnEditar = event.target.closest(".btn-editar-alimento");
        if (btnEditar) {
            const alimentoId = btnEditar.dataset.id;
            abrirModalEditar(alimentoId);
        }
    });

    // ==============================================
    // FUNCIÓN 5: Editar Alimento
    // ==============================================
    function abrirModalEditar(alimentoId) {
        fetch(`${ALIMENTO_BASE_URL}${alimentoId}`, { method: 'GET', headers: AUTH_HEADERS })
            .then(response => response.json())
            .then(alimento => {
                document.getElementById("edit-alimento-id").value = alimento.id;
                document.getElementById("edit-alimento-nombre").value = alimento.nombre;
                document.getElementById("edit-alimento-categoria").value = alimento.categoria;
                document.getElementById("edit-alimento-calorias").value = alimento.calorias_por_100g;
                document.getElementById("edit-alimento-proteinas").value = alimento.proteinas_por_100g;
                document.getElementById("edit-alimento-carbohidratos").value = alimento.carbohidratos_por_100g;
                document.getElementById("edit-alimento-grasas").value = alimento.grasas_por_100g;

                document.getElementById("edit-alimento-precio").value = alimento.precio_unitario;
                document.getElementById("edit-alimento-stock").value = alimento.stock_actual;

                const preview = document.getElementById("edit-alimento-imagen-preview");
                preview.src = alimento.imagen_url || 'https://via.placeholder.com/150/E8F5E9/4CAF50?text=Sin+Imagen';

                modalEditar.show();
            })
            .catch(error => {
                Swal.fire('Error', 'No se pudo cargar el alimento.', 'error');
            });
    }

    formEditarAlimento.addEventListener("submit", function(event) {
        event.preventDefault();

        const alimentoId = document.getElementById("edit-alimento-id").value;
        const fileInput = document.getElementById("edit-alimento-imagen-file");
        const newFile = fileInput.files[0];

        const datosTexto = {
            nombre: document.getElementById("edit-alimento-nombre").value,
            categoria: document.getElementById("edit-alimento-categoria").value,
            calorias_por_100g: parseFloat(document.getElementById("edit-alimento-calorias").value),
            proteinas_por_100g: parseFloat(document.getElementById("edit-alimento-proteinas").value),
            carbohidratos_por_100g: parseFloat(document.getElementById("edit-alimento-carbohidratos").value),
            grasas_por_100g: parseFloat(document.getElementById("edit-alimento-grasas").value),
            precio_unitario: parseFloat(document.getElementById("edit-alimento-precio").value || 0),
            stock_actual: parseInt(document.getElementById("edit-alimento-stock").value || 0)
        };

        fetch(`${ALIMENTO_BASE_URL}${alimentoId}`, {
            method: 'PATCH',
            headers: AUTH_HEADERS,
            body: JSON.stringify(datosTexto)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(error => { throw new Error(error.detail || 'Error al actualizar.'); });
            }
            return response.json();
        })
        .then(async () => {
            if (newFile) {
                const imageFormData = new FormData();
                imageFormData.append("imagen", newFile);
                await fetch(`${ALIMENTO_BASE_URL}${alimentoId}/upload-image`, {
                    method: 'POST',
                    body: imageFormData,
                    headers: { 'Authorization': `Bearer ${TOKEN}` }
                });
            }
            modalEditar.hide();
            Swal.fire({
                icon: 'success',
                title: '¡Actualizado!',
                text: 'Cambios guardados correctamente.',
                timer: 1500,
                showConfirmButton: false,
                confirmButtonColor: '#4CAF50'
            });
            cargarAlimentos();
        })
        .catch(error => {
            Swal.fire('Error', error.message, 'error');
        });
    });
});