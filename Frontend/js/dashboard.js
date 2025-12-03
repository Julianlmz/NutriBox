document.addEventListener("DOMContentLoaded", function() {

    setupLogoutButton();

    const mobileLogout = document.getElementById("logout-button-mobile");
    if (mobileLogout) {
        mobileLogout.addEventListener("click", () => {
             document.getElementById("logout-button").click();
        });
    }

    // 2. Buscar los datos del usuario
    fetch("/usuario/me", {
        method: 'GET',
        headers: AUTH_HEADERS
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Token inválido o expirado.');
        }
    })
    .then(usuario => {
        // ✅ CORRECCIÓN: Usar el ID correcto que existe en el HTML
        const userNameElement = document.getElementById("userName");
        if (userNameElement) {
            userNameElement.textContent = usuario.nombre;
        }

        // También actualizar contadores si existen
        const totalHijos = document.getElementById("totalHijos");
        const totalLoncheras = document.getElementById("totalLoncheras");
        const totalDirecciones = document.getElementById("totalDirecciones");

        if (totalHijos) totalHijos.textContent = "0"; // Puedes cargar datos reales aquí
        if (totalLoncheras) totalLoncheras.textContent = "0";
        if (totalDirecciones) totalDirecciones.textContent = "0";
    })
    .catch(gestionarErrorDeAutenticacion);

});