document.addEventListener("DOMContentLoaded", async function() {
    if(typeof setupLogoutButton === 'function') setupLogoutButton();
    await cargarRestricciones();

    const form = document.getElementById("form-restriccion");
    if (form) {
        form.addEventListener("submit", async function(e) {
            e.preventDefault();
            const data = {
                nombre: document.getElementById("nombre-restriccion").value,
                descripcion: document.getElementById("descripcion-restriccion").value,
                nivel_severidad: document.getElementById("severidad-restriccion").value
            };

            try {
                const response = await fetch("/restriccion/", {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${localStorage.getItem("access_token")}`, 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    Swal.fire({ icon: 'success', title: '¡Guardada!', timer: 1500, showConfirmButton: false });
                    bootstrap.Modal.getInstance(document.getElementById('modalRestriccion')).hide();
                    form.reset();
                    await cargarRestricciones();
                } else { throw new Error('Error'); }
            } catch (error) { Swal.fire('Error', 'No se pudo guardar', 'error'); }
        });
    }
});

async function cargarRestricciones() {
    try {
        const response = await fetch("/restriccion/", { headers: { 'Authorization': `Bearer ${localStorage.getItem("access_token")}` } });
        if (!response.ok) return;

        const restricciones = await response.json();
        const container = document.getElementById("lista-restricciones");

        if(restricciones.length === 0) {
            container.innerHTML = `<div class="col-12 text-center py-5"><i class="fas fa-shield-alt fa-3x text-muted mb-3 opacity-25"></i><p class="text-muted">No hay restricciones</p></div>`;
            return;
        }

        // AQUÍ ESTÁ EL CAMBIO: Clases fijas de estilo rojo
        container.innerHTML = restricciones.map(r => `
            <div class="col-md-6 col-lg-4">
                <div class="bg-white p-4 rounded-4 shadow-sm border-start border-danger border-4 h-100 position-relative">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <h5 class="fw-bold mb-0 text-danger">${r.nombre}</h5>
                        <span class="badge bg-${r.nivel_severidad === 'Alto' ? 'danger' : r.nivel_severidad === 'Medio' ? 'warning' : 'info'}">${r.nivel_severidad}</span>
                    </div>
                    <p class="text-muted small mb-0">${r.descripcion || 'Sin descripción'}</p>
                    <button onclick="eliminarRestriccion(${r.id})" class="btn btn-sm text-secondary position-absolute bottom-0 end-0 m-2"><i class="fas fa-trash-alt"></i></button>
                </div>
            </div>
        `).join("");

    } catch (error) { console.error(error); }
}

async function eliminarRestriccion(id) {
    if((await Swal.fire({ title: '¿Eliminar?', icon: 'warning', showCancelButton: true, confirmButtonColor: '#d33' })).isConfirmed) {
        await fetch(`/restriccion/${id}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${localStorage.getItem("access_token")}` } });
        await cargarRestricciones();
        Swal.fire('Eliminado', '', 'success');
    }
}