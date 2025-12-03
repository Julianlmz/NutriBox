// loncheras.js
const API_URL = 'http://127.0.0.1:8000';

document.addEventListener('DOMContentLoaded', () => {
    cargarLoncheras();
});

// Cargar loncheras del usuario
async function cargarLoncheras() {
    try {
        const token = localStorage.getItem('access_token');
        console.log('Token:', token ? 'Existe' : 'No existe');

        // Obtener ID del usuario actual
        const userResponse = await fetch(`${API_URL}/usuario/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        let currentUserId = null;
        if (userResponse.ok) {
            const userData = await userResponse.json();
            currentUserId = userData.id;
            console.log('Usuario actual ID:', currentUserId);
        }

        const response = await fetch(`${API_URL}/lonchera/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);

        if (response.ok) {
            let loncheras = await response.json();
            console.log('Loncheras recibidas:', loncheras);

            // Si viene array vacío, intentar obtener todas sin filtro
            if (loncheras.length === 0) {
                console.log('No hay loncheras, intentando obtener todas...');
                // Aquí las loncheras están vacías porque el backend filtra por usuario_id del token
                // pero guardaste las loncheras con usuario_id = hijo_id
            }

            console.log('Cantidad de loncheras:', loncheras.length);
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
        const fecha = new Date(lonchera.fecha_creacion).toLocaleDateString('es-CO', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });

        return `
            <div class="lonchera-card">
                <div class="lonchera-header">
                    <div>
                        <h3 class="lonchera-title">${lonchera.nombre}</h3>
                        <p class="lonchera-date"><i class="fas fa-calendar me-2"></i>${fecha}</p>
                    </div>
                </div>
                
                <p class="lonchera-descripcion">${lonchera.descripcion || 'Sin descripción'}</p>
                
                <div class="lonchera-stats">
                    <div class="stat-item">
                        <div class="stat-icon calorias">
                            <i class="fas fa-fire"></i>
                        </div>
                        <div class="stat-content">
                            <div class="stat-value">${lonchera.calorias}</div>
                            <div class="stat-label">Calorías</div>
                        </div>
                    </div>
                    
                    <div class="stat-item">
                        <div class="stat-icon precio">
                            <i class="fas fa-dollar-sign"></i>
                        </div>
                        <div class="stat-content">
                            <div class="stat-value">$${lonchera.precio.toFixed(2)}</div>
                            <div class="stat-label">Precio</div>
                        </div>
                    </div>
                    
                    <div class="stat-item">
                        <div class="stat-icon alimentos">
                            <i class="fas fa-utensils"></i>
                        </div>
                        <div class="stat-content">
                            <div class="stat-value">${lonchera.alimentos?.length || 0}</div>
                            <div class="stat-label">Alimentos</div>
                        </div>
                    </div>
                </div>
                
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
        const response = await fetch(`${API_URL}/lonchera/${loncheraId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const lonchera = await response.json();

            // Obtener alimentos de la lonchera
            let alimentosHTML = '<p style="color: #7f8c8d; text-align: center; padding: 2rem;">No hay alimentos en esta lonchera</p>';

            try {
                const alimentosResponse = await fetch(`${API_URL}/lonchera/${loncheraId}/alimentos`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (alimentosResponse.ok) {
                    const alimentos = await alimentosResponse.json();

                    // Verificar si alimentos es un array y tiene elementos
                    if (Array.isArray(alimentos) && alimentos.length > 0) {
                        alimentosHTML = alimentos.map(a => `
                            <div style="padding: 10px; border-bottom: 1px solid #eee;">
                                <strong>${a.nombre_alimento || a.nombre || 'Alimento'}</strong><br>
                                <small style="color: #7f8c8d;">
                                    ${a.cantidad_gramos || 100}g • 
                                    ${Math.round(a.calorias_porcion || 0)} cal • 
                                    $${(a.precio_porcion || 0).toFixed(2)}
                                </small>
                            </div>
                        `).join('');
                    }
                }
            } catch (error) {
                console.error('Error al cargar alimentos:', error);
                alimentosHTML = '<p style="color: #f57c00; text-align: center; padding: 2rem;"><i class="fas fa-exclamation-triangle"></i> No se pudieron cargar los alimentos</p>';
            }

            Swal.fire({
                title: lonchera.nombre,
                html: `
                    <div style="text-align: left;">
                        <p style="color: #7f8c8d; margin-bottom: 1rem;">${lonchera.descripcion || 'Sin descripción'}</p>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem;">
                            <div style="background: #fff3e0; padding: 1rem; border-radius: 10px; text-align: center;">
                                <div style="font-size: 1.5rem; font-weight: 700; color: #f57c00;">${lonchera.calorias}</div>
                                <div style="font-size: 0.8rem; color: #7f8c8d;">Calorías</div>
                            </div>
                            <div style="background: #e8f5e9; padding: 1rem; border-radius: 10px; text-align: center;">
                                <div style="font-size: 1.5rem; font-weight: 700; color: #388e3c;">$${lonchera.precio.toFixed(2)}</div>
                                <div style="font-size: 0.8rem; color: #7f8c8d;">Precio</div>
                            </div>
                            <div style="background: #e3f2fd; padding: 1rem; border-radius: 10px; text-align: center;">
                                <div style="font-size: 1.5rem; font-weight: 700; color: #1976d2;">${lonchera.alimentos?.length || 0}</div>
                                <div style="font-size: 0.8rem; color: #7f8c8d;">Alimentos</div>
                            </div>
                        </div>
                        <h4 style="margin-bottom: 1rem; color: #2c3e50;">Alimentos:</h4>
                        <div style="max-height: 300px; overflow-y: auto;">
                            ${alimentosHTML}
                        </div>
                    </div>
                `,
                width: 600,
                confirmButtonColor: '#4CAF50',
                confirmButtonText: 'Cerrar'
            });
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire('Error', 'No se pudo cargar el detalle de la lonchera', 'error');
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
        const response = await fetch(`${API_URL}/lonchera/${loncheraId}`, {
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

// Mostrar error
function mostrarError() {
    const container = document.getElementById('lista-loncheras');
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon" style="background: #ffebee;">
                <i class="fas fa-exclamation-triangle" style="color: #c62828;"></i>
            </div>
            <h4 class="empty-title">Error al cargar loncheras</h4>
            <p class="empty-subtitle">Por favor, intenta de nuevo más tarde</p>
            <button onclick="cargarLoncheras()" class="btn-nueva-lonchera">
                <i class="fas fa-sync me-2"></i> Reintentar
            </button>
        </div>
    `;
}