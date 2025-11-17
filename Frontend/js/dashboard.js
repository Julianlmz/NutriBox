// --- COPIA Y PEGA ESTE CÓDIGO EN frontend/js/dashboard.js ---

document.addEventListener("DOMContentLoaded", function() {

    // 1. Configurar el botón de cerrar sesión
    // (Usa la función de auth-guard.js)
    setupLogoutButton();
    // (Para el botón móvil en el sidebar)
    const mobileLogout = document.getElementById("logout-button-mobile");
    if (mobileLogout) {
        mobileLogout.addEventListener("click", () => {
             document.getElementById("logout-button").click();
        });
    }

    // 2. Buscar los datos del usuario para el "Bienvenido"
    fetch("http://127.0.0.1:8000/usuario/me", {
        method: 'GET',
        headers: AUTH_HEADERS
    })
    .then(response => {
        if (response.ok) { return response.json(); }
        else { throw new Error('Token inválido o expirado.'); }
    })
    .then(usuario => {
        document.getElementById("welcome-message").textContent = `¡Bienvenid@, ${usuario.nombre}!`;
    })
    .catch(gestionarErrorDeAutenticacion); // <-- Usa la función de error de auth-guard.js

});