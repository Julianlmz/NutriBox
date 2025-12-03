// dashboard.js
const API_URL = 'http://127.0.0.1:8000';

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
        const userNameElement = document.getElementById("userName");
        if (userNameElement) {
            userNameElement.textContent = usuario.nombre;
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

        // Mostrar loading en las tarjetas
        const totalHijos = document.getElementById('total-hijos');
        const totalLoncheras = document.getElementById('total-loncheras');
        const totalDirecciones = document.getElementById('total-direcciones');

        if (totalHijos) totalHijos.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        if (totalLoncheras) totalLoncheras.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        if (totalDirecciones) totalDirecciones.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        // Cargar datos en paralelo
        const [hijosRes, loncherasRes, direccionesRes] = await Promise.all([
            fetch(`${API_URL}/hijo/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            }),
            fetch(`${API_URL}/lonchera/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            }),
            fetch(`${API_URL}/direccion/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            })
        ]);

        const hijos = hijosRes.ok ? await hijosRes.json() : [];
        const loncheras = loncherasRes.ok ? await loncherasRes.json() : [];
        const direcciones = direccionesRes.ok ? await direccionesRes.json() : [];

        // Actualizar contadores con animación
        if (totalHijos) animarContador(totalHijos, hijos.length);
        if (totalLoncheras) animarContador(totalLoncheras, loncheras.length);
        if (totalDirecciones) animarContador(totalDirecciones, direcciones.length);

        // También actualizar IDs antiguos si existen
        const totalHijosOld = document.getElementById("totalHijos");
        const totalLoncherasOld = document.getElementById("totalLoncheras");
        const totalDireccionesOld = document.getElementById("totalDirecciones");
        
        if (totalHijosOld) totalHijosOld.textContent = hijos.length;
        if (totalLoncherasOld) totalLoncherasOld.textContent = loncheras.length;
        if (totalDireccionesOld) totalDireccionesOld.textContent = direcciones.length;

    } catch (error) {
        console.error('Error al cargar estadísticas:', error);
        
        // Mostrar 0 en caso de error
        const totalHijos = document.getElementById('total-hijos');
        const totalLoncheras = document.getElementById('total-loncheras');
        const totalDirecciones = document.getElementById('total-direcciones');
        
        if (totalHijos) totalHijos.textContent = '0';
        if (totalLoncheras) totalLoncheras.textContent = '0';
        if (totalDirecciones) totalDirecciones.textContent = '0';
    }
}

// Animar contador
function animarContador(elemento, valorFinal) {
    let valorActual = 0;
    const duracion = 1000;
    const incremento = valorFinal / (duracion / 16);

    const intervalo = setInterval(() => {
        valorActual += incremento;
        if (valorActual >= valorFinal) {
            elemento.textContent = valorFinal;
            clearInterval(intervalo);
        } else {
            elemento.textContent = Math.floor(valorActual);
        }
    }, 16);
}