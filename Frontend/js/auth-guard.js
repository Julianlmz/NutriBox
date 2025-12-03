const TOKEN = localStorage.getItem("access_token");
const AUTH_HEADERS = new Headers();
AUTH_HEADERS.append("Authorization", `Bearer ${TOKEN}`);
AUTH_HEADERS.append("Content-Type", "application/json");

console.log("Token encontrado:", TOKEN ? "Sí" : "No");

(function () {
    if (!TOKEN) {
        console.error("No hay token. Redirigiendo al login.");
        window.location.href = "login.html";
    } else {
        console.log("Token válido, continuando...");
    }
})();

function setupLogoutButton() {
    const logoutButton = document.getElementById("logout-button");
    if (logoutButton) {
        logoutButton.addEventListener("click", function() {
            localStorage.removeItem("access_token");
            Swal.fire({
                icon: 'success',
                title: '¡Hasta luego!',
                timer: 1500,
                showConfirmButton: false
            })
            .then(() => { window.location.href = "login.html"; });
        });
    }
}

function gestionarErrorDeAutenticacion(error) {
    console.error("Error de autenticación:", error.message);
    console.error("Stack completo:", error); // ✅ Más info
    localStorage.removeItem("access_token");
    Swal.fire({
        icon: 'error',
        title: 'Sesión Expirada',
        text: 'Por favor, inicia sesión de nuevo.'
    })
    .then(() => { window.location.href = "login.html"; });
}