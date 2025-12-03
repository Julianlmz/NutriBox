document.addEventListener("DOMContentLoaded", function() {

    const loginForm = document.getElementById("login-form");

    loginForm.addEventListener("submit", function(event) {

        event.preventDefault();

        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);

        const backendURL = "/auth/token";

        // ✅ AGREGADO: Mostrar loading
        Swal.fire({
            title: 'Iniciando sesión...',
            allowOutsideClick: false,
            didOpen: () => { Swal.showLoading() }
        });

        fetch(backendURL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData,
        })
        .then(response => {
            console.log("Status:", response.status); // ✅ DEBUGGING
            if (response.ok) {
                return response.json();
            } else {
                return response.json().then(error => {
                    throw new Error(error.detail || 'Error de autenticación');
                });
            }
        })
        .then(data => {
            console.log("Token recibido:", data.access_token); // ✅ DEBUGGING

            localStorage.setItem("access_token", data.access_token);

            Swal.fire({
                icon: 'success',
                title: '¡Bienvenido!',
                text: 'Has iniciado sesión correctamente.',
                timer: 2000,
                showConfirmButton: false
            }).then(() => {
                window.location.href = "dashboard.html";
            });
        })
        .catch(error => {
            console.error('Error completo:', error); // ✅ DEBUGGING
            Swal.fire({
                icon: 'error',
                title: 'Error al iniciar sesión',
                text: 'Usuario o contraseña incorrectos. Inténtalo de nuevo.',
            });
        });
    });
});