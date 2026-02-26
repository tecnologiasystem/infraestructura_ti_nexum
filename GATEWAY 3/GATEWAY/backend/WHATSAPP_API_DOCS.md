# API de WhatsApp - Documentación

## Descripción
Endpoints para consultar y descargar datos de WhatsApp desde la tabla `WhatsAppDetalle` de la base de datos NEXUM.

## Endpoints Disponibles

### 1. Obtener Detalle de WhatsApp
**GET** `/api/whatsapp/detalle`

Obtiene todos los registros que tienen WhatsApp asignado (campo `tiene_whatsApp` no vacío y diferente de "Pausado").

**Parámetros de consulta:**
- `idEncabezado` (int, requerido): ID del encabezado para filtrar los registros

**Ejemplo de uso:**
```
GET /api/whatsapp/detalle?idEncabezado=44
```

**Respuesta exitosa (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "idEncabezado": 44,
      "tiene_whatsApp": "573001234567",
      // ... otros campos
    }
  ],
  "total": 150
}
```

---

### 2. Contar Registros Vacíos
**GET** `/api/whatsapp/vacios`

Cuenta cuántos registros tienen el campo `tiene_whatsApp` vacío o con valor "Pausado".

**Parámetros de consulta:**
- `idEncabezado` (int, requerido): ID del encabezado para filtrar los registros

**Ejemplo de uso:**
```
GET /api/whatsapp/vacios?idEncabezado=44
```

**Respuesta exitosa (200):**
```json
{
  "success": true,
  "vacios": 25
}
```

---

### 3. Obtener Estadísticas
**GET** `/api/whatsapp/estadisticas`

Obtiene estadísticas completas: total de registros, cuántos tienen WhatsApp (excluyendo "Pausado") y cuántos están vacíos o pausados.

**Parámetros de consulta:**
- `idEncabezado` (int, requerido): ID del encabezado para filtrar los registros

**Ejemplo de uso:**
```
GET /api/whatsapp/estadisticas?idEncabezado=44
```

**Respuesta exitosa (200):**
```json
{
  "success": true,
  "estadisticas": {
    "total": 175,
    "con_whatsapp": 150,
    "vacios": 25
  }
}
```

---

### 4. Descargar Excel
**GET** `/api/whatsapp/descargar-excel`

Genera y descarga un archivo Excel con dos pestañas:
1. **Datos WhatsApp**: Todos los registros con WhatsApp asignado
2. **Estadísticas**: Resumen de totales, con WhatsApp y vacíos

**Parámetros de consulta:**
- `idEncabezado` (int, requerido): ID del encabezado para filtrar los registros

**Ejemplo de uso:**
```
GET /api/whatsapp/descargar-excel?idEncabezado=44
```

**Respuesta exitosa (200):**
- Descarga un archivo Excel con nombre: `whatsapp_detalle_{idEncabezado}_{timestamp}.xlsx`

---

## Arquitectura del Código

El código sigue la arquitectura de tres capas del proyecto:

### DAL (Data Access Layer) - `app/dal/whatsapp_dal.py`
- `obtener_whatsapp_detalle_DAL()`: Ejecuta query para obtener registros con WhatsApp
- `contar_whatsapp_vacios_DAL()`: Ejecuta query para contar registros vacíos
- `obtener_estadisticas_whatsapp_DAL()`: Ejecuta query para obtener estadísticas completas

### BLL (Business Logic Layer) - `app/bll/whatsapp_bll.py`
- `obtener_whatsapp_detalle_BLL()`: Lógica de negocio para obtener detalles
- `contar_whatsapp_vacios_BLL()`: Lógica de negocio para contar vacíos
- `obtener_estadisticas_whatsapp_BLL()`: Lógica de negocio para estadísticas

### API (Presentation Layer) - `app/api/whatsapp_api.py`
- Endpoints REST que consumen la capa BLL
- Generación de Excel con pandas y openpyxl
- Manejo de errores y respuestas HTTP

---

## Uso en el Frontend

### Ejemplo: Mostrar estadísticas y botón de descarga

```javascript
// Obtener estadísticas al cargar la página
async function cargarEstadisticas(idEncabezado) {
  try {
    const response = await fetch(`/api/whatsapp/estadisticas?idEncabezado=${idEncabezado}`);
    const data = await response.json();
    
    if (data.success) {
      const stats = data.estadisticas;
      console.log(`Total: ${stats.total}`);
      console.log(`Con WhatsApp: ${stats.con_whatsapp}`);
      console.log(`Vacíos: ${stats.vacios}`);
      
      // Mostrar en la UI
      document.getElementById('totalRegistros').textContent = stats.total;
      document.getElementById('conWhatsapp').textContent = stats.con_whatsapp;
      document.getElementById('faltantes').textContent = stats.vacios;
    }
  } catch (error) {
    console.error('Error al cargar estadísticas:', error);
  }
}

// Descargar Excel
function descargarExcel(idEncabezado) {
  const url = `/api/whatsapp/descargar-excel?idEncabezado=${idEncabezado}`;
  window.open(url, '_blank');
}
```

### Ejemplo HTML
```html
<div class="estadisticas">
  <h3>Estadísticas de WhatsApp</h3>
  <p>Total de registros: <span id="totalRegistros">-</span></p>
  <p>Con WhatsApp: <span id="conWhatsapp">-</span></p>
  <p>Faltantes: <span id="faltantes">-</span></p>
  
  <button onclick="descargarExcel(44)">Descargar Excel</button>
</div>
```

---

## Queries SQL Originales

Los endpoints implementan estos queries (modificados para excluir "Pausado"):

```sql
-- Query 1: Obtener registros con WhatsApp (excluyendo Pausado)
SELECT *
FROM [NEXUM].[dbo].[WhatsAppDetalle] WITH(NOLOCK)
WHERE tiene_whatsApp <> ''
AND tiene_whatsApp <> 'Pausado'
AND idEncabezado = 44

-- Query 2: Contar registros vacíos o pausados
SELECT COUNT(*) as VACIOS
FROM [NEXUM].[dbo].[WhatsAppDetalle] WITH(NOLOCK)
WHERE (tiene_whatsApp = '' OR tiene_whatsApp = 'Pausado')
AND idEncabezado = 44
```

---

## Notas Técnicas

1. **Conexión a Base de Datos**: Usa `get_connection()` de `config/db_config.py`
2. **Base de Datos**: NEXUM en SQL Server (172.18.72.111,1433)
3. **Tabla**: `[NEXUM].[dbo].[WhatsAppDetalle]`
4. **Generación de Excel**: Usa `pandas` y `openpyxl`
5. **CORS**: Ya configurado en `main.py` para permitir todas las origins durante desarrollo

---

## Testing

Puedes probar los endpoints usando:

1. **Navegador**: Visita `http://localhost:8000/docs` para ver la documentación interactiva de FastAPI
2. **cURL**:
   ```bash
   curl "http://localhost:8000/api/whatsapp/estadisticas?idEncabezado=44"
   ```
3. **Postman**: Importa los endpoints y prueba cada uno
