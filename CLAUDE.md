# Tension — Documentación del Proyecto

Sistema Django multi-usuario para el registro diario de lecturas de presión arterial. Incluye API REST, dashboard web responsivo (mobile-first), gráficas históricas con Chart.js y un agente IA basado en Claude API que analiza e interpreta los datos bajo demanda.

---

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Runtime | Python 3.11 + venv |
| Framework | Django 5.2 |
| API REST | Django REST Framework 3.16 |
| Auth API | DRF Token + JWT (djangorestframework-simplejwt) |
| Base de datos | PostgreSQL + psycopg2-binary |
| Variables entorno | django-environ |
| CSS | Tailwind CSS (CDN) |
| Gráficas | Chart.js 4.4.4 (CDN) |
| Agente IA | Anthropic Python SDK (`claude-sonnet-4-6`) |
| Servidor WSGI | Gunicorn |
| Proxy inverso | Nginx |
| Deploy | systemd en VPS |

---

## Estructura del Proyecto

```
tension/
├── .env                         # Variables secretas — NO subir a git
├── .env.example                 # Plantilla documentada
├── .gitignore
├── CLAUDE.md                    # Este archivo
├── Recomendaciones.md           # Registro de mejoras técnicas
├── manage.py
├── requirements.txt
├── requirements-dev.txt
├── tension_project/             # Configuración Django
│   ├── settings/
│   │   ├── base.py              # Config común
│   │   ├── development.py       # DEBUG=True, debug-toolbar
│   │   └── production.py       # HTTPS, HSTS, cookies secure
│   ├── urls.py                  # Router global
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/                # Registro, login, perfiles
│   │   ├── models.py            # UserProfile
│   │   ├── forms.py             # RegisterForm
│   │   ├── views.py             # RegisterView, ProfileView
│   │   ├── urls.py
│   │   └── admin.py
│   ├── readings/                # App central — lecturas PA
│   │   ├── models.py            # BloodPressureReading
│   │   ├── forms.py             # BloodPressureReadingForm
│   │   ├── views.py             # CBVs web + BloodPressureReadingViewSet
│   │   ├── serializers.py       # Serializer + validaciones médicas + readings_to_csv()
│   │   ├── urls.py              # Vistas web
│   │   ├── api_urls.py          # DefaultRouter DRF
│   │   ├── health_urls.py       # GET /health/ sin auth
│   │   └── admin.py
│   ├── dashboard/               # Vista principal
│   │   ├── views.py             # DashboardView
│   │   └── urls.py
│   ├── analytics/               # Gráficas y estadísticas
│   │   ├── services.py          # get_chart_data() — datos diarios TruncDate
│   │   ├── views.py             # ChartsView + chart_data_api
│   │   ├── urls.py              # Web
│   │   └── api_urls.py          # API
│   └── agent/                   # Agente IA Claude
│       ├── models.py            # AgentAnalysis
│       ├── prompts.py           # SYSTEM_PROMPT médico (>2048 tokens para caching)
│       ├── services.py          # request_analysis() con prompt caching
│       ├── serializers.py
│       ├── views.py             # AgentView + AnalysisRequestView + AnalysisListView
│       ├── urls.py              # Web
│       └── api_urls.py          # API
├── templates/
│   ├── base.html                # Tailwind CDN, dark mode, navbar mobile
│   ├── registration/            # login.html, register.html
│   ├── readings/                # list.html, form.html, confirm_delete.html
│   ├── dashboard/               # index.html
│   ├── analytics/               # charts.html (Chart.js)
│   └── agent/                   # index.html (formulario + historial)
├── static/
└── deploy/
    ├── nginx/tension.conf
    └── systemd/tension.service
```

---

## Variables .env Requeridas

```env
SECRET_KEY=genera-con-python-secrets-token-hex-32
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://tension_user:password@localhost:5432/tension
ANTHROPIC_API_KEY=sk-ant-...
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu@email.com
EMAIL_HOST_PASSWORD=app-password
DEFAULT_FROM_EMAIL=tension@tudominio.com
```

---

## Primeros Pasos (desarrollo)

```bash
# 1. Entorno virtual
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/Mac

# 2. Dependencias
pip install -r requirements-dev.txt

# 3. Configuración
cp .env.example .env
# Editar .env con DATABASE_URL y ANTHROPIC_API_KEY

# 4. Base de datos PostgreSQL
# psql -U postgres
# CREATE DATABASE tension;
# CREATE USER tension_user WITH PASSWORD 'tu_password';
# GRANT ALL PRIVILEGES ON DATABASE tension TO tension_user;

# 5. Migraciones
python manage.py migrate
python manage.py createsuperuser

# 6. Arrancar servidor
python manage.py runserver
```

---

## Modelos de Datos

### BloodPressureReading (`apps/readings/models.py`)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `user` | FK → User | Propietario de la lectura |
| `systolic` | PositiveSmallIntegerField | Sistólica (mmHg) |
| `diastolic` | PositiveSmallIntegerField | Diastólica (mmHg) |
| `pulse` | PositiveSmallIntegerField? | Pulso (ppm), opcional |
| `measured_at` | DateTimeField | Fecha y hora de la medición |
| `time_of_day` | CharField (choices) | Mañana/Tarde/Noche/Madrugada |
| `notes` | TextField | Notas libres |
| `created_at` | DateTimeField | Auto generado |

Métodos clave:
- `classification()` → `str`: Clasificación AHA/ACC 2017 (normal/elevated/hypertension_1/hypertension_2/crisis)
- `classification_label` → `str`: Etiqueta en español
- `classification_color` → `str`: Clases Tailwind para color

### AgentAnalysis (`apps/agent/models.py`)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `user` | FK → User | Usuario que solicitó el análisis |
| `requested_at` | DateTimeField | Auto generado |
| `date_from` / `date_to` | DateField | Período analizado |
| `reading_count` | IntegerField | Lecturas incluidas |
| `analysis_text` | TextField | Respuesta de Claude |
| `model_used` | CharField | Modelo Claude utilizado |

---

## Endpoints Principales

### Web (requieren login)

| URL | Vista | Descripción |
|-----|-------|-------------|
| `/` | DashboardView | Últimas lecturas + stats semana |
| `/lecturas/` | ReadingListView | Historial con filtros de fecha |
| `/lecturas/nueva/` | ReadingCreateView | Formulario nueva lectura |
| `/lecturas/{id}/editar/` | ReadingUpdateView | Editar lectura |
| `/lecturas/{id}/eliminar/` | ReadingDeleteView | Eliminar lectura |
| `/graficas/` | ChartsView | Gráficas Chart.js entre fechas |
| `/agente/` | AgentView | Solicitar y ver análisis IA |

### API REST (requieren Token o JWT)

| Método | URL | Descripción |
|--------|-----|-------------|
| GET/POST | `/api/v1/readings/` | Listar/crear lecturas |
| GET/PATCH/DELETE | `/api/v1/readings/{id}/` | Detalle lectura |
| GET | `/api/v1/readings/stats/` | Estadísticas del período |
| GET | `/api/v1/readings/chart/` | Datos JSON por lectura |
| GET | `/api/v1/readings/export/` | Descarga CSV |
| GET | `/api/v1/analytics/chart/` | Datos diarios agregados |
| POST | `/api/v1/agent/analyze/` | Solicitar análisis IA |
| GET | `/api/v1/agent/analyses/` | Historial de análisis |
| POST | `/api/v1/token/` | Obtener token DRF |
| POST | `/api/v1/jwt/` | Obtener JWT |
| GET | `/health/` | Health check (sin auth) |

---

## Clasificación AHA/ACC 2017

| Categoría | Sistólica | | Diastólica | Color |
|-----------|-----------|---|------------|-------|
| Normal | < 120 | Y | < 80 | Verde |
| Elevada | 120–129 | Y | < 80 | Amarillo |
| HTA Estadio 1 | 130–139 | O | 80–89 | Naranja |
| HTA Estadio 2 | ≥ 140 | O | ≥ 90 | Rojo |
| Crisis hipertensiva | > 180 | O | > 120 | Rojo oscuro |

---

## Reglas de Desarrollo

1. **Filtrar SIEMPRE por usuario**: `filter(user=request.user)` en todo QuerySet protegido. Esta regla nunca tiene excepciones.
2. **Campo `user` nunca en serializer/form**: Se asigna solo en `perform_create(serializer)` o `form_valid(form)`, nunca desde el payload del cliente.
3. **CBVs con `LoginRequiredMixin`**: Para todas las vistas web protegidas. FBVs solo para `/health/`.
4. **Validaciones médicas en serializer**: SBP: 50–300, DBP: 30–200, pulse: 30–220; y validación cruzada diastólica < sistólica.
5. **Agente IA**: Guardar cada análisis en `AgentAnalysis`. Usar `cache_control: {type: ephemeral}` en el system prompt para activar prompt caching de Anthropic.
6. **Configuración desde `.env`**: Nunca hardcodear credenciales. Sí commitear `.env.example` actualizado. No commitear `.env`.
7. **Modelos**: Todo modelo con `__str__`, `db_index=True` en campos filtrados frecuentemente.
8. **Serializers DRF**: `read_only_fields` explícito, validar rangos en el dominio de la aplicación.

---

## Despliegue en VPS

```bash
# En el VPS (Ubuntu/Debian)
cd /home/antonio
git clone <repo> Tension
cd Tension
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar .env con valores de producción
cp .env.example .env
# Editar .env

# Migraciones y estáticos
python manage.py migrate
python manage.py collectstatic --noinput

# Instalar servicio systemd
sudo cp deploy/systemd/tension.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tension
sudo systemctl start tension

# Configurar Nginx
sudo cp deploy/nginx/tension.conf /etc/nginx/sites-available/tension
sudo ln -s /etc/nginx/sites-available/tension /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## Comportamiento en Planificación

Siempre que se presente un plan de implementación, debe incluirse una sección final **"Recomendaciones para Profesionalizar el Desarrollo"** con estos puntos (solo los relevantes al contexto):

1. **Mejoras de calidad**: type hints, logging estructurado, manejo de errores
2. **Buenas prácticas**: patrones de diseño aplicables, separación de responsabilidades
3. **Seguridad**: validaciones, sanitización de datos, permisos
4. **Rendimiento**: índices DB, caché Redis, queries N+1, paginación
5. **Testing**: qué tests agregar para el cambio propuesto
6. **Deuda técnica**: TODOs relacionados que podrían resolverse con el cambio

Las recomendaciones nuevas se persisten en `Recomendaciones.md` bajo su categoría correspondiente, marcando con `[x]` las implementadas.

---

## Comandos Frecuentes

```bash
# Desarrollo
python manage.py runserver
python manage.py shell

# Base de datos
python manage.py makemigrations
python manage.py migrate
python manage.py dbshell

# Producción
python manage.py collectstatic --noinput
sudo systemctl status tension
sudo journalctl -u tension -f    # Logs en tiempo real
sudo systemctl restart tension
```
