# 🗺️ MAPA DE RELACIONES - NutriBox

## Diagrama de Relaciones Completo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BASE DE DATOS NUTRIBOX                              │
│                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌──────────────┐
│   USUARIO    │ ◄─── MODELO PRINCIPAL
│   (id: PK)   │
│              │
│ - nombre     │
│ - apellido   │
│ - cedula     │
│ - edad       │
│ - rol        │
│ - localidad  │
└──┬───┬───┬───┘
   │   │   │
   │   │   └─────────────────────────┐
   │   │                             │
   │   │   ┌─────────────────────┐   │   ┌──────────────────┐
   │   │   │  HISTORIAL          │   │   │   PEDIDO         │
   │   └──►│  ELIMINACION        │   └──►│   (id: PK)       │
   │       │  (id: PK)           │       │                  │
   │       │                     │       │ - usuario_id FK  │ ◄── 1:N
   │       │ - usuario_id FK     │       │ - fecha          │     (Un usuario
   │       │ - tabla_nombre      │       │ - total          │      hace muchos
   │       │ - registro_id       │       │ - estado         │      pedidos)
   │       │ - datos_json        │       └────────┬─────────┘
   │       │ - motivo            │                │
   │       └─────────────────────┘                │
   │                                              │
   │   ┌─────────────────────┐                   │ N:M (Muchos a Muchos)
   │   │     PERFIL          │                   │ a través de:
   └──►│     (id: PK)        │                   │
       │                     │                   ▼
       │ - usuario_id FK ◄───┼─── 1:1       ┌──────────────────┐
       │   (UNIQUE)          │   (Un usuario│  PEDIDO_PRODUCTO │ ◄── TABLA
       │ - bio               │    tiene UN  │  (Tabla N:M)     │     INTERMEDIA
       │ - telefono          │    perfil)   │                  │
       │ - foto_url          │              │ - pedido_id PK   │
       └─────────────────────┘              │ - producto_id PK │
                                            │ - cantidad       │
                                            │ - precio_unit    │
   ┌─────────────────────┐                 │ - subtotal       │
   │     LONCHERA        │                 └────────┬─────────┘
   │     (id: PK)        │                          │
   │                     │                          │
   │ - usuario_id FK ◄───┼─── 1:N                  │
   │ - nombre            │     (Un usuario          │
   │ - descripcion       │      tiene muchas        │
   │ - precio            │      loncheras)          ▼
   │ - calorias          │              ┌──────────────────┐
   └─────────┬───────────┘              │    PRODUCTO      │
             │                          │    (id: PK)      │
             │                          │                  │
             │                          │ - nombre         │
             │ N:M (Muchos a Muchos)    │ - descripcion    │
             │ a través de:             │ - precio         │
             ▼                          │ - stock_actual   │
   ┌─────────────────────┐             └──────────────────┘
   │ LONCHERA_ALIMENTO   │ ◄── TABLA
   │ (Tabla N:M)         │     INTERMEDIA
   │                     │
   │ - lonchera_id PK    │
   │ - alimento_id PK    │
   │ - cantidad_gramos   │
   └──────────┬──────────┘
              │
              │
              ▼
   ┌─────────────────────┐
   │     ALIMENTO        │
   │     (id: PK)        │
   │                     │
   │ - nombre            │
   │ - categoria         │
   │ - calorias_100g     │
   │ - proteinas_100g    │
   │ - carbohidratos     │
   │ - grasas            │
   │ - precio_unit       │
   │ - stock_actual      │
   └─────────┬───────┬───┘
             │       │
             │       └──────────────────┐
             │                          │
             │ N:M (Muchos a Muchos)    │ 1:N (Uno a Muchos)
             │ a través de:             │
             ▼                          ▼
   ┌─────────────────────┐   ┌──────────────────────┐
   │  RESTRICCION_       │   │   MOVIMIENTO         │
   │  ALIMENTO           │   │   INVENTARIO         │
   │  (Tabla N:M)        │   │   (id: PK)           │
   │                     │   │                      │
   │ - restriccion_id PK │   │ - alimento_id FK     │
   │ - alimento_id PK    │   │ - tipo_movimiento    │
   │ - fecha_asociacion  │   │ - cantidad           │
   └──────────┬──────────┘   │ - stock_anterior     │
              │               │ - stock_nuevo        │
              │               │ - motivo             │
              ▼               │ - usuario_id FK      │
   ┌─────────────────────┐   └──────────────────────┘
   │   RESTRICCION       │
   │   (id: PK)          │
   │                     │
   │ - nombre            │
   │ - descripcion       │
   │ - nivel_severidad   │
   └─────────────────────┘
```

---

## Leyenda de Relaciones

### 1:1 (Uno a Uno)
```
┌─────────┐        ┌─────────┐
│ Usuario │───────►│ Perfil  │
└─────────┘   1:1  └─────────┘
```
- Un usuario tiene **UN** perfil
- Un perfil pertenece a **UN** usuario
- Campo: `usuario_id UNIQUE` en Perfil

### 1:N (Uno a Muchos)
```
┌─────────┐        ┌──────────┐
│ Usuario │───────►│ Lonchera │
└─────────┘   1:N  └──────────┘
                    (muchas)
```
- Un usuario tiene **MUCHAS** loncheras
- Una lonchera pertenece a **UN** usuario
- Campo: `usuario_id` en Lonchera

### N:M (Muchos a Muchos)
```
┌──────────┐    ┌───────────────┐    ┌──────────┐
│ Lonchera │───►│ Lonchera_     │◄───│ Alimento │
└──────────┘    │ Alimento      │    └──────────┘
   (muchas)     └───────────────┘     (muchos)
                 Tabla Intermedia
```
- Una lonchera tiene **MUCHOS** alimentos
- Un alimento puede estar en **MUCHAS** loncheras
- Tabla intermedia: `LoncheraAlimento`

---

## Tablas por Categoría

### 📋 TABLAS PRINCIPALES (8)
Tablas con datos directos del negocio:

1. **Usuario** - Usuarios del sistema (padres e hijos)
2. **Perfil** - Información adicional del usuario (1:1)
3. **Lonchera** - Loncheras creadas por usuarios (1:N)
4. **Alimento** - Catálogo de alimentos disponibles
5. **Restriccion** - Alergias y restricciones alimentarias
6. **Producto** - Productos para venta
7. **Pedido** - Pedidos realizados por usuarios (1:N)
8. **MovimientoInventario** - Historial de cambios en stock (1:N)

### 🔗 TABLAS DE RELACIÓN N:M (3)
Tablas que conectan otras tablas (muchos a muchos):

9. **RestriccionAlimento** - Qué alimentos tienen qué restricciones
10. **LoncheraAlimento** - Qué alimentos tiene cada lonchera
11. **PedidoProducto** - Qué productos tiene cada pedido

### 📊 TABLAS DE AUDITORÍA (1)
Tablas para registro y auditoría:

12. **HistorialEliminacion** - Registro de eliminaciones

---

## Flujo de Datos Típico

### Caso 1: Usuario crea una lonchera
```
1. Usuario se registra
   └─► Se crea registro en tabla USUARIO

2. Usuario crea perfil
   └─► Se crea registro en tabla PERFIL (1:1)
   
3. Usuario crea lonchera
   └─► Se crea registro en tabla LONCHERA (1:N)
   
4. Usuario agrega alimentos a la lonchera
   └─► Se crean registros en tabla LONCHERA_ALIMENTO (N:M)
```

### Caso 2: Usuario hace un pedido
```
1. Usuario crea un pedido
   └─► Se crea registro en tabla PEDIDO (1:N)
   
2. Usuario agrega productos al pedido
   └─► Se crean registros en tabla PEDIDO_PRODUCTO (N:M)
   
3. Se confirma el pedido
   └─► Se descuenta el stock en tabla PRODUCTO
   └─► Se registra en MOVIMIENTO_INVENTARIO (1:N)
```

### Caso 3: Gestión de restricciones
```
1. Se registra un alimento nuevo
   └─► Se crea registro en tabla ALIMENTO
   
2. Se identifica que tiene gluten
   └─► Se crea asociación en RESTRICCION_ALIMENTO (N:M)
   
3. Usuario busca alimentos sin gluten
   └─► Se consulta RESTRICCION_ALIMENTO
   └─► Se filtran alimentos que NO tienen esa restricción
```

---

## Campos Clave en Relaciones

### Foreign Keys (Llaves Foráneas)
```
Usuario.id
  ↓
  ├─► Perfil.usuario_id (UNIQUE para 1:1)
  ├─► Lonchera.usuario_id (1:N)
  ├─► Pedido.usuario_id (1:N)
  └─► MovimientoInventario.usuario_id (1:N)

Lonchera.id + Alimento.id
  ↓
  └─► LoncheraAlimento (lonchera_id, alimento_id) N:M

Pedido.id + Producto.id
  ↓
  └─► PedidoProducto (pedido_id, producto_id) N:M

Restriccion.id + Alimento.id
  ↓
  └─► RestriccionAlimento (restriccion_id, alimento_id) N:M
```

---

## Endpoints por Relación

### Relación 1:1 (Usuario ↔ Perfil)
```
POST   /perfiles                    - Crear perfil para usuario
GET    /perfiles/usuario/{id}       - Obtener perfil de un usuario
GET    /perfiles/{id}/completo      - Ver perfil con datos del usuario
```

### Relación 1:N (Usuario → Loncheras)
```
GET    /loncheras?usuario_id={id}   - Ver loncheras de un usuario
POST   /loncheras                    - Crear lonchera para usuario
```

### Relación N:M (Lonchera ↔ Alimento)
```
POST   /loncheras/{id}/alimentos/{alimento_id}  - Agregar alimento
GET    /loncheras/{id}/alimentos                - Ver alimentos
DELETE /loncheras/{id}/alimentos/{alimento_id}  - Quitar alimento
```

### Relación N:M (Pedido ↔ Producto)
```
POST   /pedidos/{id}/productos/{producto_id}  - Agregar producto
GET    /pedidos/{id}/detalle                  - Ver productos
DELETE /pedidos/{id}/productos/{producto_id}  - Quitar producto
```

### Relación N:M (Alimento ↔ Restriccion)
```
POST   /restricciones/{id}/alimentos/{alimento_id}  - Asociar
GET    /restricciones/{id}/alimentos                - Ver alimentos con restricción
GET    /alimentos/{id}/restricciones                - Ver restricciones de alimento
```

---

## Validaciones Importantes

### 1:1 (Usuario ↔ Perfil)
```python
# ✅ CORRECTO: Un usuario, un perfil
Usuario.id = 1 → Perfil.usuario_id = 1

# ❌ INCORRECTO: No se puede crear segundo perfil
Usuario.id = 1 → Perfil.usuario_id = 1 (ya existe)
                 Perfil.usuario_id = 1 (ERROR: duplicado)
```

### 1:N (Usuario → Loncheras)
```python
# ✅ CORRECTO: Un usuario, muchas loncheras
Usuario.id = 1 → Lonchera.usuario_id = 1
                 Lonchera.usuario_id = 1
                 Lonchera.usuario_id = 1 (todas válidas)
```

### N:M (Lonchera ↔ Alimento)
```python
# ✅ CORRECTO: Mismo alimento en varias loncheras
Lonchera.id = 1 → LoncheraAlimento(1, 5)  # Lonchera 1, Alimento 5
Lonchera.id = 2 → LoncheraAlimento(2, 5)  # Lonchera 2, Alimento 5
Lonchera.id = 3 → LoncheraAlimento(3, 5)  # Lonchera 3, Alimento 5
```

---

## Resumen Visual

```
┌─────────────────────────────────────────────┐
│ NUTRIBOX - 12 MODELOS - 3 TIPOS RELACIONES │
└─────────────────────────────────────────────┘

    ┌──────────┐
    │ USUARIO  │ ◄── Centro del sistema
    └────┬─────┘
         │
    ┌────┴────┬─────────┬──────────┐
    │         │         │          │
   1:1       1:N       1:N        1:N
    │         │         │          │
    ▼         ▼         ▼          ▼
┌────────┐ ┌────┐  ┌────────┐  ┌────┐
│ Perfil │ │Long│  │ Pedido │  │Hist│
└────────┘ └──┬─┘  └───┬────┘  └────┘
              │        │
             N:M      N:M
              │        │
              ▼        ▼
           ┌────┐  ┌──────┐
           │Alim│  │Produc│
           └──┬─┘  └──────┘
              │
             N:M
              │
              ▼
           ┌────┐
           │Rest│
           └────┘
```

**Legend:**
- 1:1 = Uno a Uno (línea simple)
- 1:N = Uno a Muchos (línea con flecha)
- N:M = Muchos a Muchos (línea doble)

---

**Total: 6 Relaciones Implementadas**
- 1 relación 1:1 ✅
- 3 relaciones 1:N ✅
- 3 relaciones N:M ✅ (con 3 tablas intermedias)
