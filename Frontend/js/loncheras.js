document.addEventListener("DOMContentLoaded", function() {

    setupLogoutButton();
    const mobileLogout = document.getElementById("logout-button-mobile");
    if (mobileLogout) {
        mobileLogout.addEventListener("click", () => {
             document.getElementById("logout-button").click();
        });
    }

    const listaDiv = document.getElementById("lista-loncheras");
    const modalElement = document.getElementById('modalEditarLonchera');
    const modalEditar = new bootstrap.Modal(modalElement);
    let currentUserId = null;

    // CORRECCIÓN: Ruta relativa
    fetch("/usuario/me", { method: 'GET', headers: AUTH_HEADERS })
        .then(response => {
            if (response.ok) { return response.json(); }
            else { throw new Error('Token inválido.'); }
        })
        .then(usuario => {
            currentUserId = usuario.id;
            cargarLoncheras();
        })
        .catch(gestionarErrorDeAutenticacion);

    function cargarLoncheras() {
        const loadingText = document.getElementById("lista-loncheras");
        // (Usamos listaDiv temporalmente para mostrar loading o limpiar)

        // CORRECCIÓN: Ruta relativa
        fetch("/lonchera/", {
            method: 'GET',
            headers: AUTH_HEADERS
        })
        .then(response => {
            if (!response.ok) { throw new Error('Error al cargar loncheras'); }
            return response.json();
        })
        .then(loncheras => {
            listaDiv.innerHTML = ""; // Limpiar lista
            if (loncheras.length === 0) {
                listaDiv.innerHTML = '<div class="text-center text-muted py-5"><i class="fas fa-box-open fa-3x mb-3 opacity-25"></i><p>Aún no tienes loncheras.</p></div>';
                return;
            }
            loncheras.forEach(lonchera => {
                const loncheraCard = document.createElement('div');
                loncheraCard.className = 'card-lonchera-item'; // Usamos la clase CSS nueva
                loncheraCard.innerHTML = `
                    <div>
                        <h5 class="mb-1 fw-bold text-dark">${lonchera.nombre}</h5>
                        <p class="mb-0 text-muted small text-truncate" style="max-width: 250px;">${lonchera.descripcion}</p>
                    </div>
                    <div class="d-flex gap-2">
                        <button class="btn btn-action btn-outline-primary btn-editar" 
                                data-id="${lonchera.id}" 
                                data-nombre="${lonchera.nombre}" 
                                data-descripcion="${lonchera.descripcion}">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-action btn-outline-danger btn-borrar" data-id="${lonchera.id}">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                `;
                listaDiv.appendChild(loncheraCard);
            });
        })
        .catch(error => {
            console.error("Error:", error);
            listaDiv.innerHTML = '<p class="text-center text-danger">Error al cargar.</p>';
        });
    }

    const formCrearLonchera = document.getElementById("form-crear-lonchera");
    formCrearLonchera.addEventListener("submit", function(event) {
        event.preventDefault();
        const nombre = document.getElementById("lonchera-nombre").value;
        const descripcion = document.getElementById("lonchera-descripcion").value;

        const datosLonchera = {
            nombre: nombre,
            descripcion: descripcion,
            usuario_id: currentUserId,
        };

        // CORRECCIÓN: Ruta relativa
        fetch("/lonchera/", {
            method: 'POST',
            headers: AUTH_HEADERS,
            body: JSON.stringify(datosLonchera)
        })
        .then(response => {
            if (response.ok) { return response.json(); }
            else { throw new Error('Error al crear.'); }
        })
        .then(nuevaLonchera => {
            Swal.fire({
                icon: 'success',
                title: '¡Creada!',
                text: `Lonchera "${nuevaLonchera.nombre}" lista.`,
                confirmButtonColor: '#4CAF50'
            });
            formCrearLonchera.reset();
            cargarLoncheras();
        })
        .catch(error => {
            Swal.fire('Error', 'No se pudo crear la lonchera.', 'error');
        });
    });

    listaDiv.addEventListener("click", function(event) {
        const btnBorrar = event.target.closest(".btn-borrar");
        const btnEditar = event.target.closest(".btn-editar");

        if (btnBorrar) {
            const loncheraId = btnBorrar.dataset.id;
            gestionarClickDeBorrado(loncheraId);
        }
        if (btnEditar) {
            const loncheraId = btnEditar.dataset.id;
            const nombre = btnEditar.dataset.nombre;
            const descripcion = btnEditar.dataset.descripcion;

            document.getElementById("edit-lonchera-id").value = loncheraId;
            document.getElementById("edit-lonchera-nombre").value = nombre;
            document.getElementById("edit-lonchera-descripcion").value = descripcion;

            modalEditar.show();
        }
    });

    function gestionarClickDeBorrado(loncheraId) {
        Swal.fire({
            title: '¿Borrar lonchera?',
            text: "Desaparecerá de tu lista.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#f8f9fa',
            cancelButtonText: '<span style="color:#555">Cancelar</span>',
            confirmButtonText: 'Sí, borrar'
        }).then((result) => {
            if (result.isConfirmed) {
                // CORRECCIÓN: Ruta relativa
                fetch(`/lonchera/${loncheraId}`, {
                    method: 'DELETE',
                    headers: AUTH_HEADERS
                })
                .then(response => {
                    if (response.status === 204) { return; }
                    else { throw new Error('Error al borrar.'); }
                })
                .then(() => {
                    Swal.fire({
                        icon: 'success',
                        title: '¡Borrada!',
                        showConfirmButton: false,
                        timer: 1000
                    });
                    cargarLoncheras();
                })
                .catch(error => {
                    Swal.fire('Error', 'No se pudo borrar.', 'error');
                });
            }
        });
    }

    const formEditarLonchera = document.getElementById("form-editar-lonchera");
    formEditarLonchera.addEventListener("submit", function(event) {
        event.preventDefault();

        const loncheraId = document.getElementById("edit-lonchera-id").value;
        const nombre = document.getElementById("edit-lonchera-nombre").value;
        const descripcion = document.getElementById("edit-lonchera-descripcion").value;

        const datosActualizados = {
            nombre: nombre,
            descripcion: descripcion
        };

        // CORRECCIÓN: Ruta relativa
        fetch(`/lonchera/${loncheraId}`, {
            method: 'PATCH',
            headers: AUTH_HEADERS,
            body: JSON.stringify(datosActualizados)
        })
        .then(response => {
            if (response.ok) { return response.json(); }
            else { throw new Error('Error al actualizar.'); }
        })
        .then(loncheraActualizada => {
            modalEditar.hide();
            Swal.fire({
                icon: 'success',
                title: '¡Actualizado!',
                showConfirmButton: false,
                timer: 1000
            });
            cargarLoncheras();
        })
        .catch(error => {
            Swal.fire('Error', 'No se pudo actualizar.', 'error');
        });
    });
});