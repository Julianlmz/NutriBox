# 🍎 NutriBox - Sistema de Gestión de Loncheras Nutritivas

## 📋 Descripción

**NutriBox** es una aplicación web completa para la gestión inteligente de loncheras escolares, diseñada para padres de familia que buscan garantizar una alimentación balanceada y segura para sus hijos. El sistema permite crear loncheras personalizadas considerando restricciones alimentarias, calcular información nutricional automáticamente y gestionar múltiples perfiles familiares.

---

## ✨ Características Principales

* **🍱 Creación de Loncheras Personalizadas:** Arma loncheras balanceadas con cálculo automático de calorías y macronutrientes.
* **🚫 Sistema de Restricciones:** Detecta y bloquea automáticamente alimentos con alérgenos peligrosos.
* **👨‍👩‍👧‍👦 Múltiples Perfiles:** Gestiona perfiles para todos tus hijos en una sola cuenta.
* **📊 Estadísticas Nutricionales:** Visualiza gráficos de gasto mensual, alimentos más frecuentes y distribución nutricional.
* **🗺️ Gestión de Direcciones:** Administra múltiples direcciones de entrega (casa, colegio, abuelos).
* **🧮 5 Algoritmos Especializados:** NutriSort, NutriCost, NutriBucket, NutriTop y Sugeridor Inteligente.

---

## 🚀 Tecnologías

### Backend
* **FastAPI:** Framework web moderno y de alto rendimiento.
* **SQLModel:** ORM asíncrono basado en SQLAlchemy y Pydantic.
* **PostgreSQL / SQLite:** Base de datos relacional.
* **JWT:** Autenticación segura con tokens.
* **Supabase Storage:** Almacenamiento de imágenes en la nube.
* **Bcrypt:** Hash seguro de contraseñas.

### Frontend
* **HTML5 / CSS3 / JavaScript (Vanilla)**
* **Bootstrap 5:** Framework CSS responsivo.
* **Chart.js:** Visualización de datos.
* **SweetAlert2:** Alertas elegantes.
* **Font Awesome:** Iconografía.

### Arquitectura
* Patrón MVC mejorado con separación de capas.
* API RESTful completamente documentada.
* Async/Await para operaciones de base de datos.
* Middleware CORS configurado para desarrollo y producción.

---

## 📁 Estructura del Proyecto

```text
NutriBox/
│
├── 📂 Core/                    # Núcleo de la aplicación
│   ├── auth.py                # Autenticación JWT
│   ├── database.py            # Configuración de base de datos
│   ├── seguridad.py           # Funciones de seguridad (bcrypt)
│   └── supabase_client.py     # Cliente para almacenamiento de imágenes
│
├── 📂 Modulos/                 # Módulos principales
│   ├── models.py              # Modelos de datos (SQLModel)
│   ├── Usuario.py             # Endpoints de usuarios
│   ├── Hijo.py                # Gestión de perfiles de hijos
│   ├── Alimento.py            # CRUD de alimentos
│   ├── Lonchera.py            # Creación y gestión de loncheras
│   ├── Restriccion.py         # Restricciones alimentarias
│   ├── Perfil.py              # Perfiles de usuario
│   ├── Pedido.py              # Sistema de pedidos
│   ├── Producto.py            # Catálogo de productos
│   ├── Inventario.py          # Control de inventario
│   └── Algoritmos.py          # Rutas a documentación de algoritmos
│
├── 📂 Servicios/               # Servicios auxiliares
│   ├── Direccion.py           # Gestión de direcciones de entrega
│   ├── Historial.py           # Auditoría de eliminaciones
│   └── Reporte.py             # Generación de reportes CSV
│
├── 📂 Frontend/                # Archivos estáticos del cliente
│   ├── 📂 css/                # Estilos
│   │   └── style.css
│   └── 📂 js/                 # Scripts JavaScript
│       ├── auth-guard.js      # Protección de rutas
│       ├── login.js           # Lógica de inicio de sesión
│       ├── register.js        # Registro de usuarios
│       ├── dashboard.js       # Panel principal
│       ├── hijos.js           # Gestión de hijos
│       ├── alimentos.js       # CRUD de alimentos
│       ├── crear-lonchera.js  # Creador de loncheras
│       ├── loncheras.js       # Historial de loncheras
│       ├── direcciones.js     # Administración de direcciones
│       ├── restricciones.js   # Gestión de restricciones
│       └── estadisticas.js    # Visualización de datos
│
├── 📂 Templates/               # Plantillas HTML
│   ├── 📂 Algoritmos/         # Documentación de algoritmos
│   ├── index.html             # Landing page
│   ├── dashboard.html         # Panel principal
│   └── ...                    # Otras vistas
│
├── 📂 Tests/                   # Pruebas
│   └── test_main.http         # Suite de pruebas HTTP
│
├── main.py                     # Punto de entrada de la aplicación
├── requirements.txt            # Dependencias Python
├── .env.example                # Variables de entorno (ejemplo)
└── README.md                   # Este archivo
```

Prerrequisitos

    Python 3.11+

    pip (gestor de paquetes de Python)

    PostgreSQL (opcional, usa SQLite por defecto)

    Cuenta de Supabase (opcional, para almacenamiento de imágenes)

Pasos de Instalación

    
    Clonar el repositorio
    Bash
    git clone [https://github.com/tu-usuario/nutribox.git](https://github.com/tu-usuario/nutribox.git)
    cd nutribox
    

Crear entorno virtual
    Bash
    
    python -m venv venv

# Windows
    venv\Scripts\activate

# Linux/Mac
    source venv/bin/activate

Instalar dependencias
    Bash
    
    pip install -r requirements.txt

Configurar variables de entorno Crea un archivo .env en la raíz del proyecto basándote en .env.example:
Fragmento de código

# Base de datos (opcional - usa SQLite si no se configura)
    POSTGRESQL_ADDON_URI=postgresql://usuario:password@localhost:5432/nutribox

# Supabase Storage (opcional - para subir imágenes)
    SUPABASE_URL=[https://tu-proyecto.supabase.co](https://tu-proyecto.supabase.co)
    SUPABASE_KEY=tu-api-key-aqui
    SUPABASE_BUCKET=nutribox-images

# Seguridad
    SECRET_KEY=tu_clave_secreta

Ejecutar la aplicación
Bash

    uvicorn main:app --reload --host 0.0.0.0 --port 8000

    Acceder a la aplicación

        Frontend: http://localhost:8000

        API Docs: http://localhost:8000/docs

        ReDoc: http://localhost:8000/redoc

🔐 Autenticación

El sistema utiliza JWT (JSON Web Tokens).

    Registro: POST /usuario/

    Login: POST /auth/token (devuelve access_token y user_id)

    Acceso protegido: Incluye el token en el header: Authorization: Bearer {token}

Ejemplo de Uso (Frontend):
JavaScript

    // Login
    const response = await fetch('/auth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: 'username=usuario@email.com&password=tu-password'
    });
    
    const { access_token, user_id } = await response.json();
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('user_id', user_id);
    
    // Petición autenticada
    fetch('/hijo/', {
      headers: { 'Authorization': `Bearer ${access_token}` }
    });

📊 Modelos de Datos
Relaciones de Base de Datos
Plaintext

    ┌─────────────┐
    │   Usuario   │──┐
    │  (Padre)    │  │ 1:N
    └─────────────┘  │
                     ├──> ┌─────────────┐
                     │    │    Hijo     │
                     │    └─────────────┘
                     │         │ N:M
                     │         └──> ┌──────────────┐
                     │              │ Restricción  │
                     │              └──────────────┘
                     │                     │ N:M
                     │                     └──> ┌────────────┐
                     └──> ┌──────────┐          │  Alimento  │
                          │ Lonchera │<────N:M──┘
                          └──────────┘
                               │ N:1
                               └──> ┌────────────┐
                                    │ Dirección  │
                                    └────────────┘

🎨 Características del Frontend
Diseño UI/UX

    Glassmorphism: Efectos de vidrio esmerilado en tarjetas.

    Blobs animados: Fondos dinámicos con gradientes.

    Mobile-first: Totalmente responsivo.

Flujo de Usuario

    Landing Page → Presenta las características.

    Registro/Login → Autenticación segura.

    Dashboard → Vista general con estadísticas.

    Gestión de Hijos → Crear perfiles con fotos.

    Crear Lonchera → Sistema inteligente que detecta alérgenos.

🧮 Algoritmos Especializados

NutriBox incluye 5 algoritmos de ordenamiento y optimización:

    NutriSort-Multiclave: Híbrido TimSort + MergeSort para ordenar alimentos por múltiples criterios.

    NutriCost-Greedy: Optimización de presupuesto (Mochila Fraccionaria).

    NutriBucket-Adapt: Bucket Sort adaptativo por categorías.

    NutriTop-k: Quickselect para encontrar los mejores alimentos sin ordenar todo.

    Sugeridor Inteligente: Greedy + Backtracking para combinaciones óptimas.

    Cada algoritmo tiene su documentación interactiva en /algoritmos/{nombre}.

📡 API Endpoints (Resumen)
Método	Endpoint	Descripción

    POST	/auth/token	Iniciar sesión (Login)
    POST	/usuario/	Registrar usuario
    GET	/hijo/	Listar hijos del usuario
    GET	/alimento/	Listar catálogo de alimentos
    POST	/loncheras	Crear nueva lonchera
    POST	/restriccion/	Crear restricción/alergia
    GET	/direcciones/	Listar direcciones


📝 Licencia y Autores

Autor: Julián Leal - 67001277

Institución: Universidad Católica de Colombia

Link: https://nutribox.onrender.com

Año: 2025

Este proyecto fue desarrollado como trabajo académico para el curso de Estructura de Datos.