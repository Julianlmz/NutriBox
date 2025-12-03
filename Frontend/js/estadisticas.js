// estadisticas.js
const API_URL = 'http://127.0.0.1:8000';

let chartLoncherasPorHijo, chartAlimentosMasUsados, chartLoncherasPorMes, chartRestriccionesSeveridad;

document.addEventListener('DOMContentLoaded', () => {
    cargarEstadisticas();
});

async function cargarEstadisticas() {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = 'login.html';
            return;
        }

        // Cargar todos los datos
        const [hijos, loncheras, alimentos, restricciones] = await Promise.all([
            fetch(`${API_URL}/hijo/`, { headers: { 'Authorization': `Bearer ${token}` } }).then(r => r.json()),
            fetch(`${API_URL}/lonchera/`, { headers: { 'Authorization': `Bearer ${token}` } }).then(r => r.json()),
            fetch(`${API_URL}/alimento/`, { headers: { 'Authorization': `Bearer ${token}` } }).then(r => r.json()),
            fetch(`${API_URL}/restriccion/`, { headers: { 'Authorization': `Bearer ${token}` } }).then(r => r.json())
        ]);

        // Actualizar métricas
        document.getElementById('stat-hijos').textContent = hijos.length;
        document.getElementById('stat-loncheras').textContent = loncheras.length;
        document.getElementById('stat-alimentos').textContent = alimentos.length;
        document.getElementById('stat-restricciones').textContent = restricciones.length;

        // Crear gráficos
        crearGraficoLoncherasPorHijo(hijos, loncheras);
        crearGraficoAlimentosMasUsados(loncheras);
        crearGraficoLoncherasPorMes(loncheras);
        crearGraficoRestriccionesSeveridad(restricciones);

    } catch (error) {
        console.error('Error al cargar estadísticas:', error);
    }
}

function crearGraficoLoncherasPorHijo(hijos, loncheras) {
    const ctx = document.getElementById('chartLoncherasPorHijo');

    // Contar loncheras por hijo
    const conteo = {};
    hijos.forEach(hijo => {
        conteo[hijo.nombre] = loncheras.filter(l => l.hijo_id === hijo.id).length;
    });

    if (chartLoncherasPorHijo) chartLoncherasPorHijo.destroy();

    chartLoncherasPorHijo = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(conteo),
            datasets: [{
                data: Object.values(conteo),
                backgroundColor: ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336', '#00BCD4'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

function crearGraficoAlimentosMasUsados(loncheras) {
    const ctx = document.getElementById('chartAlimentosMasUsados');

    // Contar alimentos (simulado - necesitarías endpoint de alimentos por lonchera)
    const alimentosConteo = {};

    // Simulación de datos (reemplazar con datos reales)
    const top5 = {
        'Manzana': 45,
        'Sándwich': 38,
        'Yogurt': 32,
        'Galletas': 28,
        'Jugo': 25
    };

    if (chartAlimentosMasUsados) chartAlimentosMasUsados.destroy();

    chartAlimentosMasUsados = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(top5),
            datasets: [{
                label: 'Veces usado',
                data: Object.values(top5),
                backgroundColor: '#4CAF50',
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function crearGraficoLoncherasPorMes(loncheras) {
    const ctx = document.getElementById('chartLoncherasPorMes');

    // Agrupar por mes
    const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    const conteoMeses = new Array(12).fill(0);

    loncheras.forEach(l => {
        if (l.fecha_creacion) {
            const fecha = new Date(l.fecha_creacion);
            const mes = fecha.getMonth();
            conteoMeses[mes]++;
        }
    });

    if (chartLoncherasPorMes) chartLoncherasPorMes.destroy();

    chartLoncherasPorMes = new Chart(ctx, {
        type: 'line',
        data: {
            labels: meses,
            datasets: [{
                label: 'Loncheras creadas',
                data: conteoMeses,
                borderColor: '#2196F3',
                backgroundColor: 'rgba(33, 150, 243, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function crearGraficoRestriccionesSeveridad(restricciones) {
    const ctx = document.getElementById('chartRestriccionesSeveridad');

    // Contar por severidad
    const conteo = { 'Alto': 0, 'Medio': 0, 'Bajo': 0 };
    restricciones.forEach(r => {
        if (conteo[r.nivel_severidad] !== undefined) {
            conteo[r.nivel_severidad]++;
        }
    });

    if (chartRestriccionesSeveridad) chartRestriccionesSeveridad.destroy();

    chartRestriccionesSeveridad = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Alto', 'Medio', 'Bajo'],
            datasets: [{
                data: [conteo.Alto, conteo.Medio, conteo.Bajo],
                backgroundColor: ['#F44336', '#FF9800', '#4CAF50'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}