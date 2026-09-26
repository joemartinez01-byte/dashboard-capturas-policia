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

    # Mapeo de nombres de meses
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
    df["MES"] = df["MES_NUM"].map(nombres_meses)
    return df


try:
    df = cargar_datos()

    # Panel de Control en la Barra Lateral
    st.sidebar.header("⚙️ Controles y Filtros")

    # 1. Filtro de Departamento
    deptos = ["TODOS (NACIONAL)"] + sorted(
        [str(d) for d in df["DEPARTAMENTO"].dropna().unique()]
    )
    depto_sel = st.sidebar.selectbox("1. Departamento / Zona", deptos)

    if depto_sel != "TODOS (NACIONAL)":
        df_filtrado = df[df["DEPARTAMENTO"] == depto_sel]
    else:
        df_filtrado = df.copy()

    # 2. Filtro de Meses (Selección múltiple o individual)
    lista_meses = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ]
    meses_sel = st.sidebar.multiselect(
        "2. Filtrar Mes(es)",
        options=lista_meses,
        default=lista_meses,  # Por defecto selecciona todos los meses
        help="Puedes seleccionar uno o varios meses para acotar la comparación",
    )

    if meses_sel:
        df_filtrado = df_filtrado[df_filtrado["MES"].isin(meses_sel)]
    else:
        st.warning(
            "Por favor selecciona al menos un mes en el filtro lateral."
        )

    # 3. Selección de Años
    años_disponibles = sorted(list(df_filtrado["AÑO"].unique()))

    col1_f, col2_f = st.sidebar.columns(2)
    with col1_f:
        año_base = st.selectbox(
            "Año Base",
            años_disponibles,
            index=0 if años_disponibles else 0,
        )
    with col2_f:
        idx_comp = (
            len(años_disponibles) - 1 if len(años_disponibles) > 1 else 0
        )
        año_comp = st.selectbox(
            "Año Contraste",
            años_disponibles,
            index=idx_comp,
        )

    # Agrupación por Mes y Año
    resumen = (
        df_filtrado.groupby(["AÑO", "MES_NUM", "MES"])["CAPTURAS"]
        .sum()
        .reset_index()
    )

    # Indicadores KPI
    tot_base = resumen[resumen["AÑO"] == año_base]["CAPTURAS"].sum()
    tot_comp = resumen[resumen["AÑO"] == año_comp]["CAPTURAS"].sum()
    dif_abs = tot_comp - tot_base
    var_pct = ((dif_abs / tot_base) * 100) if tot_base > 0 else 0

    st.markdown("### 📊 Indicadores Clave")
    texto_meses = (
        "Todos los meses"
        if len(meses_sel) == 12
        else ", ".join(meses_sel) if len(meses_sel) <= 3 else f"{len(meses_sel)} meses seleccionados"
    )
    st.caption(f"Filtro aplicado: **{depto_sel}** | Meses: **{texto_meses}**")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric(f"Capturas {año_base}", f"{tot_base:,}")
    kpi2.metric(f"Capturas {año_comp}", f"{tot_comp:,}")
    kpi3.metric("Diferencia Absoluta", f"{dif_abs:,}")
    kpi4.metric("Variación Interanual", f"{var_pct:+.2f}%")

    # Gráfico de Tendencia o Comparativo
    st.markdown("### 📈 Tendencia / Comparativa por Mes")
    resumen_sub = resumen[resumen["AÑO"].isin([año_base, año_comp])].copy()
    resumen_sub["AÑO"] = resumen_sub["AÑO"].astype(str)
    resumen_sub = resumen_sub.sort_values("MES_NUM")

    if len(meses_sel) == 1:
        # Si selecciona solo 1 mes, muestra un gráfico de barras comparativo por año
        fig = px.bar(
            resumen_sub,
            x="AÑO",
            y="CAPTURAS",
            color="AÑO",
            text="CAPTURAS",
            title=f"Capturas en {meses_sel[0]}: {año_base} vs {año_comp} ({depto_sel})",
        )
        fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    else:
        # Si selecciona varios meses, muestra la curva temporal
        fig = px.line(
            resumen_sub,
            x="MES",
            y="CAPTURAS",
            color="AÑO",
            markers=True,
            title=f"Comparativo Mensual: {año_base} vs {año_comp} ({depto_sel})",
        )
        # Línea de umbral si estamos viendo nivel Nacional
        if depto_sel == "TODOS (NACIONAL)":
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
    # Ordenar por el orden natural de meses
    pivot_df = pivot_df.reindex(
        [m for m in lista_meses if m in pivot_df.index]
    )
    st.dataframe(pivot_df, use_container_width=True)

except Exception as e:
    st.error(
        f"Asegúrate de haber subido el archivo 'resumen_capturas_dashboard.csv'. Detalle: {e}"
    )