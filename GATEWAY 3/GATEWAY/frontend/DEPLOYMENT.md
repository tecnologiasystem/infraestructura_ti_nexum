# 🚀 Despliegue del Frontend con Reverse Proxy

Este documento explica cómo desplegar el frontend de Gateway con Nginx como reverse proxy.

## 📋 Requisitos Previos

- Docker y Docker Compose instalados
- Puertos 80 disponible en el servidor
- Acceso a los servidores backend (172.18.73.22:3002 y 172.18.73.76:3000)

## 🏗️ Arquitectura

```
┌─────────────┐
│   Usuario   │
└──────┬──────┘
       │ http://tu-servidor
       ▼
┌─────────────────────────────┐
│   Nginx (Puerto 80)         │
│   - Sirve React Build       │
│   - Reverse Proxy           │
└──────┬──────────────────────┘
       │
       ├─► /api/* ──────────► http://172.18.73.22:3002/api/*
       ├─► /auth/* ─────────► http://172.18.73.76:3000/*
       └─► /gateway/* ──────► http://172.18.73.22:3002/gateway/*
```

## 🔧 Configuración

### 1. Archivos Creados

- **nginx.conf**: Configuración del reverse proxy
- **Dockerfile**: Build multi-etapa (Node + Nginx)
- **docker-compose.yml**: Orquestación del contenedor
- **.dockerignore**: Archivos excluidos del build
- **src/config/rutas.js**: Adaptado para desarrollo/producción

### 2. Rutas del Reverse Proxy

| Ruta Frontend | Destino Backend |
|--------------|-----------------|
| `/api/*` | `http://172.18.73.22:3002/api/*` |
| `/auth/*` | `http://172.18.73.76:3000/*` |
| `/gateway/*` | `http://172.18.73.22:3002/gateway/*` |
| `/*` (otros) | Archivos estáticos de React |

## 🚀 Despliegue

### Opción 1: Docker Compose (Recomendado)

```bash
# 1. Construir y levantar el contenedor
docker-compose up -d --build

# 2. Ver logs
docker-compose logs -f frontend

# 3. Verificar estado
docker-compose ps

# 4. Detener
docker-compose down
```

### Opción 2: Docker Manual

```bash
# 1. Construir imagen
docker build -t gateway-frontend .

# 2. Ejecutar contenedor
docker run -d \
  --name gateway-frontend \
  -p 80:80 \
  --restart unless-stopped \
  gateway-frontend

# 3. Ver logs
docker logs -f gateway-frontend

# 4. Detener y eliminar
docker stop gateway-frontend
docker rm gateway-frontend
```

### Opción 3: Build Manual (Sin Docker)

```bash
# 1. Instalar dependencias
npm install

# 2. Construir para producción
npm run build

# 3. Copiar build a servidor web
# El contenido de /build debe copiarse a /var/www/html o similar

# 4. Configurar Nginx manualmente
# Copiar nginx.conf a /etc/nginx/sites-available/
# Crear symlink en /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/gateway /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🧪 Verificación

### 1. Verificar que el frontend está corriendo

```bash
curl http://localhost/
```

### 2. Probar el reverse proxy

```bash
# Probar API Gateway
curl http://localhost/api/planeacion

# Probar servicio de login
curl http://localhost/auth/login

# Probar gateway general
curl http://localhost/gateway/crm/conversaciones
```

### 3. Verificar en el navegador

```
http://tu-servidor/
```

## 🔒 Configuración de Seguridad (Producción)

### 1. Usar HTTPS con SSL/TLS

Actualizar `nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name tu-dominio.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # ... resto de configuración
}

# Redireccionar HTTP a HTTPS
server {
    listen 80;
    server_name tu-dominio.com;
    return 301 https://$server_name$request_uri;
}
```

### 2. Añadir Variables de Entorno

Crear `.env.production`:

```env
REACT_APP_API_URL=/api
REACT_APP_AUTH_URL=/auth
REACT_APP_GATEWAY_URL=/gateway
```

## 🛠️ Troubleshooting

### Problema: No se cargan los archivos estáticos

**Solución**: Verificar que el build se copió correctamente
```bash
docker exec gateway-frontend ls -la /usr/share/nginx/html
```

### Problema: Error 502 Bad Gateway en /api

**Solución**: Verificar conectividad al backend
```bash
docker exec gateway-frontend ping 172.18.73.22
```

### Problema: Rutas de React (404 en refresh)

**Solución**: Ya está configurado `try_files` en nginx.conf para SPA

### Problema: CORS errors

**Solución**: El reverse proxy elimina problemas de CORS. Si persisten, verificar que las rutas usen el proxy.

## 📊 Monitoreo

### Ver logs en tiempo real
```bash
docker-compose logs -f frontend
```

### Ver métricas del contenedor
```bash
docker stats gateway-frontend
```

### Verificar salud del contenedor
```bash
docker inspect gateway-frontend | grep -A 5 "Health"
```

## 🔄 Actualización

```bash
# 1. Detener contenedor actual
docker-compose down

# 2. Actualizar código
git pull  # o actualizar archivos manualmente

# 3. Reconstruir y levantar
docker-compose up -d --build

# 4. Limpiar imágenes antiguas
docker image prune -f
```

## 📝 Notas Importantes

1. **Desarrollo vs Producción**: El archivo `rutas.js` detecta automáticamente el entorno
2. **Cache**: Los archivos estáticos tienen cache de 1 año
3. **Timeouts**: Configurados a 300s para peticiones largas
4. **Compresión**: Gzip habilitado para archivos text/css/js
5. **Health Check**: Docker verificará la salud cada 30s

## 🌐 Cambiar IPs del Backend

Si necesitas cambiar las IPs del backend, edita `nginx.conf`:

```nginx
location /api/ {
    proxy_pass http://NUEVA_IP:PUERTO/api/;
    # ...
}
```

Luego reconstruye:
```bash
docker-compose up -d --build
```

## 📞 Soporte

Para problemas o dudas, revisar:
- Logs: `docker-compose logs -f`
- Configuración: `nginx.conf`
- Build: `Dockerfile`
