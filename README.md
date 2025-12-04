# 🍎 NutriBox - Sistema de Gestión de Loncheras Nutritivas

## 📋 Descripción

**NutriBox** es una aplicación web para la gestión inteligente de loncheras escolares, diseñada para padres que buscan garantizar una alimentación balanceada y segura para sus hijos.  
El sistema permite:

- Crear loncheras personalizadas considerando restricciones alimentarias.  
- Calcular automáticamente información nutricional.  
- Gestionar múltiples perfiles familiares.  

---

## ✨ Características Principales

- **🍱 Creación de Loncheras Personalizadas:** Cálculo automático de calorías y macronutrientes.  
- **🚫 Sistema de Restricciones:** Bloqueo automático de alimentos con alérgenos peligrosos.  
- **👨‍👩‍👧‍👦 Múltiples Perfiles:** Administración de perfiles de hijos en una sola cuenta.  
- **📊 Estadísticas Nutricionales:** Gráficos de gasto mensual, alimentos frecuentes y distribución nutricional.  
- **🗺️ Gestión de Direcciones:** Manejo de múltiples direcciones de entrega (casa, colegio, abuelos).  
- **🧮 Algoritmos Especializados:** NutriSort, NutriCost, NutriBucket, NutriTop y Sugeridor Inteligente.  

---

## 🚀 Tecnologías

### Backend
- FastAPI  
- SQLModel  
- PostgreSQL / SQLite  
- JWT  
- Supabase Storage  
- Bcrypt  

### Frontend
- HTML5 / CSS3 / JavaScript (Vanilla)  
- Bootstrap 5  
- Chart.js  
- SweetAlert2  
- Font Awesome  

### Arquitectura
- Patrón MVC con separación de capas.  
- API RESTful documentada.  
- Operaciones asíncronas con `async/await`.  
- Middleware CORS para desarrollo y producción.  

---

## 📁 Estructura del Proyecto

```text
NutriBox/
├── Core/                  # Núcleo de la aplicación
├── Modulos/               # Módulos principales
├── Servicios/             # Servicios auxiliares
├── Frontend/              # Archivos estáticos
├── Templates/             # Plantillas HTML
├── Tests/                 # Pruebas
├── main.py                # Punto de entrada
├── requirements.txt       # Dependencias
├── .env.example           # Variables de entorno
└── README.md              # Este archivo
```

---

## ⚙️ Prerrequisitos

- Python 3.11+  
- pip  
- PostgreSQL (opcional, SQLite por defecto)  
- Cuenta Supabase (opcional, para imágenes)  

---

## 🛠️ Instalación

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/nutribox.git
cd nutribox

# Crear entorno virtual
python -m venv venv

# Activar entorno
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Configuración de entorno

```env
POSTGRESQL_ADDON_URI=postgresql://usuario:password@localhost:5432/nutribox
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-api-key-aqui
SUPABASE_BUCKET=nutribox-images
SECRET_KEY=tu_clave_secreta
```

---

## ▶️ Ejecución

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- Frontend: [http://localhost:8000](http://localhost:8000)  
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)  
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)  

---

## 🔐 Autenticación

- Registro: `POST /usuario/`  
- Login: `POST /auth/token`  
- Acceso protegido: `Authorization: Bearer {token}`  

---

## 📊 Modelos de Datos

```plaintext
Usuario (Padre) 1:N Hijo
Hijo N:M Restricción
Restricción N:M Alimento
Usuario 1:N Lonchera N:1 Dirección
```

---

## 🎨 Frontend

- Glassmorphism  
- Blobs animados  
- Mobile-first  

Flujo: Landing → Registro/Login → Dashboard → Gestión de Hijos → Crear Lonchera.  

---

## 🧮 Algoritmos Especializados

- NutriSort-Multiclave  
- NutriCost-Greedy  
- NutriBucket-Adapt  
- NutriTop-k  
- Sugeridor Inteligente  

---

## 📡 API Endpoints (Resumen)

| Método | Endpoint       | Descripción              |
|--------|---------------|--------------------------|
| POST   | /auth/token   | Iniciar sesión           |
| POST   | /usuario/     | Registrar usuario        |
| GET    | /hijo/        | Listar hijos             |
| GET    | /alimento/    | Listar alimentos         |
| POST   | /loncheras    | Crear lonchera           |
| POST   | /restriccion/ | Crear restricción        |
| GET    | /direcciones/ | Listar direcciones       |

---

## 📝 Licencia y Autores

- Autor: **Julián Leal - 67001277**  
- Institución: **Universidad Católica de Colombia**
- Link del Render: https://nutribox.onrender.com
- Año: **2025**  


