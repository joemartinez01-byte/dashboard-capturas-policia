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


# Cargar datos con caché para alta velocidad
@st.cache_data
def cargar_datos():
    df = pd.read_csv("consolidado_capturas_2022_2026.csv", low_memory=False)
    col_fecha = [c for c in df.columns if "FECHA" in c.upper()][0]
    col_casos = [
        c for c in df.columns if "CASO" in c.upper() or "CANT" in c.upper()
    ][0]
    col_depto = [c for c in df.columns if "DEP" in c.upper()][0]

    df["FECHA_DT"] = pd.to_datetime(
        df[col_fecha], format="%d/%m/%Y", errors="coerce"
    )
    df["CAPTURAS"] = (
        pd.to_numeric(df[col_casos], errors="coerce").fillna(1).astype(int)
    )
    df["AÑO"] = df["FECHA_DT"].dt.year
    df["MES_NUM"] = df["FECHA_DT"].dt.month
    df["DEPARTAMENTO"] = df[col_depto]
    return df


try:
    df = cargar_datos()

    # Panel lateral de controles
    st.sidebar.header("⚙️ Controles y Filtros")

    deptos = ["TODOS (NACIONAL)"] + sorted(
        df["DEPARTAMENTO"].dropna().unique().tolist()
    )
    depto_sel = st.sidebar.selectbox("Departamento / Zona", deptos)

    if depto_sel != "TODOS (NACIONAL)":
        df_filtrado = df[df["DEPARTAMENTO"] == depto_sel]
    else:
        df_filtrado = df.copy()

    años_disponibles = sorted(
        [int(a) for a in df_filtrado["AÑO"].dropna().unique()]
    )

    col1_f, col2_f = st.sidebar.columns(2)
    with col1_f:
        año_base = st.selectbox(
            "Año Base", años_disponibles, index=0 if años_disponibles else 0
        )
    with col2_f:
        año_comp = st.selectbox(
            "Año Contraste",
            años_disponibles,
            index=len(años_disponibles) - 1 if años_disponibles else 0,
        )

    # Agrupación por Mes y Año
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

    # Indicadores KPI principales
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

    # Gráfico de Tendencia Comparativa con Plotly
    st.markdown("### 📈 Tendencia Mensual Comparativa")
    resumen_sub = resumen[resumen["AÑO"].isin([año_base, año_comp])]
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

    # Tabla de resumen
    st.markdown("### 📋 Desglose Numérico por Mes")
    pivot_df = resumen_sub.pivot(
        index="MES", columns="AÑO", values="CAPTURAS"
    ).fillna(0)
    st.dataframe(pivot_df, use_container_width=True)

except Exception as e:
    st.error(
        f"Asegúrate de que el archivo 'consolidado_capturas_2022_2026.csv' se encuentre subido en el repositorio. Detalle: {e}"
    )