from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
import streamlit as st

from storage import append_record, load_records, ensure_dirs
from pdf_utils import generate_service_report_pdf


# =========================
# CONFIGURACIÓN DE PÁGINA
# =========================
st.set_page_config(page_title="Old Motor Garage | Reportes", layout="wide")


# =========================
# LOGIN
# =========================
def login():
    st.title("🔒 Acceso restringido")
    st.write("Ingresa tu usuario y contraseña para continuar.")

    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):
        if (
            usuario == st.secrets["APP_USER"]
            and password == st.secrets["APP_PASSWORD"]
        ):
            st.session_state["logueada"] = True
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")


if "logueada" not in st.session_state:
    st.session_state["logueada"] = False

if not st.session_state["logueada"]:
    login()
    st.stop()

if st.sidebar.button("Cerrar sesión"):
    st.session_state["logueada"] = False
    st.rerun()


# =========================
# APP NORMAL
# =========================
LOGO_PATH = "logo.jpg"

ensure_dirs()


def now_folio() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _to_bool(v) -> bool:
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        if pd.isna(v):
            return False
        return bool(int(v))
    if isinstance(v, str):
        s = v.strip().lower()
        return s in ("true", "1", "si", "sí", "x", "checked")
    return False


def _norm_phone(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    return "".join(ch for ch in s if ch.isdigit())


def row_to_record(row: pd.Series) -> dict:
    record = row.to_dict()

    checkbox_keys = [
        "frenos_calipers", "frenos_balatas", "frenos_grosor", "frenos_mangueras",
        "frenos_liquido", "frenos_purga",
        "motor_prueba_aceite", "motor_residuos", "motor_compresion", "motor_balancines",
        "motor_cuerpo_aceleracion", "motor_bujia", "motor_aceite_motul", "motor_filtro_aceite",
        "despl_cadena", "despl_pinon_seguro", "despl_flecha_transmision",
        "despl_sprocket_flecha", "despl_retenes",
        "carga_estator_regulador_bateria", "carga_encendido_circuito",
        "carga_conectores_arnes", "carga_mandos_general",
        "susp_barras_amortiguadores", "susp_retenes",
    ]

    for k in checkbox_keys:
        record[k] = _to_bool(record.get(k))

    text_keys = [
        "cliente_nombre", "cliente_tel", "fecha_ingreso", "fecha_entrega",
        "moto_marca", "moto_modelo", "moto_anio", "moto_km", "moto_placas_serie",
        "observaciones_recepcion",
        "obs_frenos", "obs_motor", "obs_despl", "obs_carga", "obs_susp",
        "recomendaciones", "tecnico_responsable", "comentarios_tecnico",
        "folio", "timestamp"
    ]

    for k in text_keys:
        v = record.get(k, "")
        if pd.isna(v):
            record[k] = ""
        else:
            record[k] = str(v)

    return record


st.title("📄 Old Motor Garage — Reporte de Servicio")

tab1, tab2 = st.tabs(["🧾 Captura", "🔎 Consulta"])


with tab1:
    st.subheader("Captura rápida del servicio")

    if not os.path.exists(LOGO_PATH):
        st.warning("No encontré logo.jpg en el mismo directorio que app.py. Colócalo ahí para que salga en el PDF.")

    colA, colB = st.columns(2)

    with colA:
        st.markdown("### Datos del cliente")
        cliente_nombre = st.text_input("Nombre")
        cliente_tel = st.text_input("Teléfono / WhatsApp")
        fecha_ingreso = st.date_input("Fecha de ingreso")
        fecha_entrega = st.date_input("Fecha de entrega")

    with colB:
        st.markdown("### Datos de la motocicleta")
        moto_marca = st.text_input("Marca")
        moto_modelo = st.text_input("Modelo")
        moto_anio = st.text_input("Año")
        moto_km = st.text_input("Kilometraje")
        moto_placas_serie = st.text_input("Placas / Serie")

    st.markdown("### Observaciones de recepción")
    observaciones_recepcion = st.text_area(
        "Describe el estado en que llega la moto / detalles que comenta el cliente / accesorios entregados, etc.",
        height=120
    )

    st.divider()

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### Sistema de frenos")
        frenos_calipers = st.checkbox("Mantenimiento a cálipers y ejes de cálipers", value=True)
        frenos_balatas = st.checkbox("Mantenimiento a balatas", value=True)
        frenos_grosor = st.checkbox("Medición de grosor y desgaste de balatas", value=True)
        frenos_mangueras = st.checkbox("Mantenimiento y revisión de mangueras", value=True)
        frenos_liquido = st.checkbox("Revisión de líquido de frenos", value=True)
        frenos_purga = st.checkbox("Purga de sistema de frenos delanteros y traseros", value=True)
        obs_frenos = st.text_area("Observaciones frenos", height=90)

    with c2:
        st.markdown("### Motor")
        motor_prueba_aceite = st.checkbox("Prueba de propiedades del aceite", value=True)
        motor_residuos = st.checkbox("Análisis de residuos de asentamiento interno", value=True)
        motor_compresion = st.checkbox("Revisión de compresión", value=True)
        motor_balancines = st.checkbox("Ajuste de balancines (según manual)", value=True)
        motor_cuerpo_aceleracion = st.checkbox("Limpieza de cuerpo de aceleración", value=True)
        motor_bujia = st.checkbox("Cambio de bujía", value=True)
        motor_aceite_motul = st.checkbox("Cambio de aceite Motul sintético", value=True)
        motor_filtro_aceite = st.checkbox("Cambio de filtro de aceite", value=True)
        obs_motor = st.text_area("Observaciones motor", height=90)

    with c3:
        st.markdown("### Desplazamiento")
        despl_cadena = st.checkbox("Lubricación y tensión de cadena", value=True)
        despl_pinon_seguro = st.checkbox("Revisión de piñón y seguro", value=True)
        despl_flecha_transmision = st.checkbox("Revisión de flecha de transmisión", value=True)
        despl_sprocket_flecha = st.checkbox("Mantenimiento a sprocket y flecha", value=True)
        despl_retenes = st.checkbox("Revisión de retenes de transmisión", value=True)
        obs_despl = st.text_area("Observaciones desplazamiento", height=90)

    st.divider()

    c4, c5 = st.columns(2)

    with c4:
        st.markdown("### Sistema de carga")
        carga_estator_regulador_bateria = st.checkbox("Escaneo de carga estator/regulador/batería", value=True)
        carga_encendido_circuito = st.checkbox("Escaneo de encendido y circuito", value=True)
        carga_conectores_arnes = st.checkbox("Mantenimiento a conectores del arnés", value=True)
        carga_mandos_general = st.checkbox("Revisión de mandos y funcionamiento general", value=True)
        obs_carga = st.text_area("Observaciones carga", height=90)

    with c5:
        st.markdown("### Suspensión")
        susp_barras_amortiguadores = st.checkbox("Revisión de barras y amortiguadores", value=True)
        susp_retenes = st.checkbox("Limpieza de retenes", value=True)
        obs_susp = st.text_area("Observaciones suspensión", height=90)

    st.divider()

    recomendaciones = st.text_area("### Recomendaciones adicionales", height=110)
    tecnico_responsable = st.text_input("Técnico responsable")
    comentarios_tecnico = st.text_area("Comentarios del técnico", height=110)

    st.divider()

    guardar = st.button("✅ Guardar PDF + Excel", use_container_width=True)

    if guardar:
        folio = now_folio()
        pdf_path = os.path.join("output_pdfs", f"reporte_{folio}.pdf")

        record = {
            "folio": folio,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "cliente_nombre": cliente_nombre,
            "cliente_tel": cliente_tel,
            "fecha_ingreso": str(fecha_ingreso),
            "fecha_entrega": str(fecha_entrega),
            "moto_marca": moto_marca,
            "moto_modelo": moto_modelo,
            "moto_anio": moto_anio,
            "moto_km": moto_km,
            "moto_placas_serie": moto_placas_serie,
            "observaciones_recepcion": observaciones_recepcion,
            "frenos_calipers": frenos_calipers,
            "frenos_balatas": frenos_balatas,
            "frenos_grosor": frenos_grosor,
            "frenos_mangueras": frenos_mangueras,
            "frenos_liquido": frenos_liquido,
            "frenos_purga": frenos_purga,
            "obs_frenos": obs_frenos,
            "motor_prueba_aceite": motor_prueba_aceite,
            "motor_residuos": motor_residuos,
            "motor_compresion": motor_compresion,
            "motor_balancines": motor_balancines,
            "motor_cuerpo_aceleracion": motor_cuerpo_aceleracion,
            "motor_bujia": motor_bujia,
            "motor_aceite_motul": motor_aceite_motul,
            "motor_filtro_aceite": motor_filtro_aceite,
            "obs_motor": obs_motor,
            "despl_cadena": despl_cadena,
            "despl_pinon_seguro": despl_pinon_seguro,
            "despl_flecha_transmision": despl_flecha_transmision,
            "despl_sprocket_flecha": despl_sprocket_flecha,
            "despl_retenes": despl_retenes,
            "obs_despl": obs_despl,
            "carga_estator_regulador_bateria": carga_estator_regulador_bateria,
            "carga_encendido_circuito": carga_encendido_circuito,
            "carga_conectores_arnes": carga_conectores_arnes,
            "carga_mandos_general": carga_mandos_general,
            "obs_carga": obs_carga,
            "susp_barras_amortiguadores": susp_barras_amortiguadores,
            "susp_retenes": susp_retenes,
            "obs_susp": obs_susp,
            "recomendaciones": recomendaciones,
            "tecnico_responsable": tecnico_responsable,
            "comentarios_tecnico": comentarios_tecnico,
        }

        append_record(record)
        generate_service_report_pdf(record, pdf_path, logo_path=LOGO_PATH)

        st.success("Listo: guardé el registro en Excel y generé el PDF.")

        with open(pdf_path, "rb") as f:
            st.download_button(
                "⬇️ Descargar PDF",
                data=f,
                file_name=os.path.basename(pdf_path),
                mime="application/pdf",
                use_container_width=True,
            )


with tab2:
    st.subheader("Consulta de reportes Excel")

    df = load_records()

    if df.empty:
        st.info("Aún no hay registros. Guarda tu primer reporte en la pestaña Captura.")
    else:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            filtro_cliente = st.text_input("Cliente contiene", key="fc")
        with col2:
            filtro_tel = st.text_input("Teléfono contiene", key="ftel")
        with col3:
            filtro_marca = st.text_input("Marca contiene", key="fm")
        with col4:
            filtro_tecnico = st.text_input("Técnico contiene", key="ft")

        df_view = df.copy()

        if "cliente_nombre" in df_view.columns and filtro_cliente:
            df_view = df_view[df_view["cliente_nombre"].astype(str).str.contains(filtro_cliente, case=False, na=False)]
        if "cliente_tel" in df_view.columns and filtro_tel:
            df_view = df_view[df_view["cliente_tel"].astype(str).str.contains(filtro_tel, case=False, na=False)]
        if "moto_marca" in df_view.columns and filtro_marca:
            df_view = df_view[df_view["moto_marca"].astype(str).str.contains(filtro_marca, case=False, na=False)]
        if "tecnico_responsable" in df_view.columns and filtro_tecnico:
            df_view = df_view[df_view["tecnico_responsable"].astype(str).str.contains(filtro_tecnico, case=False, na=False)]

        st.dataframe(df_view, use_container_width=True)

        st.divider()
        st.markdown("## 🔁 Re-generar PDF por teléfono")

        if "cliente_tel" not in df.columns or "folio" not in df.columns:
            st.warning("Necesito columnas cliente_tel y folio en el Excel.")
        else:
            phone_query = st.text_input("Buscar registro por teléfono", key="regen_phone")

            if not phone_query.strip():
                st.info("Escribe un teléfono o parte del teléfono para buscar el registro.")
            else:
                q = _norm_phone(phone_query)
                df_candidates = df.copy()
                df_candidates["__tel_norm__"] = df_candidates["cliente_tel"].apply(_norm_phone)

                if q:
                    df_candidates = df_candidates[df_candidates["__tel_norm__"].str.contains(q, na=False)]
                else:
                    df_candidates = df_candidates[
                        df_candidates["cliente_tel"].astype(str).str.contains(phone_query, case=False, na=False)
                    ]

                if df_candidates.empty:
                    st.warning("No encontré registros con ese teléfono.")
                else:
                    st.success(f"Encontré {len(df_candidates)} registro(s).")

                    preview_cols = [
                        c for c in [
                            "folio", "timestamp", "cliente_nombre", "cliente_tel",
                            "moto_marca", "moto_modelo", "fecha_ingreso", "tecnico_responsable"
                        ]
                        if c in df_candidates.columns
                    ]

                    st.dataframe(
                        df_candidates[preview_cols].sort_values(by="timestamp", ascending=False),
                        use_container_width=True
                    )

                    folios = df_candidates["folio"].astype(str).tolist()
                    folio_sel = st.selectbox("Selecciona el folio", options=folios, key="folio_sel_filtered")

                    selected_row = df_candidates[df_candidates["folio"].astype(str) == str(folio_sel)].iloc[0]
                    record = row_to_record(selected_row)

                    colA, colB = st.columns([1, 1])

                    with colA:
                        st.write("**Resumen**")
                        st.write(f"**Cliente:** {record.get('cliente_nombre', '')}")
                        st.write(f"**Tel:** {record.get('cliente_tel', '')}")
                        st.write(
                            f"**Moto:** {record.get('moto_marca', '')} "
                            f"{record.get('moto_modelo', '')} "
                            f"({record.get('moto_anio', '')})"
                        )
                        st.write(f"**Ingreso:** {record.get('fecha_ingreso', '')}")
                        st.write(f"**Técnico:** {record.get('tecnico_responsable', '')}")

                    with colB:
                        regen = st.button("🔁 Re-generar PDF", use_container_width=True, key="regen_btn")

                    if regen:
                        regen_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                        pdf_path = os.path.join(
                            "output_pdfs",
                            f"reporte_regenerado_{record.get('folio', '')}_{regen_stamp}.pdf"
                        )

                        generate_service_report_pdf(record, pdf_path, logo_path=LOGO_PATH)
                        st.success("PDF re-generado correctamente.")

                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                "⬇️ Descargar PDF re-generado",
                                data=f,
                                file_name=os.path.basename(pdf_path),
                                mime="application/pdf",
                                use_container_width=True,
                            )

        xlsx_path = os.path.join("data", "records.xlsx")

        if os.path.exists(xlsx_path):
            with open(xlsx_path, "rb") as f:
                st.download_button(
                    "⬇️ Descargar Excel",
                    data=f,
                    file_name="records.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
