# Recomendaciones para Profesionalizar el Desarrollo

> Registro de mejoras técnicas identificadas. Marca con `[x]` las implementadas.

---

## 1. Mejoras de calidad

- [ ] **Type hints completos**: Anotar todos los métodos de vistas, servicios y serializers con tipos de retorno explícitos (`-> None`, `-> Response`, etc.)
- [ ] **Logging estructurado**: Ampliar logging en `views.py` para CRUD (creación, edición, borrado) y en `serializers.py` para validaciones fallidas. Usar `logger.warning` para intentos de acceso denegado.
- [ ] **Manejo de errores específicos en `request_analysis()`**: Capturar `anthropic.APITimeoutError`, `anthropic.RateLimitError`, `anthropic.APIConnectionError` con mensajes de usuario apropiados en lugar del genérico 503.

## 2. Buenas prácticas

- [ ] **Service layer para dashboard**: Extraer la lógica de estadísticas de `DashboardView.get_context_data()` a `apps/dashboard/services.py` para facilitar tests unitarios.
- [ ] **Constantes médicas centralizadas**: Mover los límites de validación (50–300, 30–200, 30–220) a `apps/readings/constants.py`, compartido entre `serializers.py` y `forms.py`.
- [ ] **Señales para UserProfile**: Usar `post_save` signal en `User` para crear automáticamente `UserProfile` al registrar nuevos usuarios.

## 3. Seguridad

- [ ] **Rate limiting en `/api/v1/agent/analyze/`**: Instalar `django-ratelimit` y limitar a 10 análisis/usuario/hora para evitar costes inesperados en la API de Claude.
- [ ] **Timeout explícito en cliente Anthropic**: Ya configurado a 60 segundos en `services.py`. Revisar si es suficiente para períodos con muchos datos.
- [ ] **HTTPS con Certbot**: TLS obligatorio en producción. Añadir configuración SSL en `deploy/nginx/tension.conf` (hay bloque comentado).
- [ ] **Cabeceras de seguridad adicionales**: Añadir `Content-Security-Policy` en Nginx para proteger contra XSS.

## 4. Rendimiento

- [ ] **Prompt caching efectivo**: Verificar que `SYSTEM_PROMPT` en `prompts.py` supera los 2048 tokens mínimos para `claude-sonnet-4-6`. Confirmar `cache_read_input_tokens > 0` en logs tras la segunda llamada.
- [ ] **Índice funcional por fecha**: Si el volumen crece, añadir índice funcional `measured_at::date` en PostgreSQL para filtros por rango de fecha.
- [ ] **Paginación cursor en API**: Cambiar a `CursorPagination` en `REST_FRAMEWORK` para listas grandes (más eficiente que offset en tablas grandes).
- [ ] **Select related en DashboardView**: Añadir `.select_related('user')` si se muestran datos del usuario en el contexto.

## 5. Testing

- [ ] **Mock del cliente Anthropic**: Usar `unittest.mock.patch('anthropic.Anthropic')` en tests del agente para no consumir créditos y hacer tests deterministas.
- [ ] **Test de aislamiento de datos (crítico)**: Verificar que usuario B no puede acceder a lecturas de usuario A via API (`GET /api/v1/readings/`) ni via web (`/lecturas/{id}/`).
- [ ] **Tests de clasificación**: Tests unitarios para `BloodPressureReading.classification()` cubriendo todos los límites exactos de cada categoría AHA (valores en el límite, por encima y por debajo).
- [ ] **Test de exportación CSV**: Verificar que el CSV exportado contiene exactamente los campos esperados y solo los datos del usuario autenticado.
- [ ] **Tests de formulario**: Verificar validación cruzada diastólica < sistólica en el formulario web.

## 6. Deuda técnica

- [ ] **Streaming para análisis largos**: Para períodos con muchos datos (>500 lecturas), considerar `client.messages.stream()` con Server-Sent Events al frontend para feedback en tiempo real.
- [ ] **Exportación PDF**: Añadir `weasyprint` o `reportlab` para generar informes PDF con gráficas incluidas, listos para llevar al médico.
- [ ] **Alertas por email**: Notificación cuando una lectura supera umbrales peligrosos (>180/120 mmHg) usando `Django send_mail`. Pendiente de implementar.
- [ ] **Historial de análisis paginado**: La vista `/agente/` muestra los 10 últimos. Añadir paginación o botón "Ver más" para historiales largos.
- [ ] **Internacionalización (i18n)**: Las clasificaciones están hardcodeadas en español en el modelo. Considerar `gettext` si se necesita soporte multiidioma en el futuro.
