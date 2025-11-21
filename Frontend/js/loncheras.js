// --- COPIA Y PEGA EL CÓDIGO DEL CRUD DE LONCHERAS AQUÍ ---

document.addEventListener("DOMContentLoaded", function() {

    // 1. Configurar botones de layout (del auth-guard.js)
    setupLogoutButton();
    const mobileLogout = document.getElementById("logout-button-mobile");
    if (mobileLogout) {
        mobileLogout.addEventListener("click", () => {
             document.getElementById("logout-button").click();
        });
    }

    // 2. Referencias del CRUD
    const listaDiv = document.getElementById("lista-loncheras");
    const modalElement = document.getElementById('modalEditarLonchera');
    const modalEditar = new bootstrap.Modal(modalElement);
    let currentUserId = null; // Lo necesitaremos para el 'Create'

    // 3. Obtener el ID del usuario (necesario para 'Crear')
    fetch("http://127.0.0.1:8000/usuario/me", { method: 'GET', headers: AUTH_HEADERS })
        .then(response => {
            if (response.ok) { return response.json(); }
            else { throw new Error('Token inválido.'); }
        })
        .then(usuario => {
            currentUserId = usuario.id;
            // Una vez que tenemos el ID del usuario, cargamos sus loncheras
            cargarLoncheras();
        })
        .catch(gestionarErrorDeAutenticacion);


    // ==============================================
    // FUNCIÓN 2: Cargar las loncheras (Read)
    // ==============================================
    function cargarLoncheras() {
        // ... (el resto del código es idéntico al que ya tenías) ...
        const loadingText = document.getElementById("loncheras-loading");

        if (loadingText) { loadingText.style.display = "block"; }
        listaDiv.innerHTML = "";

        fetch(`/lonchera/`, {
            method: 'GET',
            headers: AUTH_HEADERS
        })
        .then(response => {
            if (!response.ok) { throw new Error('Error al cargar loncheras'); }
            return response.json();
        })
        .then(loncheras => {
            if (loadingText) { loadingText.style.display = "none"; }
            if (loncheras.length === 0) {
                listaDiv.innerHTML = '<p class="text-muted text-center">Aún no has creado ninguna lonchera.</p>';
                return;
            }
            loncheras.forEach(lonchera => {
                const loncheraCard = document.createElement('div');
                loncheraCard.className = 'card mb-3';
                loncheraCard.innerHTML = `
                    <div class="card-body d-flex justify-content-between align-items-center">
                        <div>
                            <h5 class="card-title mb-1">${lonchera.nombre}</h5>
                            <p class="card-text text-muted small">${lonchera.descripcion}</p>
                        </div>
                        <div>
                            <button class="btn btn-sm btn-outline-primary btn-editar" 
                                    data-id="${lonchera.id}" 
                                    data-nombre="${lonchera.nombre}" 
                                    data-descripcion="${lonchera.descripcion}">
                                Editar
                            </button>
                            <button class="btn btn-sm btn-outline-danger btn-borrar" data-id="${lonchera.id}">
                                Borrar
                            </button>
                        </div>
                    </div>
                `;
                listaDiv.appendChild(loncheraCard);
            });
        })
        .catch(error => {
            console.error("Error al cargar loncheras:", error);
            if (loadingText) { loadingText.textContent = "Error al cargar las loncheras."; }
        });
    }

    // ==============================================
    // FUNCIÓN 3: Crear una lonchera (Create)
    // ==============================================
    const formCrearLonchera = document.getElementById("form-crear-lonchera");
    formCrearLonchera.addEventListener("submit", function(event) {
        // ... (código idéntico al que ya tenías) ...
        event.preventDefault();
        const nombre = document.getElementById("lonchera-nombre").value;
        const descripcion = document.getElementById("lonchera-descripcion").value;

        const datosLonchera = {
            nombre: nombre,
            descripcion: descripcion,
            usuario_id: currentUserId,
        };

        fetch("http://127.0.0.1:8000/lonchera/", {
            method: 'POST',
            headers: AUTH_HEADERS,
            body: JSON.stringify(datosLonchera)
        })
        .then(response => {
            if (response.ok) { return response.json(); }
            else { throw new Error('Error al crear la lonchera.'); }
        })
        .then(nuevaLonchera => {
            Swal.fire('¡Creada!', `Se ha creado la lonchera "${nuevaLonchera.nombre}".`, 'success');
            formCrearLonchera.reset();
            cargarLoncheras();
        })
        .catch(error => {
            Swal.fire('Oops...', 'No se pudo crear la lonchera. Inténtalo de nuevo.', 'error');
        });
    });

    // ==============================================
    // Lógica de Click (Delete y Update)
    // ==============================================
    listaDiv.addEventListener("click", function(event) {
        // ... (código idéntico al que ya tenías) ...
        if (event.target.classList.contains("btn-borrar")) {
            const loncheraId = event.target.dataset.id;
            gestionarClickDeBorrado(loncheraId);
        }
        if (event.target.classList.contains("btn-editar")) {
            const loncheraId = event.target.dataset.id;
            const nombre = event.target.dataset.nombre;
            const descripcion = event.target.dataset.descripcion;

            document.getElementById("edit-lonchera-id").value = loncheraId;
            document.getElementById("edit-lonchera-nombre").value = nombre;
            document.getElementById("edit-lonchera-descripcion").value = descripcion;

            modalEditar.show();
        }
    });

    // ==============================================
    // FUNCIÓN 4: Borrar una lonchera (Delete)
    // ==============================================
    function gestionarClickDeBorrado(loncheraId) {
        // ... (código idéntico al que ya tenías) ...
        Swal.fire({
            title: '¿Estás seguro?',
            text: "No podrás revertir esto (será desactivada).",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: '¡Sí, bórrala!',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                fetch(`http://127.0.0.1:8000/lonchera/${loncheraId}`, {
                    method: 'DELETE',
                    headers: AUTH_HEADERS
                })
                .then(response => {
                    if (response.status === 204) { return; }
                    else { throw new Error('Error al borrar la lonchera.'); }
                })
                .then(() => {
                    Swal.fire('¡Borrada!', 'Tu lonchera ha sido desactivada.', 'success');
                    cargarLoncheras();
                })
                .catch(error => {
                    Swal.fire('Oops...', 'No se pudo borrar la lonchera.', 'error');
                });
            }
        });
    }

    // ==============================================
    // FUNCIÓN 5: Guardar Cambios (Update)
    // ==============================================
    const formEditarLonchera = document.getElementById("form-editar-lonchera");
    formEditarLonchera.addEventListener("submit", function(event) {
        // ... (código idéntico al que ya tenías) ...
        event.preventDefault();

        const loncheraId = document.getElementById("edit-lonchera-id").value;
        const nombre = document.getElementById("edit-lonchera-nombre").value;
        const descripcion = document.getElementById("edit-lonchera-descripcion").value;

        const datosActualizados = {
            nombre: nombre,
            descripcion: descripcion
        };

        fetch(`http://127.0.0.1:8000/lonchera/${loncheraId}`, {
            method: 'PATCH',
            headers: AUTH_HEADERS,
            body: JSON.stringify(datosActualizados)
        })
        .then(response => {
            if (response.ok) { return response.json(); }
            else { throw new Error('Error al actualizar la lonchera.'); }
        })
        .then(loncheraActualizada => {
            modalEditar.hide();
            Swal.fire('¡Actualizada!', `Lonchera "${loncheraActualizada.nombre}" guardada.`, 'success');
            cargarLoncheras();
        })
        .catch(error => {
            Swal.fire('Oops...', 'No se pudo actualizar la lonchera.', 'error');
        });
    });

});