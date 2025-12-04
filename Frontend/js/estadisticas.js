// estadisticas.js
const API_URL = 'http://127.0.0.1:8000';

// Variables globales para las instancias de los gráficos
let charts = {};

document.addEventListener('DOMContentLoaded', () => {
    cargarEstadisticas();
    cargarNombreUsuario();
});

// Función para poner el nombre "Bienvenid@, Julian" en el navbar
function cargarNombreUsuario() {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    fetch(`${API_URL}/usuario/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(r => r.ok ? r.json() : null)
    .then(u => {
        if(u && document.getElementById('userName')) {
            document.getElementById('userName').textContent = u.nombre;
        }
    })
    .catch(console.error);
}

async function cargarEstadisticas() {
    try {
        const token = localStorage.getItem('access_token');
        const userId = localStorage.getItem('user_id');

        if (!token || !userId) {
            window.location.href = 'login.html';
            return;
        }

        // Cargar datos en paralelo usando los endpoints correctos
        const [hijosRes, loncherasRes, restriccionesRes] = await Promise.all([
            fetch(`${API_URL}/hijo/`, { headers: { 'Authorization': `Bearer ${token}` } }),
            fetch(`${API_URL}/usuarios/${userId}/loncheras`, { headers: { 'Authorization': `Bearer ${token}` } }),
            fetch(`${API_URL}/restriccion/`, { headers: { 'Authorization': `Bearer ${token}` } })
        ]);

        const hijos = hijosRes.ok ? await hijosRes.json() : [];
        const loncheras = loncherasRes.ok ? await loncherasRes.json() : [];
        const restricciones = restriccionesRes.ok ? await restriccionesRes.json() : [];

        // --- CALCULAR MÉTRICAS ---

        // Gasto Total
        const gastoTotal = loncheras.reduce((sum, l) => sum + l.precio, 0);

        // Actualizar Tarjetas
        document.getElementById('stat-hijos').textContent = hijos.length;
        document.getElementById('stat-loncheras').textContent = loncheras.length;
        // Formatear dinero bonito
        document.getElementById('stat-gasto').textContent = `$${gastoTotal.toLocaleString('es-CO')}`;
        document.getElementById('stat-restricciones').textContent = restricciones.length;

        // --- GENERAR GRÁFICOS ---
        generarGraficoGastoMensual(loncheras);
        generarGraficoHijos(hijos, loncheras);
        generarGraficoTopAlimentos(loncheras);
        generarGraficoRestricciones(restricciones);

    } catch (error) {
        console.error('Error al cargar estadísticas:', error);
    }
}

// 1. GRÁFICO DE GASTO MENSUAL
function generarGraficoGastoMensual(loncheras) {
    const ctx = document.getElementById('chartGastoMensual');

    const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    const hoy = new Date();
    const etiquetas = [];
    const datos = [];

    for (let i = 5; i >= 0; i--) {
        const d = new Date(hoy.getFullYear(), hoy.getMonth() - i, 1);
        etiquetas.push(meses[d.getMonth()]);

        const gastoMes = loncheras
            .filter(l => {
                const fechaL = new Date(l.fecha_creacion);
                return fechaL.getMonth() === d.getMonth() && fechaL.getFullYear() === d.getFullYear();
            })
            .reduce((sum, l) => sum + l.precio, 0);

        datos.push(gastoMes);
    }

    if (charts.gasto) charts.gasto.destroy();

    charts.gasto = new Chart(ctx, {
        type: 'line',
        data: {
            labels: etiquetas,
            datasets: [{
                label: 'Gasto ($)',
                data: datos,
                borderColor: '#4CAF50',
                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                borderWidth: 3,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

// 2. GRÁFICO LONCHERAS POR HIJO
function generarGraficoHijos(hijos, loncheras) {
    const ctx = document.getElementById('chartLoncherasPorHijo');

    const conteo = {};
    hijos.forEach(h => conteo[h.nombre] = 0);

    loncheras.forEach(l => {
        hijos.forEach(h => {
            // Buscamos el nombre del hijo en la descripción de la lonchera
            if (l.descripcion && l.descripcion.includes(h.nombre)) {
                conteo[h.nombre]++;
            }
        });
    });

    if (charts.hijos) charts.hijos.destroy();

    charts.hijos = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(conteo),
            datasets: [{
                data: Object.values(conteo),
                backgroundColor: ['#2196F3', '#FF9800', '#4CAF50', '#9C27B0'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom' } }
        }
    });
}

// 3. GRÁFICO TOP ALIMENTOS
function generarGraficoTopAlimentos(loncheras) {
    const ctx = document.getElementById('chartTopAlimentos');

    const conteoAlimentos = {};

    loncheras.forEach(l => {
        if (l.alimentos && Array.isArray(l.alimentos)) {
            l.alimentos.forEach(a => {
                const nombre = a.nombre_alimento || a.nombre || 'Item';
                conteoAlimentos[nombre] = (conteoAlimentos[nombre] || 0) + 1;
            });
        }
    });

    const topAlimentos = Object.entries(conteoAlimentos)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);

    if (charts.alimentos) charts.alimentos.destroy();

    charts.alimentos = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topAlimentos.map(i => i[0]),
            datasets: [{
                label: 'Veces incluido',
                data: topAlimentos.map(i => i[1]),
                backgroundColor: '#FF9800',
                borderRadius: 5
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: { legend: { display: false } }
        }
    });
}

// 4. GRÁFICO RESTRICCIONES
function generarGraficoRestricciones(restricciones) {
    const ctx = document.getElementById('chartRestriccionesSeveridad');

    const conteo = { 'Alto': 0, 'Medio': 0, 'Bajo': 0 };
    restricciones.forEach(r => {
        if (conteo[r.nivel_severidad] !== undefined) conteo[r.nivel_severidad]++;
    });

    if (charts.restricciones) charts.restricciones.destroy();

    charts.restricciones = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Severa (Alto)', 'Moderada (Medio)', 'Leve (Bajo)'],
            datasets: [{
                data: [conteo.Alto, conteo.Medio, conteo.Bajo],
                backgroundColor: ['#F44336', '#FFC107', '#8BC34A'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom' } }
        }
    });
}