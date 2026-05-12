from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
import streamlit as st

from storage import append_record, load_records, ensure_dirs
from pdf_utils import generate_service_report_pdf


# ======================================================
# CONFIGURACIÓN
# ======================================================
st.set_page_config(
    page_title="Old Motor Garage",
    layout="wide"
)

LOGO_PATH = "logo.jpg"

ensure_dirs()
os.makedirs("output_pdfs", exist_ok=True)


# ======================================================
# ESTILO VISUAL
# ======================================================
st.markdown("""
<style>
.stApp {
    background: #ffffff;
    color: #111111;
}

h1, h2, h3, h4, p, label, span, div {
    color: #111111;
}

section[data-testid="stSidebar"] {
    background-color: #111111;
}

section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

div.stButton > button {
    background-color: #c1121f;
    color: white;
    border-radius: 12px;
    border: none;
    font-weight: bold;
    padding: 0.7rem 1rem;
}

div.stButton > button:hover {
    background-color: #a30f19;
    color: white;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    border-bottom: 2px solid #c1121f;
}

.stTabs [data-baseweb="tab"] {
    background-color: #ffffff;
    border-radius: 10px 10px 0 0;
    color: #111111;
    padding: 10px 18px;
    border: 1px solid #dddddd;
    border-bottom: none;
    font-weight: bold;
}

.stTabs [aria-selected="true"] {
    background-color: #c1121f !important;
    color: #ffffff !important;
}

.omg-card {
    background-color: #ffffff;
    border: 2px solid #c1121f;
    padding: 20px;
    border-radius: 18px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    margin-bottom: 18px;
}

.omg-title {
    font-size: 34px;
    font-weight: 900;
    margin-bottom: 0px;
    color: #111111;
}

.omg-subtitle {
    color: #444444;
    margin-top: 4px;
}

.small-card {
    background-color: #ffffff;
    padding: 18px;
    border-radius: 16px;
    border: 1px solid #dddddd;
    border-left: 6px solid #c1121f;
    box-shadow: 0 3px 10px rgba(0,0,0,0.06);
}

div[data-testid="stDataFrame"] {
    border-radius: 16px;
    border: 1px solid #dddddd;
    padding: 8px;
    background-color: #ffffff;
}

hr {
    border-top: 2px solid #c1121f;
}
</style>
""", unsafe_allow_html=True)


# ======================================================
# LOGIN
# ======================================================
def login():
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=220)

        st.markdown("""
        <div class="omg-card">
            <p class="omg-title">Old Motor Garage</p>
            <p class="omg-subtitle">Sistema de reportes y control de servicios</p>
        </div>
        """, unsafe_allow_html=True)

        usuario = st.text_input("Usuario", key="login_usuario")
        password = st.text_input("Contraseña", type="password", key="login_password")

        if st.button("Entrar", use_container_width=True, key="btn_login"):
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

if st.sidebar.button("Cerrar sesión", key="btn_logout"):
    st.session_state["logueada"] = False
    st.rerun()


# ======================================================
# FUNCIONES
# ======================================================
COLUMNAS_BONITAS = {
    "folio": "Folio",
    "timestamp": "Fecha",
    "cliente_nombre": "Nombre del cliente",
    "cliente_tel": "Teléfono",
    "moto_marca": "Marca",
    "moto_modelo": "Modelo",
    "moto_anio": "Año",
    "moto_km": "Kilometraje",
    "moto_placas_serie": "Placas / Serie",
    "fecha_ingreso": "Ingreso",
    "fecha_entrega": "Entrega",
    "tecnico_responsable": "Técnico",
    "recomendaciones": "Recomendaciones",
    "observaciones_recepcion": "Observaciones de recepción",
    "comentarios_tecnico": "Comentarios del técnico",
}


def tabla_bonita(df):
    return df.rename(columns=COLUMNAS_BONITAS)


def now_folio():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def safe_get(row, key):
    try:
        val = row.get(key, "")
        if pd.isna(val):
            return ""
        return val
    except Exception:
        return ""


def row_to_record(row):
    return row.to_dict()


# ======================================================
# ENCABEZADO
# ======================================================
col_logo, col_title = st.columns([1, 5])

with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=140)

with col_title:
    st.markdown("""
    <div class="omg-card">
        <p class="omg-title">Old Motor Garage</p>
        <p class="omg-subtitle">Sistema de reportes, historial de clientes y control de servicios</p>
    </div>
    """, unsafe_allow_html=True)


tab1, tab2 = st.tabs([
    "🧾 Captura",
    "👥 Agenda de clientes"
])


# ======================================================
# TAB CAPTURA
# ======================================================
with tab1:
    st.subheader("Captura rápida del servicio")

    df_clientes = load_records()

    tipo_cliente = st.radio(
        "Tipo de cliente",
        ["Cliente nuevo", "Cliente existente"],
        horizontal=True,
        key="tipo_cliente"
    )

    cliente_nombre_default = ""
    cliente_tel_default = ""
    moto_marca_default = ""
    moto_modelo_default = ""
    moto_anio_default = ""
    moto_km_default = ""
    moto_placas_serie_default = ""

    if tipo_cliente == "Cliente existente":
        if df_clientes.empty:
            st.info("Aún no hay clientes registrados. Captura como cliente nuevo.")
        else:
            st.markdown("### Buscar cliente")

            busqueda_cliente = st.text_input(
                "Buscar por nombre o teléfono",
                key="busqueda_cliente_captura"
            )

            df_busqueda = df_clientes.copy()

            for col in [
                "cliente_nombre",
                "cliente_tel",
                "moto_marca",
                "moto_modelo",
                "moto_anio",
                "moto_km",
                "moto_placas_serie",
            ]:
                if col not in df_busqueda.columns:
                    df_busqueda[col] = ""

            df_busqueda["cliente_nombre"] = df_busqueda["cliente_nombre"].fillna("").astype(str)
            df_busqueda["cliente_tel"] = df_busqueda["cliente_tel"].fillna("").astype(str)

            if busqueda_cliente:
                df_busqueda = df_busqueda[
                    df_busqueda["cliente_nombre"].str.contains(busqueda_cliente, case=False, na=False)
                    | df_busqueda["cliente_tel"].str.contains(busqueda_cliente, case=False, na=False)
                ]

            clientes_unicos = (
                df_busqueda[["cliente_nombre", "cliente_tel"]]
                .drop_duplicates()
                .sort_values(by="cliente_nombre")
            )

            if clientes_unicos.empty:
                st.warning("No encontré clientes con esa búsqueda.")
            else:
                opciones_clientes = [
                    f"{row.cliente_nombre} | {row.cliente_tel}"
                    for _, row in clientes_unicos.iterrows()
                ]

                cliente_sel = st.selectbox(
                    "Selecciona cliente",
                    opciones_clientes,
                    key="cliente_captura_select"
                )

                cliente_nombre_default, cliente_tel_default = cliente_sel.split(" | ", 1)

                registros_cliente = df_busqueda[
                    (df_busqueda["cliente_nombre"] == cliente_nombre_default)
                    & (df_busqueda["cliente_tel"] == cliente_tel_default)
                ].copy()

                motos_cliente = (
                    registros_cliente[
                        [
                            "moto_marca",
                            "moto_modelo",
                            "moto_anio",
                            "moto_km",
                            "moto_placas_serie",
                        ]
                    ]
                    .fillna("")
                    .astype(str)
                    .drop_duplicates()
                )

                if motos_cliente.empty:
                    st.info("Este cliente aún no tiene motocicletas registradas.")
                else:
                    opciones_motos = [
                        f"{row.moto_marca} {row.moto_modelo} | Año: {row.moto_anio} | Serie/Placas: {row.moto_placas_serie}"
                        for _, row in motos_cliente.iterrows()
                    ]

                    moto_sel = st.selectbox(
                        "Selecciona motocicleta",
                        opciones_motos,
                        key="moto_captura_select"
                    )

                    moto_index = opciones_motos.index(moto_sel)
                    moto_data = motos_cliente.iloc[moto_index]

                    moto_marca_default = moto_data["moto_marca"]
                    moto_modelo_default = moto_data["moto_modelo"]
                    moto_anio_default = moto_data["moto_anio"]
                    moto_km_default = moto_data["moto_km"]
                    moto_placas_serie_default = moto_data["moto_placas_serie"]

    colA, colB = st.columns(2)

    with colA:
        st.markdown("### Datos del cliente")

        cliente_nombre = st.text_input(
            "Nombre del cliente",
            value=cliente_nombre_default,
            key=f"cliente_nombre_{tipo_cliente}_{cliente_nombre_default}"
        )

        cliente_tel = st.text_input(
            "Teléfono / WhatsApp",
            value=cliente_tel_default,
            key=f"cliente_tel_{tipo_cliente}_{cliente_tel_default}"
        )

        fecha_ingreso = st.date_input("Fecha de ingreso", key="fecha_ingreso")
        fecha_entrega = st.date_input("Fecha de entrega", key="fecha_entrega")

    with colB:
        st.markdown("### Datos de la motocicleta")

        moto_marca = st.text_input(
            "Marca",
            value=moto_marca_default,
            key=f"moto_marca_{tipo_cliente}_{moto_marca_default}"
        )

        moto_modelo = st.text_input(
            "Modelo",
            value=moto_modelo_default,
            key=f"moto_modelo_{tipo_cliente}_{moto_modelo_default}"
        )

        moto_anio = st.text_input(
            "Año",
            value=moto_anio_default,
            key=f"moto_anio_{tipo_cliente}_{moto_anio_default}"
        )

        moto_km = st.text_input(
            "Kilometraje",
            value=moto_km_default,
            key=f"moto_km_{tipo_cliente}_{moto_km_default}"
        )

        moto_placas_serie = st.text_input(
            "Placas / Serie",
            value=moto_placas_serie_default,
            key=f"moto_placas_{tipo_cliente}_{moto_placas_serie_default}"
        )

    st.divider()

    observaciones_recepcion = st.text_area(
        "Observaciones de recepción",
        height=120,
        key="observaciones_recepcion"
    )

    st.divider()

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### Sistema de frenos")
        frenos_calipers = st.checkbox("Mantenimiento a cálipers y ejes de cálipers", value=True, key="frenos_calipers")
        frenos_balatas = st.checkbox("Mantenimiento a balatas", value=True, key="frenos_balatas")
        frenos_grosor = st.checkbox("Medición de grosor y desgaste de balatas", value=True, key="frenos_grosor")
        frenos_mangueras = st.checkbox("Mantenimiento y revisión de mangueras", value=True, key="frenos_mangueras")
        frenos_liquido = st.checkbox("Revisión de líquido de frenos", value=True, key="frenos_liquido")
        frenos_purga = st.checkbox("Purga de sistema de frenos delanteros y traseros", value=True, key="frenos_purga")
        obs_frenos = st.text_area("Observaciones frenos", height=90, key="obs_frenos")

    with c2:
        st.markdown("### Motor")
        motor_prueba_aceite = st.checkbox("Prueba de propiedades del aceite", value=True, key="motor_prueba_aceite")
        motor_residuos = st.checkbox("Análisis de residuos de asentamiento interno", value=True, key="motor_residuos")
        motor_compresion = st.checkbox("Revisión de compresión", value=True, key="motor_compresion")
        motor_balancines = st.checkbox("Ajuste de balancines según manual", value=True, key="motor_balancines")
        motor_cuerpo_aceleracion = st.checkbox("Limpieza de cuerpo de aceleración", value=True, key="motor_cuerpo_aceleracion")
        motor_bujia = st.checkbox("Cambio de bujía", value=True, key="motor_bujia")
        motor_aceite_motul = st.checkbox("Cambio de aceite Motul sintético", value=True, key="motor_aceite_motul")
        motor_filtro_aceite = st.checkbox("Cambio de filtro de aceite", value=True, key="motor_filtro_aceite")
        obs_motor = st.text_area("Observaciones motor", height=90, key="obs_motor")

    with c3:
        st.markdown("### Desplazamiento")
        despl_cadena = st.checkbox("Lubricación y tensión de cadena", value=True, key="despl_cadena")
        despl_pinon_seguro = st.checkbox("Revisión de piñón y seguro", value=True, key="despl_pinon_seguro")
        despl_flecha_transmision = st.checkbox("Revisión de flecha de transmisión", value=True, key="despl_flecha_transmision")
        despl_sprocket_flecha = st.checkbox("Mantenimiento a sprocket y flecha", value=True, key="despl_sprocket_flecha")
        despl_retenes = st.checkbox("Revisión de retenes de transmisión", value=True, key="despl_retenes")
        obs_despl = st.text_area("Observaciones desplazamiento", height=90, key="obs_despl")

    st.divider()

    c4, c5 = st.columns(2)

    with c4:
        st.markdown("### Sistema de carga")
        carga_estator_regulador_bateria = st.checkbox("Escaneo de carga estator/regulador/batería", value=True, key="carga_estator_regulador_bateria")
        carga_encendido_circuito = st.checkbox("Escaneo de encendido y circuito", value=True, key="carga_encendido_circuito")
        carga_conectores_arnes = st.checkbox("Mantenimiento a conectores del arnés", value=True, key="carga_conectores_arnes")
        carga_mandos_general = st.checkbox("Revisión de mandos y funcionamiento general", value=True, key="carga_mandos_general")
        obs_carga = st.text_area("Observaciones carga", height=90, key="obs_carga")

    with c5:
        st.markdown("### Suspensión")
        susp_barras_amortiguadores = st.checkbox("Revisión de barras y amortiguadores", value=True, key="susp_barras_amortiguadores")
        susp_retenes = st.checkbox("Limpieza de retenes", value=True, key="susp_retenes")
        obs_susp = st.text_area("Observaciones suspensión", height=90, key="obs_susp")

    st.divider()

    recomendaciones = st.text_area("Recomendaciones", height=100, key="recomendaciones")
    tecnico_responsable = st.text_input("Técnico responsable", key="tecnico_responsable")
    comentarios_tecnico = st.text_area("Comentarios del técnico", height=100, key="comentarios_tecnico")

    guardar = st.button(
        "✅ Guardar PDF + Registro",
        use_container_width=True,
        key="btn_guardar"
    )

    if guardar:
        folio = now_folio()

        pdf_path = os.path.join(
            "output_pdfs",
            f"reporte_{folio}.pdf"
        )

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

        generate_service_report_pdf(
            record,
            pdf_path,
            logo_path=LOGO_PATH
        )

        st.success("Registro guardado correctamente.")

        with open(pdf_path, "rb") as f:
            st.download_button(
                "⬇️ Descargar PDF",
                data=f,
                file_name=os.path.basename(pdf_path),
                mime="application/pdf",
                use_container_width=True,
                key="download_pdf_captura"
            )


# ======================================================
# TAB AGENDA
# ======================================================
with tab2:
    st.subheader("👥 Agenda de clientes")

    df = load_records()

    if df.empty:
        st.info("Aún no hay registros.")
    else:
        df_agenda = df.copy()

        for col in [
            "cliente_nombre",
            "cliente_tel",
            "folio",
            "timestamp",
            "moto_marca",
            "moto_modelo",
            "moto_anio",
            "moto_km",
            "moto_placas_serie",
            "fecha_ingreso",
            "fecha_entrega",
            "tecnico_responsable",
            "recomendaciones",
            "observaciones_recepcion",
            "comentarios_tecnico",
        ]:
            if col not in df_agenda.columns:
                df_agenda[col] = ""

        busqueda = st.text_input(
            "Buscar cliente por nombre o teléfono",
            key="busqueda_cliente_agenda"
        )

        if busqueda:
            df_agenda = df_agenda[
                df_agenda["cliente_nombre"].astype(str).str.contains(busqueda, case=False, na=False)
                | df_agenda["cliente_tel"].astype(str).str.contains(busqueda, case=False, na=False)
            ]

        clientes = (
            df_agenda
            .groupby(["cliente_nombre", "cliente_tel"], dropna=False)
            .agg(
                total_registros=("folio", "count"),
                ultimo_servicio=("timestamp", "max")
            )
            .reset_index()
            .sort_values(by="ultimo_servicio", ascending=False)
        )

        st.markdown("### Clientes encontrados")

        st.dataframe(
            clientes.rename(columns={
                "cliente_nombre": "Nombre del cliente",
                "cliente_tel": "Teléfono",
                "total_registros": "Servicios",
                "ultimo_servicio": "Último servicio"
            }),
            use_container_width=True
        )

        st.divider()

        opciones_clientes_agenda = [
            f"{row.cliente_nombre} | {row.cliente_tel}"
            for _, row in clientes.iterrows()
        ]

        if opciones_clientes_agenda:
            cliente_sel_agenda = st.selectbox(
                "Selecciona cliente",
                opciones_clientes_agenda,
                key="cliente_agenda_select"
            )

            nombre_sel, tel_sel = cliente_sel_agenda.split(" | ", 1)

            registros_cliente = df_agenda[
                (df_agenda["cliente_nombre"].astype(str) == nombre_sel)
                & (df_agenda["cliente_tel"].astype(str) == tel_sel)
            ].sort_values(by="timestamp", ascending=False)

            columnas = [
                "folio",
                "timestamp",
                "moto_marca",
                "moto_modelo",
                "moto_anio",
                "moto_km",
                "fecha_ingreso",
                "fecha_entrega",
                "tecnico_responsable",
                "recomendaciones"
            ]

            columnas_existentes = [c for c in columnas if c in registros_cliente.columns]

            st.markdown("### Folios y servicios asociados")
            st.dataframe(
                tabla_bonita(registros_cliente[columnas_existentes]),
                use_container_width=True
            )

            st.divider()

            folios = registros_cliente["folio"].astype(str).tolist()

            folio_sel = st.selectbox(
                "Selecciona folio",
                folios,
                key="folio_agenda_select"
            )

            detalle = registros_cliente[
                registros_cliente["folio"].astype(str) == folio_sel
            ].iloc[0]

            col1, col2 = st.columns(2)

            with col1:
                st.markdown('<div class="small-card">', unsafe_allow_html=True)
                st.write("### Cliente")
                st.write("**Nombre:**", safe_get(detalle, "cliente_nombre"))
                st.write("**Teléfono:**", safe_get(detalle, "cliente_tel"))
                st.write("**Folio:**", safe_get(detalle, "folio"))
                st.write("**Ingreso:**", safe_get(detalle, "fecha_ingreso"))
                st.write("**Entrega:**", safe_get(detalle, "fecha_entrega"))
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="small-card">', unsafe_allow_html=True)
                st.write("### Motocicleta")
                st.write("**Marca:**", safe_get(detalle, "moto_marca"))
                st.write("**Modelo:**", safe_get(detalle, "moto_modelo"))
                st.write("**Año:**", safe_get(detalle, "moto_anio"))
                st.write("**KM:**", safe_get(detalle, "moto_km"))
                st.write("**Placas / Serie:**", safe_get(detalle, "moto_placas_serie"))
                st.markdown('</div>', unsafe_allow_html=True)

            st.divider()

            st.write("### Observaciones")
            st.write(safe_get(detalle, "observaciones_recepcion"))

            st.write("### Recomendaciones")
            st.write(safe_get(detalle, "recomendaciones"))

            st.write("### Comentarios técnico")
            st.write(safe_get(detalle, "comentarios_tecnico"))

            if st.button(
                "🔁 Re-generar PDF",
                use_container_width=True,
                key="btn_regenerar_pdf_agenda"
            ):
                record = row_to_record(detalle)

                regen_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

                pdf_path = os.path.join(
                    "output_pdfs",
                    f"reporte_{regen_stamp}.pdf"
                )

                generate_service_report_pdf(
                    record,
                    pdf_path,
                    logo_path=LOGO_PATH
                )

                st.success("PDF generado correctamente.")

                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "⬇️ Descargar PDF",
                        data=f,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf",
                        use_container_width=True,
                        key="download_pdf_agenda"
                    )
