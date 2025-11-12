document.addEventListener("DOMContentLoaded", function() {

    // 1. Seleccionar el formulario
    const loginForm = document.getElementById("login-form");

    // 2. Escuchar el evento "submit"
    loginForm.addEventListener("submit", function(event) {

        // 3. Evitar el envío tradicional
        event.preventDefault();

        // 4. Obtener los valores
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        // 5. Preparar los datos para enviar al backend
        // ¡OJO! Para el login con OAuth2 de FastAPI,
        // se usa un formato especial, no JSON.
        const formData = new URLSearchParams();
        formData.append("username", email); // FastAPI espera "username", aunque usemos email
        formData.append("password", password);

        // 6. Definir la URL de tu backend
        // Esta suele ser diferente a la de crear usuario
        const backendURL = "https://nutribox.onrender.com/auth/token";

        // 7. Usar fetch() para enviar los datos
        fetch(backendURL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData, // Enviamos el objeto FormData
        })
        .then(response => {
            if (response.ok) {
                return response.json(); // Si el login es correcto
            } else {
                // Si el backend responde con un error (ej. 401 Unauthorized)
                return response.json().then(error => { throw new Error(error.detail || 'Error de autenticación'); });
            }
        })
        .then(data => {
            // ¡Éxito! El usuario inició sesión.

            // 8. Guardar el "token" de acceso
            // Este token es la "llave" que usaremos para todas las futuras peticiones
            localStorage.setItem("access_token", data.access_token);

            Swal.fire({
                icon: 'success',
                title: '¡Bienvenido!',
                text: 'Has iniciado sesión correctamente.',
                timer: 2000, // Se cierra solo después de 2 segundos
                showConfirmButton: false
            }).then(() => {
                // 9. Redirigir al dashboard (la página interna)
                window.location.href = "dashboard.html";
            });
        })
        .catch(error => {
            // Capturar cualquier error (de red o del backend)
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error al iniciar sesión',
                text: 'Usuario o contraseña incorrectos. Inténtalo de nuevo.',
            });
        });
    });
});