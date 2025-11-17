// --- COPIA Y PEGA TODO ESTE CÓDIGO EN frontend/js/alimentos.js ---

document.addEventListener("DOMContentLoaded", function() {

    // 1. Setup inicial
    setupLogoutButton();
    const mobileLogout = document.getElementById("logout-button-mobile");
    if (mobileLogout) {
        mobileLogout.addEventListener("click", () => {
             document.getElementById("logout-button").click();
        });
    }

    // El endpoint base para Alimentos
    const ALIMENTO_BASE_URL = "http://127.0.0.1:8000/alimento/";

    // Referencias a elementos del DOM
    const listaDiv = document.getElementById("lista-alimentos");
    const modalElement = document.getElementById('modalEditarAlimento');
    const modalEditar = new bootstrap.Modal(modalElement);
    const formCrearAlimento = document.getElementById("form-crear-alimento");
    const formEditarAlimento = document.getElementById("form-editar-alimento");

    // Datos de la categoría (simulamos el Enum del backend)
    const CATEGORIAS = [
        "Frutas", "Vegetales", "Proteínas", "Lácteos", "Cereales", "Snacks", "Bebidas"
    ];

    // CORRECCIÓN: Llenamos selectores inmediatamente
    llenarSelectoresCategoria();

    // Llenar los selectores de Categoría
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

    // Llamada inicial para cargar el nombre del usuario y la lista de alimentos
    fetch("http://127.0.0.1:8000/usuario/me", { method: 'GET', headers: AUTH_HEADERS })
        .then(response => {
            if (response.ok) { return response.json(); }
            else { throw new Error('Token inválido o expirado.'); }
        })
        .then(usuario => {
            document.getElementById("alimentos-loading").textContent = `Bienvenido, ${usuario.nombre}. Cargando alimentos...`;
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
                listaDiv.innerHTML = '<p class="text-muted text-center">Aún no hay alimentos en el inventario.</p>';
                return;
            }

            alimentos.forEach(alimento => {
                const card = document.createElement('div');
                card.className = 'card mb-3';

                // ⭐️ LÓGICA DE IMAGEN Y ESTRUCTURA CORREGIDA ⭐️
                const imageUrl = alimento.imagen_url || 'https://via.placeholder.com/60/4CAF50/FFFFFF?text=N';

                card.innerHTML = `
                    <div class="card-body d-flex align-items-center p-3">
                        <img src="${imageUrl}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px;" class="me-3" alt="${alimento.nombre}">
                        
                        <div class="flex-grow-1">
                            <h5 class="card-title mb-0">${alimento.nombre}</h5>
                            <p class="card-text small text-muted mb-1">
                                <i class="fas fa-tag me-1"></i>${alimento.categoria} | 
                                <i class="fas fa-fire me-1"></i>${alimento.calorias_por_100g} Cal
                            </p>
                            <p class="card-text small mb-0">Stock: ${alimento.stock_actual} | Precio: $${alimento.precio_unitario}</p>
                        </div>
                        
                        <div class="ms-auto btn-group">
                            <button class="btn btn-sm btn-outline-primary btn-editar-alimento me-2" 
                                    data-id="${alimento.id}">
                                Editar
                            </button>
                            <button class="btn btn-sm btn-outline-danger btn-borrar-alimento" data-id="${alimento.id}">
                                Borrar
                            </button>
                        </div>
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
    // FUNCIÓN 3: Crear Alimento (Create) - USANDO FORM DATA
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
        formData.append("precio_unitario", document.getElementById("alimento-precio").value);
        formData.append("stock_inicial", document.getElementById("alimento-stock").value);

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
            Swal.fire('¡Creado!', `Se ha añadido ${nuevoAlimento.nombre} al inventario.`, 'success');
            formCrearAlimento.reset();
            cargarAlimentos();
        })
        .catch(error => {
            Swal.fire('Oops...', `No se pudo crear el alimento: ${error.message}`, 'error');
        });
    });


    // ==============================================
    // FUNCIÓN 4: Borrar Alimento (Delete)
    // ==============================================
    listaDiv.addEventListener("click", function(event) {
        if (event.target.classList.contains("btn-borrar-alimento")) {
            const alimentoId = event.target.dataset.id;

            Swal.fire({
                title: '¿Estás seguro?',
                text: "Esto desactivará el alimento. No podrás revertirlo.",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Sí, ¡desactivar!'
            }).then((result) => {
                if (result.isConfirmed) {
                    fetch(`${ALIMENTO_BASE_URL}${alimentoId}`, {
                        method: 'DELETE',
                        headers: { 'Authorization': `Bearer ${TOKEN}` }
                    })
                    .then(response => {
                        if (response.status === 204) {
                            Swal.fire('¡Desactivado!', 'El alimento ha sido removido de la lista.', 'success');
                            cargarAlimentos();
                        } else {
                            throw new Error('Error al desactivar el alimento.');
                        }
                    })
                    .catch(error => {
                        Swal.fire('Oops...', 'No se pudo desactivar el alimento.', 'error');
                    });
                }
            });
        }
    });

    // ==============================================
    // FUNCIÓN 5: Editar Alimento (Update)
    // ==============================================

    // 5.1 Click en el botón Editar
    listaDiv.addEventListener("click", function(event) {
        if (event.target.classList.contains("btn-editar-alimento")) {
            const alimentoId = event.target.dataset.id;

            // 1. Obtener los datos del backend (GET)
            fetch(`${ALIMENTO_BASE_URL}${alimentoId}`, { method: 'GET', headers: AUTH_HEADERS })
                .then(response => response.json())
                .then(alimento => {
                    // 2. Rellenar el modal con los datos
                    document.getElementById("edit-alimento-id").value = alimento.id;
                    document.getElementById("edit-alimento-nombre").value = alimento.nombre;
                    document.getElementById("edit-alimento-categoria").value = alimento.categoria;
                    document.getElementById("edit-alimento-calorias").value = alimento.calorias_por_100g;
                    document.getElementById("edit-alimento-proteinas").value = alimento.proteinas_por_100g;
                    document.getElementById("edit-alimento-carbohidratos").value = alimento.carbohidratos_por_100g;
                    document.getElementById("edit-alimento-grasas").value = alimento.grasas_por_100g;
                    document.getElementById("edit-alimento-precio").value = alimento.precio_unitario;
                    document.getElementById("edit-alimento-stock").value = alimento.stock_actual;

                    // 3. Mostrar imagen actual
                    const preview = document.getElementById("edit-alimento-imagen-preview");
                    preview.src = alimento.imagen_url || 'https://via.placeholder.com/150/4CAF50/FFFFFF?text=Sin+Imagen';

                    // 4. Mostrar el modal
                    modalEditar.show();
                })
                .catch(error => {
                    Swal.fire('Error', 'No se pudieron cargar los datos del alimento.', 'error');
                });
        }
    });

    // 5.2 Enviar el formulario de Edición (PATCH + POST para imagen)
    formEditarAlimento.addEventListener("submit", function(event) {
        event.preventDefault();

        const alimentoId = document.getElementById("edit-alimento-id").value;
        const fileInput = document.getElementById("edit-alimento-imagen-file");
        const newFile = fileInput.files[0];

        // 1. Datos de texto (Usamos el mismo Content-Type que en loncheras para PATCH)
        const datosTexto = {
            nombre: document.getElementById("edit-alimento-nombre").value,
            categoria: document.getElementById("edit-alimento-categoria").value,
            calorias_por_100g: parseFloat(document.getElementById("edit-alimento-calorias").value),
            proteinas_por_100g: parseFloat(document.getElementById("edit-alimento-proteinas").value),
            carbohidratos_por_100g: parseFloat(document.getElementById("edit-alimento-carbohidratos").value),
            grasas_por_100g: parseFloat(document.getElementById("edit-alimento-grasas").value),
            precio_unitario: parseFloat(document.getElementById("edit-alimento-precio").value),
            stock_actual: parseInt(document.getElementById("edit-alimento-stock").value)
        };

        // 2. Ejecutar la actualización de texto
        fetch(`${ALIMENTO_BASE_URL}${alimentoId}`, {
            method: 'PATCH',
            headers: AUTH_HEADERS,
            body: JSON.stringify(datosTexto)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(error => { throw new Error(error.detail || 'Error al actualizar texto.'); });
            }
            return response.json();
        })
        .then(async () => {
            // 3. Si hay un archivo nuevo, subirlo (POST a /upload-image)
            if (newFile) {
                // Creamos un FormData solo para la imagen
                const imageFormData = new FormData();
                imageFormData.append("imagen", newFile);

                await fetch(`${ALIMENTO_BASE_URL}${alimentoId}/upload-image`, {
                    method: 'POST',
                    body: imageFormData,
                    headers: { 'Authorization': `Bearer ${TOKEN}` }
                });
            }

            // 4. Éxito final
            modalEditar.hide();
            Swal.fire('¡Actualizado!', 'Alimento guardado con éxito.', 'success');
            cargarAlimentos();
        })
        .catch(error => {
            Swal.fire('Oops...', `No se pudo actualizar: ${error.message}`, 'error');
        });
    });
});