import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Dashboard Capturas Policía",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🚔 Dashboard Comparativo de Capturas de la Policía (2022–2026)")
st.markdown(
    "Analiza el comportamiento mensual e interanual de las capturas en Colombia."
)


@st.cache_data
def cargar_datos():
    df = pd.read_csv("resumen_capturas_dashboard.csv")
    df = df.dropna(subset=["AÑO", "MES_NUM"])
    df["AÑO"] = df["AÑO"].astype(int)
    df["MES_NUM"] = df["MES_NUM"].astype(int)
    return df


try:
    df = cargar_datos()

    # Panel de control
    st.sidebar.header("⚙️ Controles y Filtros")

    deptos = ["TODOS (NACIONAL)"] + sorted(
        [str(d) for d in df["DEPARTAMENTO"].dropna().unique()]
    )
    depto_sel = st.sidebar.selectbox("Departamento / Zona", deptos)

    if depto_sel != "TODOS (NACIONAL)":
        df_filtrado = df[df["DEPARTAMENTO"] == depto_sel]
    else:
        df_filtrado = df.copy()

    años_disponibles = sorted(list(df_filtrado["AÑO"].unique()))

    col1_f, col2_f = st.sidebar.columns(2)
    with col1_f:
        año_base = st.selectbox("Año Base", años_disponibles, index=0)
    with col2_f:
        idx_comp = (
            len(años_disponibles) - 1 if len(años_disponibles) > 1 else 0
        )
        año_comp = st.selectbox(
            "Año Contraste", años_disponibles, index=idx_comp
        )

    # Agrupación mensual
    resumen = (
        df_filtrado.groupby(["AÑO", "MES_NUM"])["CAPTURAS"].sum().reset_index()
    )
    nombres_meses = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre",
    }
    resumen["MES"] = resumen["MES_NUM"].map(nombres_meses)

    # Indicadores KPI
    tot_base = resumen[resumen["AÑO"] == año_base]["CAPTURAS"].sum()
    tot_comp = resumen[resumen["AÑO"] == año_comp]["CAPTURAS"].sum()
    dif_abs = tot_comp - tot_base
    var_pct = ((dif_abs / tot_base) * 100) if tot_base > 0 else 0

    st.markdown("### 📊 Indicadores Clave")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric(f"Total Capturas {año_base}", f"{tot_base:,}")
    kpi2.metric(f"Total Capturas {año_comp}", f"{tot_comp:,}")
    kpi3.metric("Diferencia Absoluta", f"{dif_abs:,}")
    kpi4.metric("Variación Interanual", f"{var_pct:+.2f}%")

    # Gráfico de Tendencias
    st.markdown("### 📈 Tendencia Mensual Comparativa")
    resumen_sub = resumen[resumen["AÑO"].isin([año_base, año_comp])].copy()
    resumen_sub["AÑO"] = resumen_sub["AÑO"].astype(str)
    resumen_sub = resumen_sub.sort_values("MES_NUM")

    fig = px.line(
        resumen_sub,
        x="MES",
        y="CAPTURAS",
        color="AÑO",
        markers=True,
        title=f"Comparativo Mensual: {año_base} vs {año_comp} ({depto_sel})",
    )
    fig.add_hline(
        y=17000,
        line_dash="dash",
        line_color="red",
        annotation_text="Umbral 17.000 capturas/mes",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabla numérica
    st.markdown("### 📋 Desglose Numérico por Mes")
    pivot_df = resumen_sub.pivot(
        index="MES", columns="AÑO", values="CAPTURAS"
    ).fillna(0)
    st.dataframe(pivot_df, use_container_width=True)

except Exception as e:
    st.error(f"Asegúrate de subir el archivo 'resumen_capturas_dashboard.csv'. Error: {e}")