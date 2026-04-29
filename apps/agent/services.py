from __future__ import annotations

import logging
from datetime import date

from django.conf import settings
from django.db.models import Avg, Max, Min
from django.utils import timezone

from apps.readings.models import BloodPressureReading

from .prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_TIME_OF_DAY_LABELS = {
    "morning": "Mañana",
    "afternoon": "Tarde",
    "evening": "Noche",
    "night": "Madrugada",
    "": "Sin especificar",
}


def _build_analysis_prompt(user, date_from: date, date_to: date) -> tuple[str, int]:
    """
    Construye el prompt con estadísticas y lecturas individuales del período.
    Retorna (prompt_text, reading_count).
    """
    qs = BloodPressureReading.objects.filter(
        user=user,
        measured_at__date__gte=date_from,
        measured_at__date__lte=date_to,
    ).order_by("measured_at")

    count = qs.count()
    if count == 0:
        return "", 0

    # ── Estadísticas agregadas ──────────────────────────────────────────────
    stats = qs.aggregate(
        sys_avg=Avg("systolic"),
        sys_max=Max("systolic"),
        sys_min=Min("systolic"),
        dia_avg=Avg("diastolic"),
        dia_max=Max("diastolic"),
        dia_min=Min("diastolic"),
        pulse_avg=Avg("pulse"),
    )

    # ── Distribución por clasificación ─────────────────────────────────────
    dist: dict[str, int] = {
        "normal": 0, "elevated": 0,
        "hypertension_1": 0, "hypertension_2": 0, "crisis": 0,
    }
    readings_data = list(
        qs.values(
            "systolic", "diastolic", "pulse",
            "measured_at", "time_of_day", "notes",
        )
    )
    for r in readings_data:
        tmp = BloodPressureReading(systolic=r["systolic"], diastolic=r["diastolic"])
        dist[tmp.classification()] += 1

    # ── Distribución por momento del día ───────────────────────────────────
    tod_dist: dict[str, int] = {"morning": 0, "afternoon": 0, "evening": 0, "night": 0, "": 0}
    for r in readings_data:
        tod_dist[r["time_of_day"] or ""] += 1

    # ── Tendencia temporal (primera vs segunda mitad del período) ──────────
    mid = count // 2
    first_half = readings_data[:mid] if mid > 0 else readings_data
    second_half = readings_data[mid:] if mid > 0 else readings_data

    def _avg(lst: list, key: str) -> float | None:
        vals = [r[key] for r in lst if r[key] is not None]
        return sum(vals) / len(vals) if vals else None

    first_sys = _avg(first_half, "systolic")
    second_sys = _avg(second_half, "systolic")
    first_dia = _avg(first_half, "diastolic")
    second_dia = _avg(second_half, "diastolic")

    def _f(v: float | None) -> str:
        return f"{v:.1f}" if v is not None else "—"

    # ── Tabla de lecturas individuales ─────────────────────────────────────
    # Si hay <= 60 lecturas se muestran todas; si hay más, se toman hasta 60
    # priorizando lecturas con notas, crisis o HTA2.
    MAX_ROWS = 60
    if count <= MAX_ROWS:
        rows_to_show = readings_data
    else:
        # Priorizar lecturas con notas o clasificación preocupante
        priority = []
        normal_rows = []
        for r in readings_data:
            tmp = BloodPressureReading(systolic=r["systolic"], diastolic=r["diastolic"])
            cls = tmp.classification()
            if r["notes"] or cls in ("crisis", "hypertension_2"):
                priority.append(r)
            else:
                normal_rows.append(r)
        # Repartir: hasta MAX_ROWS/2 prioritarios + el resto normales
        half = MAX_ROWS // 2
        rows_to_show = priority[:half] + normal_rows[: MAX_ROWS - min(len(priority), half)]
        rows_to_show.sort(key=lambda r: r["measured_at"])

    # Construir tabla de lecturas
    table_lines = ["| Fecha | Hora | Momento | Sistólica | Diastólica | Pulso | Clasificación | Notas |",
                   "|-------|------|---------|-----------|------------|-------|---------------|-------|"]

    for r in rows_to_show:
        # Convertir measured_at a hora local
        dt_local = timezone.localtime(r["measured_at"])
        fecha = dt_local.strftime("%d/%m/%Y")
        hora = dt_local.strftime("%H:%M")
        momento = _TIME_OF_DAY_LABELS.get(r["time_of_day"] or "", "—")
        tmp = BloodPressureReading(systolic=r["systolic"], diastolic=r["diastolic"])
        cls_label = tmp.classification_label
        pulse_str = str(r["pulse"]) if r["pulse"] else "—"
        notes_str = r["notes"].replace("|", "/").replace("\n", " ")[:60] if r["notes"] else "—"
        table_lines.append(
            f"| {fecha} | {hora} | {momento} | {r['systolic']} | {r['diastolic']} | {pulse_str} | {cls_label} | {notes_str} |"
        )

    readings_table = "\n".join(table_lines)

    # ── Notas con contenido ─────────────────────────────────────────────────
    notes_list = [
        f"- {timezone.localtime(r['measured_at']).strftime('%d/%m/%Y %H:%M')}: {r['notes']}"
        for r in readings_data
        if r["notes"]
    ]
    notes_section = "\n".join(notes_list) if notes_list else "*(Sin notas registradas)*"

    # ── Momento del día con más lecturas elevadas ───────────────────────────
    tod_high: dict[str, int] = {"morning": 0, "afternoon": 0, "evening": 0, "night": 0, "": 0}
    for r in readings_data:
        tmp = BloodPressureReading(systolic=r["systolic"], diastolic=r["diastolic"])
        if tmp.classification() in ("hypertension_1", "hypertension_2", "crisis"):
            tod_high[r["time_of_day"] or ""] += 1

    tod_high_str = ", ".join(
        f"{_TIME_OF_DAY_LABELS[k]}: {v}"
        for k, v in tod_high.items()
        if v > 0
    ) or "ninguna"

    suffix = f" (mostrando {len(rows_to_show)} representativas)" if count > MAX_ROWS else ""

    try:
        medical_context = user.profile.medical_context.strip()
    except Exception:
        medical_context = ""

    prompt = f"""Analiza las siguientes lecturas de presión arterial del período \
{date_from.strftime('%d/%m/%Y')} al {date_to.strftime('%d/%m/%Y')}:
{f"""
## Contexto médico del paciente

{medical_context}
""" if medical_context else ""}
## Resumen estadístico ({count} lecturas{suffix})

| Métrica | Sistólica (mmHg) | Diastólica (mmHg) |
|---------|-----------------|------------------|
| Promedio | {_f(stats['sys_avg'])} | {_f(stats['dia_avg'])} |
| Máximo | {_f(stats['sys_max'])} | {_f(stats['dia_max'])} |
| Mínimo | {_f(stats['sys_min'])} | {_f(stats['dia_min'])} |

Pulso promedio: {_f(stats['pulse_avg'])} ppm

## Distribución por clasificación AHA/ACC 2017

- Normal: {dist['normal']} lecturas ({dist['normal']/count*100:.1f}%)
- Elevada: {dist['elevated']} lecturas ({dist['elevated']/count*100:.1f}%)
- HTA Estadio 1: {dist['hypertension_1']} lecturas ({dist['hypertension_1']/count*100:.1f}%)
- HTA Estadio 2: {dist['hypertension_2']} lecturas ({dist['hypertension_2']/count*100:.1f}%)
- Crisis hipertensiva: {dist['crisis']} lecturas ({dist['crisis']/count*100:.1f}%)

## Distribución por momento del día

- Mañana: {tod_dist['morning']} lecturas
- Tarde: {tod_dist['afternoon']} lecturas
- Noche: {tod_dist['evening']} lecturas
- Madrugada: {tod_dist['night']} lecturas
- Sin especificar: {tod_dist['']} lecturas

Lecturas elevadas (HTA 1+2+Crisis) por momento: {tod_high_str}

## Tendencia temporal

- Primera mitad del período ({len(first_half)} lecturas): \
sistólica {_f(first_sys)} / diastólica {_f(first_dia)} mmHg (promedio)
- Segunda mitad del período ({len(second_half)} lecturas): \
sistólica {_f(second_sys)} / diastólica {_f(second_dia)} mmHg (promedio)

## Lecturas individuales

{readings_table}

## Notas del usuario

{notes_section}

---

Por favor, proporciona un análisis detallado de estos datos siguiendo el formato indicado. \
Ten en cuenta las fechas y horas concretas, el momento del día de cada lectura, \
las notas del usuario y la tendencia temporal entre la primera y segunda mitad del período."""

    return prompt, count


def request_analysis(user, date_from: date, date_to: date) -> dict:
    """
    Llama a Claude API y guarda el análisis en la base de datos.

    Retorna dict con 'analysis_text', 'reading_count', 'model_used'.
    Lanza ValueError si no hay lecturas.
    Lanza RuntimeError si la API key no está configurada.
    """
    import anthropic

    prompt_text, reading_count = _build_analysis_prompt(user, date_from, date_to)
    if reading_count == 0:
        raise ValueError("No hay lecturas en el período seleccionado.")

    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY no configurada en el servidor.")

    client = anthropic.Anthropic(api_key=api_key, timeout=60.0)

    logger.info(
        "agent: solicitando análisis para user=%s, período=%s a %s, lecturas=%d",
        user.username,
        date_from,
        date_to,
        reading_count,
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {"role": "user", "content": prompt_text}
        ],
    )

    analysis_text = next(
        (block.text for block in response.content if block.type == "text"),
        "",
    )

    cache_read = getattr(response.usage, "cache_read_input_tokens", 0)
    logger.info(
        "agent: análisis completado para user=%s — tokens_entrada=%d, cache_read=%d",
        user.username,
        response.usage.input_tokens,
        cache_read,
    )

    from .models import AgentAnalysis

    AgentAnalysis.objects.create(
        user=user,
        date_from=date_from,
        date_to=date_to,
        reading_count=reading_count,
        analysis_text=analysis_text,
        model_used="claude-sonnet-4-6",
    )

    return {
        "analysis_text": analysis_text,
        "reading_count": reading_count,
        "model_used": "claude-sonnet-4-6",
    }
