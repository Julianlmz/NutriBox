// dashboard.js
const API_URL = '';

document.addEventListener("DOMContentLoaded", function() {
    setupLogoutButton();

    const mobileLogout = document.getElementById("logout-button-mobile");
    if (mobileLogout) {
        mobileLogout.addEventListener("click", () => {
            document.getElementById("logout-button").click();
        });
    }

    // Cargar datos del usuario
    const token = localStorage.getItem('access_token');
    fetch(`${API_URL}/usuario/me`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Token inválido o expirado.');
        }
    })
    .then(usuario => {
        // 1. Actualizar nombre en el Navbar (si existe)
        const userNameElement = document.getElementById("userName");
        if (userNameElement) {
            userNameElement.textContent = usuario.nombre;
        }

        // 2. CAMBIO PRINCIPAL: Actualizar el Título Grande "Dashboard"
        const pageTitle = document.getElementById("page-title");
        if (pageTitle) {
            // Capitalizar primera letra por estética
            const nombre = usuario.nombre.charAt(0).toUpperCase() + usuario.nombre.slice(1);
            pageTitle.textContent = `Bienvenid@, ${nombre}`;
        }

        // Cargar estadísticas reales
        cargarEstadisticas();
    })
    .catch(error => {
        console.error('Error:', error);
        if (typeof gestionarErrorDeAutenticacion === 'function') {
            gestionarErrorDeAutenticacion(error);
        }
    });
});

async function cargarEstadisticas() {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) return;

        // Elementos del DOM
        const totalHijos = document.getElementById('total-hijos');
        const totalLoncheras = document.getElementById('total-loncheras');
        const totalDirecciones = document.getElementById('total-direcciones');

        // Mostrar loading
        if (totalHijos) totalHijos.innerHTML = '<i class="fas fa-spinner fa-spin" style="font-size: 1.5rem"></i>';
        if (totalLoncheras) totalLoncheras.innerHTML = '<i class="fas fa-spinner fa-spin" style="font-size: 1.5rem"></i>';
        if (totalDirecciones) totalDirecciones.innerHTML = '<i class="fas fa-spinner fa-spin" style="font-size: 1.5rem"></i>';

        // Peticiones
        const [hijosRes, loncherasRes, direccionesRes] = await Promise.all([
            fetch(`${API_URL}/hijo/`, { headers: { 'Authorization': `Bearer ${token}` } }),
            fetch(`${API_URL}/lonchera/`, { headers: { 'Authorization': `Bearer ${token}` } }),
            fetch(`${API_URL}/direcciones/?usuario_id=${localStorage.getItem('user_id')}`, { headers: { 'Authorization': `Bearer ${token}` } }) // Corrección en URL direcciones
        ]);

        const hijos = hijosRes.ok ? await hijosRes.json() : [];
        const loncheras = loncherasRes.ok ? await loncherasRes.json() : [];
        const direcciones = direccionesRes.ok ? await direccionesRes.json() : [];

        // Actualizar contadores
        if (totalHijos) animarContador(totalHijos, hijos.length);
        if (totalLoncheras) animarContador(totalLoncheras, loncheras.length);
        if (totalDirecciones) animarContador(totalDirecciones, direcciones.length);

    } catch (error) {
        console.error('Error al cargar estadísticas:', error);
    }
}

// Función de animación simple
function animarContador(elemento, valorFinal) {
    elemento.textContent = valorFinal; // Actualización directa para evitar parpadeos
}