// Espera a que todo el contenido del HTML esté cargado
document.addEventListener("DOMContentLoaded", function() {

    // 1. Seleccionar el formulario
    const registerForm = document.getElementById("register-form");

    // 2. Escuchar el evento "submit" (cuando el usuario hace clic en "Registrarse")
    registerForm.addEventListener("submit", function(event) {

        // 3. Evitar que el formulario se envíe de la forma tradicional (recargando la página)
        event.preventDefault();

        // 4. Obtener los valores de los campos
        const nombre = document.getElementById("nombre").value;
        const apellido = document.getElementById("apellido").value;
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;
        const confirmPassword = document.getElementById("confirm-password").value;

        // 5. Validación simple: revisar que las contraseñas coincidan
        if (password !== confirmPassword) {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'Las contraseñas no coinciden.',
            });
            return; // Detiene la ejecución si no coinciden
        }

        // 6. Preparar los datos para enviar al backend
        const datosUsuario = {
            nombre: nombre,
            apellido: apellido,
            email: email,
            password: password
        };

        // 7. Definir la URL de tu backend (¡IMPORTANTE!)
        // Asumiendo que tu backend FastAPI corre en el puerto 8000
        const backendURL = "https://nutribox.onrender.com/usuarios/";

        // 8. Usar fetch() para enviar los datos (el "mensajero")
        fetch(backendURL, {
            method: 'POST', // Queremos "Crear" un usuario
            headers: {
                'Content-Type': 'application/json', // Le decimos al backend que enviaremos JSON
            },
            body: JSON.stringify(datosUsuario), // Convertimos nuestro objeto JS a un string JSON
        })
        .then(response => {
            if (response.ok) {
                return response.json(); // Si el backend responde bien (ej. 200 o 201)
            } else {
                // Si el backend responde con un error (ej. 400, 404, 500)
                return response.json().then(error => { throw new Error(error.detail || 'Error al registrar'); });
            }
        })
        .then(data => {
            // ¡Éxito! El usuario se creó.
            Swal.fire({
                icon: 'success',
                title: '¡Registrado!',
                text: 'Usuario creado exitosamente. Ahora puedes iniciar sesión.',
            }).then(() => {
                // Redirigir al login después de 2 segundos
                setTimeout(() => {
                    window.location.href = "login.html"; // Redirige al login
                }, 2000);
            });
        })
        .catch(error => {
            // Capturar cualquier error (de red o del backend)
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Oops...',
                text: error.message || 'Algo salió mal. Inténtalo de nuevo.',
            });
        });
    });
});