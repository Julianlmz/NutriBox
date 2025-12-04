// loncheras.js
const API_URL = 'http://127.0.0.1:8000';

document.addEventListener('DOMContentLoaded', () => {
    cargarLoncheras();
});

// Cargar loncheras del usuario
async function cargarLoncheras() {
    try {
        const token = localStorage.getItem('access_token');
        const userId = localStorage.getItem('user_id');

        if (!token || !userId) {
            console.error("No hay sesión activa");
            window.location.href = 'login.html';
            return;
        }

        const response = await fetch(`${API_URL}/usuarios/${userId}/loncheras`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            let loncheras = await response.json();

            // Ordenar por fecha descendente
            loncheras.sort((a, b) => new Date(b.fecha_creacion) - new Date(a.fecha_creacion));

            renderizarLoncheras(loncheras);
        } else {
            const errorText = await response.text();
            console.error('Error response:', errorText);
            mostrarError();
        }
    } catch (error) {
        console.error('Error al cargar loncheras:', error);
        mostrarError();
    }
}

// Renderizar lista de loncheras
function renderizarLoncheras(loncheras) {
    const container = document.getElementById('lista-loncheras');

    if (loncheras.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon"><i class="fas fa-box-open"></i></div>
                <h4 class="empty-title">No tienes loncheras creadas</h4>
                <p class="empty-subtitle">Crea tu primera lonchera nutritiva para tus hijos</p>
                <a href="crear-lonchera.html" class="btn-nueva-lonchera">
                    <i class="fas fa-plus-circle"></i> Crear Primera Lonchera
                </a>
            </div>
        `;
        return;
    }

    container.innerHTML = loncheras.map(lonchera => {
        const fechaObj = new Date(lonchera.fecha_creacion);
        const fecha = isNaN(fechaObj.getTime()) ? 'Fecha desconocida' : fechaObj.toLocaleDateString('es-CO', {
            year: 'numeric', month: 'long', day: 'numeric'
        });

        return `
            <div class="lonchera-card">
                <div class="lonchera-header">
                    <div>
                        <h3 class="lonchera-title">${lonchera.nombre}</h3>
                        <p class="lonchera-date"><i class="fas fa-calendar me-2"></i>${fecha}</p>
                    </div>
                </div>
                
                <p class="lonchera-descripcion" style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; margin-bottom: 1.5rem;">
                    ${lonchera.descripcion || 'Sin descripción'}
                </p>
                
                <div class="lonchera-actions">
                    <button class="btn-action btn-ver" onclick="verDetalle(${lonchera.id})">
                        <i class="fas fa-eye me-1"></i> Ver Detalle
                    </button>
                    <button class="btn-action btn-eliminar" onclick="eliminarLonchera(${lonchera.id})">
                        <i class="fas fa-trash me-1"></i> Eliminar
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Ver detalle de lonchera
async function verDetalle(loncheraId) {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL}/loncheras/${loncheraId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const lonchera = await response.json();
            const alimentos = lonchera.alimentos || [];

            let alimentosHTML = '';
            if (alimentos.length > 0) {
                alimentosHTML = alimentos.map(a => `
                    <div style="padding: 10px; border-bottom: 1px solid #eee; display: flex; align-items: center;">
                        <div style="width: 40px; height: 40px; background: #f0f0f0; border-radius: 8px; margin-right: 10px; display: flex; align-items: center; justify-content: center;">
                            <i class="fas fa-apple-alt text-muted"></i>
                        </div>
                        <div>
                            <strong>${a.nombre_alimento || 'Alimento'}</strong><br>
                            <small style="color: #7f8c8d;">
                                ${a.cantidad_gramos}g • 
                                ${Math.round(a.calorias_porcion)} cal • 
                                $${a.precio_porcion.toFixed(2)}
                            </small>
                        </div>
                    </div>
                `).join('');
            } else {
                alimentosHTML = '<p style="color: #7f8c8d; text-align: center; padding: 1rem;">No hay alimentos registrados en esta lonchera</p>';
            }

            // AQUÍ ES DONDE AHORA SE MUESTRA LA INFORMACIÓN IMPORTANTE
            Swal.fire({
                title: lonchera.nombre,
                html: `
                    <div style="text-align: left;">
                        <p style="color: #7f8c8d; margin-bottom: 1rem;">${lonchera.descripcion || 'Sin descripción'}</p>
                        
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem;">
                            <div style="background: #fff3e0; padding: 0.8rem; border-radius: 10px; text-align: center;">
                                <div style="font-size: 1.2rem; font-weight: 700; color: #f57c00;">${lonchera.calorias}</div>
                                <div style="font-size: 0.7rem; color: #7f8c8d;">Calorías</div>
                            </div>
                            <div style="background: #e8f5e9; padding: 0.8rem; border-radius: 10px; text-align: center;">
                                <div style="font-size: 1.2rem; font-weight: 700; color: #388e3c;">$${lonchera.precio.toFixed(2)}</div>
                                <div style="font-size: 0.7rem; color: #7f8c8d;">Precio</div>
                            </div>
                            <div style="background: #e3f2fd; padding: 0.8rem; border-radius: 10px; text-align: center;">
                                <div style="font-size: 1.2rem; font-weight: 700; color: #1976d2;">${alimentos.length}</div>
                                <div style="font-size: 0.7rem; color: #7f8c8d;">Items</div>
                            </div>
                        </div>

                        <h5 style="margin-bottom: 1rem; color: #2c3e50; font-size: 1rem; font-weight: 600;">Contenido:</h5>
                        <div style="max-height: 250px; overflow-y: auto; background: #f9f9f9; border-radius: 10px; padding: 10px;">
                            ${alimentosHTML}
                        </div>
                    </div>
                `,
                width: 500,
                confirmButtonColor: '#4CAF50',
                confirmButtonText: 'Cerrar'
            });
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire('Error', 'No se pudo cargar el detalle', 'error');
    }
}

// Eliminar lonchera
async function eliminarLonchera(loncheraId) {
    const result = await Swal.fire({
        title: '¿Eliminar lonchera?',
        text: 'Esta acción no se puede deshacer',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#c62828',
        cancelButtonColor: '#95a5a6',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    });

    if (!result.isConfirmed) return;

    try {
        Swal.fire({
            title: 'Eliminando...',
            allowOutsideClick: false,
            didOpen: () => Swal.showLoading()
        });

        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL}/loncheras/${loncheraId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        Swal.close();

        if (response.ok) {
            Swal.fire({
                icon: 'success',
                title: 'Eliminada',
                text: 'La lonchera ha sido eliminada',
                timer: 1500,
                showConfirmButton: false
            });
            cargarLoncheras();
        } else {
            throw new Error('Error al eliminar');
        }
    } catch (error) {
        Swal.close();
        console.error('Error:', error);
        Swal.fire('Error', 'No se pudo eliminar la lonchera', 'error');
    }
}

function mostrarError() {
    const container = document.getElementById('lista-loncheras');
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon" style="background: #ffebee;">
                <i class="fas fa-exclamation-triangle" style="color: #c62828;"></i>
            </div>
            <h4 class="empty-title">Error al cargar loncheras</h4>
            <p class="empty-subtitle">Por favor, intenta de nuevo más tarde</p>
            <button onclick="cargarLoncheras()" class="btn-nueva-lonchera" style="background: #c62828;">
                <i class="fas fa-sync me-2"></i> Reintentar
            </button>
        </div>
    `;
}