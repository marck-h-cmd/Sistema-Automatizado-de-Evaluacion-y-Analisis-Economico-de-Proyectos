import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px


from src.utils.eval_basica import calcular_vpn
from src.utils.sensibilidad import (
    calcular_sensibilidad_univariada,
    grafico_sensibilidad_univariada,
    interpretar_sensibilidad_univariada_ia,

    calcular_sensibilidad_bivariada,
    grafico_sensibilidad_bivariada,
    interpretar_sensibilidad_bivariada_ia,

    calcular_tornado,
    grafico_tornado,
    tabla_tornado,
    interpretar_tornado_completo_ia,
    
    interpretar_resumen_riesgo_ia
    
)

# ======================================================
# FUNCIONES AUXILIARES DE RIESGO
# ======================================================

def calcular_elasticidad(vpns, variaciones):
    base = vpns[len(vpns)//2]
    delta_vpn = (max(vpns) - min(vpns)) / base
    delta_var = (max(variaciones) - min(variaciones)) / 100
    return delta_vpn / delta_var if delta_var != 0 else 0


def margen_seguridad(punto_eq):
    return abs(punto_eq) if punto_eq is not None else None


def clasificar_riesgo(rango, max_rango):
    ratio = rango / max_rango
    if ratio > 0.66:
        return "🔴 Alto"
    elif ratio > 0.33:
        return "🟠 Medio"
    return "🟢 Bajo"

def simulacion_montecarlo(flujos, tasa, n=10000):
    vpns = []
    for _ in range(n):
        flujos_sim = flujos * np.random.normal(1, 0.1, len(flujos))
        tasa_sim = tasa * np.random.normal(1, 0.05)
        vpns.append(calcular_vpn(flujos_sim, tasa_sim))
    return np.array(vpns)


def escenarios_criticos(vpns):
    return {
        "Peor Escenario": min(vpns),
        "Caso Base": vpns[len(vpns)//2],
        "Mejor Escenario": max(vpns)
    }



def elasticidad_generica(valores):
    base = valores[len(valores)//2]
    return (max(valores) - min(valores)) / abs(base) if base != 0 else 0


def indice_estabilidad(vpns, vpn_base):
    return np.std(vpns) / abs(vpn_base)


def pendiente_vpn(vpns, variaciones):
    return (vpns[-1] - vpns[0]) / (variaciones[-1] - variaciones[0])

def metricas_riesgo(vpns):
    return {
        "VPN Esperado": np.mean(vpns),
        "Desviación": np.std(vpns),
        "Prob VPN < 0": np.mean(vpns < 0) * 100,
        "VaR 5%": np.percentile(vpns, 5),
        "CVaR 5%": vpns[vpns <= np.percentile(vpns, 5)].mean()
    }

def grafico_distribucion_vpn(vpns):
    fig = px.histogram(vpns, nbins=50, title="Distribución del VPN")
    fig.add_vline(x=0, line_dash="dash", line_color="red")
    return fig

def semaforo_riesgo(prob_neg):
    if prob_neg > 40:
        return "🔴 Riesgo Alto"
    elif prob_neg > 20:
        return "🟠 Riesgo Medio"
    return "🟢 Riesgo Bajo"


# =============================
# ESTILOS DASHBOARD
# =============================
st.markdown("""
<style>
[data-testid="metric-container"] {
    background-color: #f8f9fa;
    border-radius: 12px;
    padding: 15px;
    text-align: center;
}

.block-container {
    padding-top: 1rem;
}

h1, h2, h3 {
    color: #1f4e79;
}
</style>
""", unsafe_allow_html=True)


# =============================
# VISTA PRINCIPAL
# =============================
def show_sensibilidad_form():

    st.title("⚠️ Análisis de Sensibilidad y Riesgo")
    st.markdown(
        "Identificación de variables críticas, riesgo financiero y estabilidad del proyecto."
    )

    if st.session_state.proyecto_data is None:
        st.warning("⚠️ Primero completa la Evaluación Básica.")
        return

    flujos = st.session_state.proyecto_data["flujos"]
    tasa = st.session_state.proyecto_data["tasa_descuento"]
    vpn_base = st.session_state.proyecto_data["vpn"]

    tab_uni, tab_bi, tab_tor, tab_res = st.tabs(
        ["📊 Univariada", "🎯 Bivariada", "🌪️ Tornado", "📌 Resumen de Riesgo"]
    )

    # =====================================================
    # 📊 UNIVARIADA
    # =====================================================
    with tab_uni:

        st.subheader("📊 Sensibilidad Univariada")

        st.info("""
        Este análisis muestra **cómo cambia la rentabilidad del proyecto**
        cuando **una sola variable se modifica**, manteniendo las demás constantes.

        Es ideal para:
        • Identificar variables críticas  
        • Medir riesgo financiero  
        • Evaluar la estabilidad del proyecto
        """)

        col_ctrl, col_kpi = st.columns([2, 1])

        # =============================
        # CONTROLES
        # =============================
        with col_ctrl:

            variable = st.selectbox(
                "Variable a analizar ❓",
                ["Flujos de Caja", "Tasa de Descuento", "Inversión Inicial"],
                help="""
                Selecciona la variable económica que deseas evaluar.

                • Flujos de Caja → ingresos futuros
                • Tasa de Descuento → costo del capital / riesgo
                • Inversión Inicial → monto inicial del proyecto
                """
            )

            rango = st.slider(
                "Rango de variación (%) ❓",
                10, 50, 30, 5,
                help="""
                Define cuánto puede variar la variable seleccionada
                hacia arriba y hacia abajo.

                Ejemplo:
                30% → se evalúa desde -30% hasta +30%
                """
            )

            st.caption("""
            ⚙️ El sistema evalúa múltiples escenarios dentro de este rango
            para medir el impacto económico.
            """)

        # =============================
        # CÁLCULOS
        # =============================
        resultado = calcular_sensibilidad_univariada(
            variable, flujos, tasa, rango
        )

        variaciones = resultado["variaciones"]
        vpns = resultado["vpns"]
        tirs = resultado["tirs"]
        bcs = resultado["bcs"]
        punto_eq = resultado["punto_equilibrio"]

        elasticidad_vpn = elasticidad_generica(vpns)
        elasticidad_tir = elasticidad_generica(tirs)
        elasticidad_bc = elasticidad_generica(bcs)
        estabilidad = indice_estabilidad(vpns, vpn_base)
        pendiente = pendiente_vpn(vpns, variaciones)

        elasticidad = calcular_elasticidad(vpns, variaciones)
        margen = margen_seguridad(punto_eq)
        escenarios = escenarios_criticos(vpns)

        # =============================
        # KPI PRINCIPALES
        # =============================
        with col_kpi:

            st.metric(
                "VPN Mínimo",
                f"${min(vpns):,.2f}",
                help="Peor resultado posible dentro del rango analizado."
            )

            st.metric(
                "VPN Máximo",
                f"${max(vpns):,.2f}",
                help="Mejor resultado posible bajo el mismo rango."
            )

            st.metric(
                "Elasticidad VPN",
                f"{elasticidad:.2f}",
                help="""
                Mide qué tan sensible es el VPN ante cambios
                porcentuales de la variable analizada.

                Valores altos = mayor riesgo
                """
            )

        # =============================
        # GRÁFICO
        # =============================
        st.markdown("### 📈 Comportamiento de los Indicadores")

        st.caption("""
        El gráfico muestra cómo reaccionan los indicadores financieros
        cuando la variable seleccionada cambia.

        • VPN → creación de valor
        • TIR → rentabilidad
        • B/C → eficiencia económica
        """)

        fig = grafico_sensibilidad_univariada(
            variaciones, vpns, tirs, bcs,
            variable, st.session_state.proyecto_data["tmar"]
        )
        st.plotly_chart(fig, use_container_width=True)

        # =============================
        # MARGEN DE SEGURIDAD
        # =============================
        if margen:
            st.info(f"""
            🛡️ **Margen de Seguridad: {margen:.1f}%**

            Indica cuánto puede variar la variable
            antes de que el proyecto deje de ser rentable (VPN = 0).
            """)

        # =============================
        # MÉTRICAS AVANZADAS
        # =============================
        with st.expander("📈 Métricas Avanzadas de Sensibilidad"):

            st.caption("""
            Estas métricas permiten evaluar **riesgo, estabilidad
            y velocidad de cambio del proyecto**.
            """)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Elasticidades (Volatilidad)**")
                st.metric("VPN", f"{elasticidad_vpn:.2f}", help="Sensibilidad del valor económico.")
                st.metric("TIR", f"{elasticidad_tir:.2f}", help="Sensibilidad de la rentabilidad.")
                st.metric("B/C", f"{elasticidad_bc:.2f}", help="Sensibilidad de la eficiencia.")

            with col2:
                st.markdown("**Estabilidad del Proyecto**")
                st.metric(
                    "Índice de Estabilidad",
                    f"{estabilidad:.2f}",
                    help="Relación entre la variabilidad del VPN y el VPN base."
                )
                st.metric(
                    "Pendiente VPN",
                    f"{pendiente:,.2f}",
                    help="Velocidad con la que cambia el VPN."
                )

        # =============================
        # ESCENARIOS
        # =============================
        with st.expander("📊 Escenarios Críticos"):

            st.caption("""
            Comparación de los escenarios más relevantes
            para evaluar riesgos y oportunidades.
            """)

            st.table(pd.DataFrame.from_dict(
                escenarios, orient="index", columns=["VPN ($)"]
            ))

        # =============================
        # IA
        # =============================
        with st.expander("🤖 Interpretación con IA"):

            st.caption("""
            La IA analiza automáticamente:
            • Sensibilidad
            • Elasticidad
            • Punto de equilibrio
            • Comportamiento gráfico
            """)

            if st.button("Generar interpretación", key="ia_uni"):
                st.info(
                    interpretar_sensibilidad_univariada_ia(
                        variable,
                        variaciones,
                        vpns,
                        tirs,
                        bcs,
                        elasticidad_vpn,
                        elasticidad_tir,
                        elasticidad_bc,
                        estabilidad,
                        pendiente,
                        punto_eq,
                        escenarios
                    )
                )
   
        


        # =====================================================
        # 🎯 BIVARIADA
        # =====================================================
    with tab_bi:

        st.subheader("🎯 Sensibilidad Bivariada")

        st.info("""
        Este análisis evalúa **cómo cambia el VPN del proyecto cuando dos variables
        se modifican al mismo tiempo**.

        Es especialmente útil para:
        • Evaluar escenarios combinados de riesgo  
        • Analizar relaciones entre variables críticas  
        • Detectar zonas de pérdida y estabilidad
        """)

        col1, col2 = st.columns(2)

        # =============================
        # CONTROLES DE VARIABLES
        # =============================
        with col1:
            var1 = st.selectbox(
                "Variable 1 ❓",
                ["Flujos de Caja", "Tasa de Descuento", "Inversión Inicial"],
                help="""
                Primera variable económica a modificar.

                Se analiza su impacto conjunto con la Variable 2.
                """
            )

            rango1 = st.slider(
                "Rango Variable 1 (%) ❓",
                10, 50, 30, 5,
                help="""
                Porcentaje máximo de variación de la Variable 1.

                Ejemplo:
                30% → se evalúa desde -30% hasta +30%
                """
            )

        with col2:
            var2 = st.selectbox(
                "Variable 2 ❓",
                ["Tasa de Descuento", "Flujos de Caja", "Inversión Inicial"],
                help="""
                Segunda variable económica que se analiza simultáneamente
                con la Variable 1.
                """
            )

            rango2 = st.slider(
                "Rango Variable 2 (%) ❓",
                10, 50, 30, 5,
                help="""
                Porcentaje máximo de variación de la Variable 2.
                """
            )

        st.caption("""
        ⚙️ El sistema genera una matriz de escenarios combinando
        todas las variaciones posibles de ambas variables.
        """)

        # =============================
        # VALIDACIÓN
        # =============================
        if var1 == var2:
            st.error("⚠️ Selecciona variables diferentes para realizar el análisis.")
        else:
            resultado = calcular_sensibilidad_bivariada(
                var1, var2, flujos, tasa, rango1, rango2
            )

            col_graf, col_kpi = st.columns([3, 1])

            # =============================
            # GRÁFICO
            # =============================
            with col_graf:

                st.markdown("### 🗺️ Mapa de Sensibilidad del VPN")

                st.caption("""
                Cada punto del gráfico representa un **escenario posible**
                según la combinación de ambas variables.

                • Colores positivos → VPN favorable  
                • Colores negativos → riesgo de pérdida  
                • Zonas planas → estabilidad
                """)

                fig = grafico_sensibilidad_bivariada(
                    resultado["vpn_matrix"],
                    resultado["vars1"],
                    resultado["vars2"],
                    var1, var2
                )
                st.plotly_chart(fig, use_container_width=True)

            # =============================
            # KPIs
            # =============================
            with col_kpi:

                st.metric(
                    "VPN Mínimo",
                    f"${resultado['vpn_min']:,.2f}",
                    help="Peor escenario económico dentro del rango analizado."
                )

                st.metric(
                    "VPN Máximo",
                    f"${resultado['vpn_max']:,.2f}",
                    help="Mejor escenario económico con ambas variables combinadas."
                )

                st.metric(
                    "VPN > 0",
                    f"{resultado['pct_positivo']:.1f}%",
                    help="""
                    Porcentaje de escenarios donde el proyecto
                    mantiene rentabilidad positiva.
                    """
                )

                st.caption("""
                📌 Un porcentaje bajo indica **alto riesgo conjunto**.
                """)

            # =============================
            # IA
            # =============================
            with st.expander("🤖 Interpretación con IA"):

                st.caption("""
                La IA analiza:
                • Zonas de riesgo y oportunidad  
                • Sensibilidad conjunta  
                • Robustez del proyecto ante cambios simultáneos
                """)

                if st.button("Generar interpretación", key="ia_bi"):
                    st.info(
                        interpretar_sensibilidad_bivariada_ia(
                            var1,
                            var2,
                            resultado["vars1"],
                            resultado["vars2"],
                            resultado["vpn_matrix"],
                            resultado["vpn_min"],
                            resultado["vpn_max"],
                            resultado["pct_positivo"]
                        )
                    )



    # =====================================================
    # 🌪️ TORNADO
    # =====================================================
    with tab_tor:

        st.subheader("🌪️ Análisis Tornado")

        st.info("""
        El **Análisis Tornado** identifica **qué variables tienen mayor impacto
        sobre el VPN del proyecto** cuando se modifican individualmente.

        Es una herramienta clave para:
        • Priorizar riesgos  
        • Identificar variables críticas  
        • Enfocar estrategias de mitigación
        """)

        # =============================
        # CONTROL DE RANGO
        # =============================
        rango = st.slider(
            "Rango de variación (%) ❓",
            10, 50, 20, 5,
            help="""
            Define cuánto puede variar cada variable económica.

            Ejemplo:
            20% → se evalúa el impacto desde -20% hasta +20%
            """
        )

        st.caption("""
        ⚙️ Cada variable se analiza de forma independiente manteniendo
        las demás constantes.
        """)

        # =============================
        # CÁLCULO
        # =============================
        vars_ordenadas = calcular_tornado(
            flujos, tasa, vpn_base, rango, calcular_vpn
        )

        max_rango = max(v[1]["rango"] for v in vars_ordenadas)

        col_graf, col_res = st.columns([3, 1])

        # =============================
        # GRÁFICO TORNADO
        # =============================
        with col_graf:

            st.markdown("### 📊 Gráfico Tornado – Impacto en el VPN")

            st.caption("""
            • Cada barra representa una variable económica  
            • La longitud indica el **impacto sobre el VPN**  
            • Las barras superiores son las **más críticas**
            """)

            fig = grafico_tornado(vars_ordenadas, vpn_base, rango)
            st.plotly_chart(fig, use_container_width=True)

            st.caption("""
            🔍 Cuanto más larga es la barra, **mayor es el riesgo asociado** a esa variable.
            """)

        # =============================
        # KPIs PRINCIPALES
        # =============================
        var_critica, datos = vars_ordenadas[0]

        with col_res:

            st.markdown("### 📌 Variable Más Crítica")

            st.metric(
                "Variable Crítica",
                var_critica,
                help="Variable que genera el mayor cambio en el VPN."
            )

            st.metric(
                "Impacto en el VPN",
                f"${datos['rango']:,.2f}",
                help="""
                Diferencia máxima del VPN al variar esta variable
                dentro del rango definido.
                """
            )

            st.metric(
                "Nivel de Riesgo",
                clasificar_riesgo(datos["rango"], max_rango),
                help="""
                Clasificación relativa del riesgo comparado con
                las demás variables analizadas.
                """
            )

            st.caption("""
            📌 Esta variable debería ser prioritaria en la gestión del proyecto.
            """)

        # =============================
        # TABLA DETALLADA
        # =============================
        with st.expander("📊 Ranking Detallado de Variables"):

            st.caption("""
            La tabla ordena las variables desde la más crítica
            hasta la menos sensible.
            """)

            tabla = tabla_tornado(vars_ordenadas)
            tabla["Riesgo"] = tabla["Rango"].apply(
                lambda x: clasificar_riesgo(
                    float(x.replace("$","").replace(",","")), max_rango
                )
            )

            st.dataframe(
                tabla,
                use_container_width=True,
                hide_index=True
            )

            st.caption("""
            🔴 Alto → Prioridad inmediata  
            🟠 Medio → Monitoreo continuo  
            🟢 Bajo → Riesgo controlado
            """)

        # =============================
        # IA
        # =============================
        with st.expander("🤖 Interpretación con IA"):

            st.caption("""
            La IA analiza:
            • Jerarquía de riesgos  
            • Sensibilidad del VPN  
            • Recomendaciones estratégicas
            """)

            if st.button("Generar interpretación", key="ia_tor"):
                st.info(
                    interpretar_tornado_completo_ia(
                        vars_ordenadas,
                        rango
                    )
                )



    # =====================================================
    # 📌 RESUMEN EJECUTIVO DE RIESGO
    # =====================================================
    with tab_res:

        st.subheader("📌 Resumen Ejecutivo de Riesgo")

        st.info("""
        Este resumen consolida todos los análisis del proyecto
        para responder rápidamente:
        • ¿Qué tan riesgoso es el proyecto?
        • ¿Existe probabilidad de pérdida?
        • ¿Qué variables requieren mayor control?
        """)

        # =============================
        # SIMULACIÓN MONTE CARLO
        # =============================
        st.markdown("### 🎲 Simulación Monte Carlo")
        st.caption("""
        ❓ **¿Qué es esto?**  
        Se generan miles de escenarios posibles del VPN
        variando los flujos y la tasa para modelar la incertidumbre real.
        """)

        vpns_mc = simulacion_montecarlo(flujos, tasa)

        riesgo = metricas_riesgo(vpns_mc)

        col1, col2 = st.columns(2)

        # =============================
        # MÉTRICAS DE RIESGO
        # =============================
        with col1:

            st.markdown("### 📊 Indicadores Clave")
            st.caption("Resumen numérico del comportamiento del VPN bajo riesgo")

            for k, v in riesgo.items():
                st.metric(
                    k,
                    f"{v:,.2f}" if isinstance(v, float) else v,
                    help={
                        "VPN Esperado": "Promedio del VPN considerando todos los escenarios simulados",
                        "Prob VPN < 0": "Probabilidad de que el proyecto genere pérdidas",
                        "VaR 95%": "Pérdida máxima esperada en el 95% de los casos",
                        "CVaR 95%": "Pérdida promedio en los peores escenarios"
                    }.get(k, "Indicador de riesgo financiero")
                )

        # =============================
        # GRÁFICO DE DISTRIBUCIÓN
        # =============================
        with col2:

            st.markdown("### 📈 Distribución del VPN")
            st.caption("""
            Representa todos los valores posibles del VPN obtenidos
            en la simulación.
            """)

            st.plotly_chart(
                grafico_distribucion_vpn(vpns_mc),
                use_container_width=True
            )

            st.caption("""
            🔍 **Cómo interpretarlo**  
            • Derecha de 0 → escenarios rentables  
            • Izquierda de 0 → escenarios de pérdida  
            • Mayor concentración positiva → menor riesgo
            """)

        # =============================
        # SEMÁFORO DE RIESGO
        # =============================
        st.markdown("### 🚦 Evaluación Global")
        st.caption("Clasificación visual del nivel de riesgo del proyecto")

        st.success(semaforo_riesgo(riesgo["Prob VPN < 0"]))

        # =============================
        # RANKING DE VARIABLES
        # =============================
        st.markdown("### 🧭 Variables Críticas")
        st.caption("Variables ordenadas según su impacto en el VPN")

        ranking = [
            {
                "Variable": v,
                "Impacto VPN": f"${d['rango']:,.2f}",
                "Riesgo": clasificar_riesgo(d["rango"], max_rango)
            }
            for v, d in vars_ordenadas
        ]

        st.dataframe(pd.DataFrame(ranking), use_container_width=True)

        # =============================
        # CONCLUSIÓN
        # =============================
        with st.expander("🤖 Interpretación con IA"):
            st.caption("""
            La IA explica de forma integral:
            • Riesgo global del proyecto  
            • Resultados probabilísticos  
            • Variables críticas  
            • Recomendaciones finales
            """)

            if st.button("Generar interpretación", key="ia_res"):
                st.info(
                    interpretar_resumen_riesgo_ia(
                        riesgo,
                        vpns_mc,
                        vars_ordenadas
                    )
                )





