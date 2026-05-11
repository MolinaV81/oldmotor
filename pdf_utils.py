from __future__ import annotations

import os
from typing import Dict, Any, List, Tuple

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm


def _wrap_text(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    leading: float = 12,
    font_name: str = "Helvetica",
    font_size: int = 10,
) -> float:
    if not text:
        return y

    c.setFont(font_name, font_size)

    words = str(text).split()
    line = ""
    for w in words:
        test = (line + " " + w).strip()
        if c.stringWidth(test, font_name, font_size) <= max_width:
            line = test
        else:
            if line:
                c.drawString(x, y, line)
                y -= leading
            line = w

    if line:
        c.drawString(x, y, line)
        y -= leading

    return y


def _checkbox_line_wrapped(
    c: canvas.Canvas,
    x: float,
    y: float,
    label: str,
    checked: bool,
    max_width: float,
    leading: float = 12,
) -> float:
    box = 10
    text_x = x + box + 8

    c.rect(x, y - 8, box, box, stroke=1, fill=0)

    if checked:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x + 2, y - 9, "x")

    c.setFont("Helvetica", 10)
    y = _wrap_text(
        c=c,
        text=label,
        x=text_x,
        y=y - 7,
        max_width=max_width,
        leading=leading,
        font_name="Helvetica",
        font_size=10,
    )

    return y + 7


def generate_service_report_pdf(
    data: Dict[str, Any],
    out_path: str,
    logo_path: str = "logo.jpg",
) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    c = canvas.Canvas(out_path, pagesize=letter)
    width, height = letter

    margin_x = 2 * cm
    y = height - 2 * cm

    # Header con logo
    if os.path.exists(logo_path):
        c.drawImage(
            logo_path,
            margin_x,
            y - 45,
            width=120,
            height=40,
            preserveAspectRatio=True,
            mask="auto",
        )

    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin_x + 140, y - 15, "REPORTE DE SERVICIO")

    c.setFont("Helvetica", 10)
    c.drawString(margin_x + 140, y - 32, f"Folio: {data.get('folio','')}")
    c.drawString(margin_x + 260, y - 32, f"Fecha registro: {data.get('timestamp','')}")

    y -= 70
    c.line(margin_x, y, width - margin_x, y)
    y -= 18

    # Datos del cliente
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_x, y, "Datos del cliente")
    y -= 14
    c.setFont("Helvetica", 10)
    c.drawString(margin_x, y, f"Nombre: {data.get('cliente_nombre','')}")
    c.drawString(margin_x + 280, y, f"Tel: {data.get('cliente_tel','')}")
    y -= 14
    c.drawString(margin_x, y, f"Fecha ingreso: {data.get('fecha_ingreso','')}")
    c.drawString(margin_x + 280, y, f"Fecha entrega: {data.get('fecha_entrega','')}")
    y -= 18

    # Datos de la moto
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_x, y, "Datos de la motocicleta")
    y -= 14
    c.setFont("Helvetica", 10)
    c.drawString(margin_x, y, f"Marca: {data.get('moto_marca','')}")
    c.drawString(margin_x + 200, y, f"Modelo: {data.get('moto_modelo','')}")
    c.drawString(margin_x + 410, y, f"Año: {data.get('moto_anio','')}")
    y -= 14
    c.drawString(margin_x, y, f"Kilometraje: {data.get('moto_km','')}")
    c.drawString(margin_x + 280, y, f"Placas/Serie: {data.get('moto_placas_serie','')}")
    y -= 18

    # ✅ NUEVO: Observaciones de recepción
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_x, y, "Observaciones de recepción")
    y -= 14
    c.setFont("Helvetica", 10)

    y = _wrap_text(
        c=c,
        text=str(data.get("observaciones_recepcion", "") or ""),
        x=margin_x,
        y=y,
        max_width=width - 2 * margin_x,
        leading=12,
        font_name="Helvetica",
        font_size=10,
    )
    y -= 6

    c.line(margin_x, y, width - margin_x, y)
    y -= 16

    # Config columnas
    left_x = margin_x
    right_x = width / 2 + 0.5 * cm
    col_w = width / 2 - margin_x - 0.5 * cm

    sections: List[Tuple[str, List[Tuple[str, str]], str]] = [
        (
            "Sistema de frenos",
            [
                ("frenos_calipers", "Mantenimiento a cálipers y ejes de cálipers"),
                ("frenos_balatas", "Mantenimiento a balatas"),
                ("frenos_grosor", "Medición de grosor y desgaste de balatas"),
                ("frenos_mangueras", "Mantenimiento y revisión de mangueras"),
                ("frenos_liquido", "Revisión de líquido de frenos"),
                ("frenos_purga", "Purga de sistema de frenos delanteros y traseros"),
            ],
            "obs_frenos",
        ),
        (
            "Motor",
            [
                ("motor_prueba_aceite", "Prueba de propiedades del aceite"),
                ("motor_residuos", "Análisis de residuos de asentamiento interno"),
                ("motor_compresion", "Revisión de compresión"),
                ("motor_balancines", "Ajuste de balancines (según manual)"),
                ("motor_cuerpo_aceleracion", "Limpieza de cuerpo de aceleración"),
                ("motor_bujia", "Cambio de bujía"),
                ("motor_aceite_motul", "Cambio de aceite (Motul sintético)"),
                ("motor_filtro_aceite", "Cambio de filtro de aceite"),
            ],
            "obs_motor",
        ),
        (
            "Desplazamiento (tracción/transmisión)",
            [
                ("despl_cadena", "Lubricación y tensión de cadena"),
                ("despl_pinon_seguro", "Revisión de piñón y seguro"),
                ("despl_flecha_transmision", "Revisión de flecha de transmisión"),
                ("despl_sprocket_flecha", "Mantenimiento a sprocket y flecha"),
                ("despl_retenes", "Revisión de retenes de transmisión"),
            ],
            "obs_despl",
        ),
        (
            "Sistema de carga",
            [
                ("carga_estator_regulador_bateria", "Escaneo de carga (estator/regulador/batería)"),
                ("carga_encendido_circuito", "Escaneo de encendido y circuito"),
                ("carga_conectores_arnes", "Mantenimiento a conectores del arnés"),
                ("carga_mandos_general", "Revisión de mandos y funcionamiento general"),
            ],
            "obs_carga",
        ),
        (
            "Suspensión",
            [
                ("susp_barras_amortiguadores", "Revisión de barras y amortiguadores"),
                ("susp_retenes", "Limpieza de retenes"),
            ],
            "obs_susp",
        ),
    ]

    c.setFont("Helvetica", 10)
    col_y_left = y
    col_y_right = y

    for idx, (title, items, obs_key) in enumerate(sections):
        use_left = (idx % 2 == 0)
        x = left_x if use_left else right_x
        cy = col_y_left if use_left else col_y_right

        needed = 14 + len(items) * 24 + 70
        if cy - needed < 2 * cm:
            c.showPage()
            y = height - 2 * cm
            col_y_left = y
            col_y_right = y
            cy = y

            c.setFont("Helvetica-Bold", 14)
            c.drawString(margin_x, y, "REPORTE DE SERVICIO (continuación)")
            y -= 18
            c.setFont("Helvetica", 10)

        c.setFont("Helvetica-Bold", 11)
        c.drawString(x, cy, title)
        cy -= 14

        c.setFont("Helvetica", 10)
        text_max_width = col_w - 18

        for key, label in items:
            cy = _checkbox_line_wrapped(
                c=c,
                x=x,
                y=cy,
                label=label,
                checked=bool(data.get(key)),
                max_width=text_max_width,
                leading=12,
            )
            cy -= 2

        cy -= 4
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, cy, "Observaciones:")
        cy -= 12

        c.setFont("Helvetica", 10)
        cy = _wrap_text(
            c=c,
            text=str(data.get(obs_key, "") or ""),
            x=x,
            y=cy,
            max_width=col_w,
            leading=12,
            font_name="Helvetica",
            font_size=10,
        )
        cy -= 8

        if use_left:
            col_y_left = cy
        else:
            col_y_right = cy

    y = min(col_y_left, col_y_right) - 10
    c.line(margin_x, y, width - margin_x, y)
    y -= 16

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_x, y, "Recomendaciones adicionales")
    y -= 14

    c.setFont("Helvetica", 10)
    y = _wrap_text(
        c=c,
        text=str(data.get("recomendaciones", "") or ""),
        x=margin_x,
        y=y,
        max_width=width - 2 * margin_x,
        leading=12,
        font_name="Helvetica",
        font_size=10,
    )
    y -= 6

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_x, y, "Técnico responsable")
    y -= 14

    c.setFont("Helvetica", 10)
    c.drawString(margin_x, y, f"Nombre: {data.get('tecnico_responsable','')}")
    y -= 14

    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_x, y, "Comentarios del técnico:")
    y -= 12

    c.setFont("Helvetica", 10)
    _wrap_text(
        c=c,
        text=str(data.get("comentarios_tecnico", "") or ""),
        x=margin_x,
        y=y,
        max_width=width - 2 * margin_x,
        leading=12,
        font_name="Helvetica",
        font_size=10,
    )

    c.save()
