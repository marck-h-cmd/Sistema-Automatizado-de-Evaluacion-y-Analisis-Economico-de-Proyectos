import streamlit as st
from src.utils.ai import consultar_groq
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from src.utils.eval_basica import calcular_vpn, calcular_tir, calcular_bc
import pandas as pd


# ======================================================
# FUNCIONES AUXILIARES DE RIESGO
# ======================================================

def calcular_elasticidad(vpns, variaciones):
    """Calcula la elasticidad del VPN respecto a variaciones en una variable."""
    base = vpns[len(vpns)//2]
    delta_vpn = (max(vpns) - min(vpns)) / base
    delta_var = (max(variaciones) - min(variaciones)) / 100
    return delta_vpn / delta_var if delta_var != 0 else 0


def margen_seguridad(punto_eq):
    """Calcula el margen de seguridad basado en el punto de equilibrio."""
    return abs(punto_eq) if punto_eq is not None else None


def clasificar_riesgo(rango, max_rango):
    """Clasifica el nivel de riesgo en función del rango de impacto."""
    ratio = rango / max_rango
    if ratio > 0.66:
        return "🔴 Alto"
    elif ratio > 0.33:
        return "🟠 Medio"
    return "🟢 Bajo"


def simulacion_montecarlo(flujos, tasa, n=10000):
    """
    Ejecuta simulación Monte Carlo para el VPN.
    
    Args:
        flujos: Array de flujos de caja
        tasa: Tasa de descuento
        n: Número de simulaciones (default: 10000)
    
    Returns:
        Array con los VPN simulados
    """
    vpns = []
    flujos_array = np.array(flujos)
    for _ in range(n):
        flujos_sim = flujos_array * np.random.normal(1, 0.1, len(flujos_array))
        tasa_sim = tasa * np.random.normal(1, 0.05)
        vpns.append(calcular_vpn(flujos_sim, tasa_sim / 100))
    return np.array(vpns)


def escenarios_criticos(vpns):
    """Identifica escenarios críticos: peor, base y mejor."""
    return {
        "Peor Escenario": min(vpns),
        "Caso Base": vpns[len(vpns)//2],
        "Mejor Escenario": max(vpns)
    }


def elasticidad_generica(valores):
    """Calcula elasticidad genérica para cualquier indicador."""
    base = valores[len(valores)//2]
    return (max(valores) - min(valores)) / abs(base) if base != 0 else 0


def indice_estabilidad(vpns, vpn_base):
    """Calcula índice de estabilidad del proyecto."""
    return np.std(vpns) / abs(vpn_base) if vpn_base != 0 else 0


def pendiente_vpn(vpns, variaciones):
    """Calcula la pendiente de cambio del VPN."""
    return (vpns[-1] - vpns[0]) / (variaciones[-1] - variaciones[0])


def metricas_riesgo(vpns):
    """Calcula métricas de riesgo basadas en simulación."""
    return {
        "VPN Esperado": np.mean(vpns),
        "Desviación": np.std(vpns),
        "Prob VPN < 0": np.mean(vpns < 0) * 100,
        "VaR 5%": np.percentile(vpns, 5),
        "CVaR 5%": vpns[vpns <= np.percentile(vpns, 5)].mean()
    }


def grafico_distribucion_vpn(vpns):
    """Crea histograma de distribución del VPN."""
    fig = px.histogram(vpns, nbins=50, title="Distribución del VPN")
    fig.add_vline(x=0, line_dash="dash", line_color="red")
    return fig


def semaforo_riesgo(prob_neg):
    """Clasifica el riesgo según probabilidad de VPN negativo."""
    if prob_neg > 40:
        return "🔴 Riesgo Alto"
    elif prob_neg > 20:
        return "🟠 Riesgo Medio"
    return "🟢 Riesgo Bajo"



def interpretar_sensibilidad_univariada_ia(
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
    punto_equilibrio=None,
    escenarios=None
):
    """
    Genera una interpretación completa del análisis de sensibilidad univariada
    explicando todos los KPIs, gráficos y riesgos para usuarios no expertos.
    """

    resumen = f"""
    ANÁLISIS REALIZADO:
    Sensibilidad Univariada

    VARIABLE ANALIZADA:
    {variable}

    RANGO DE VARIACIÓN:
    Desde {min(variaciones):+.1f}% hasta {max(variaciones):+.1f}%

    RESULTADOS PRINCIPALES:
    VPN mínimo: {min(vpns):,.2f}
    VPN máximo: {max(vpns):,.2f}

    TIR mínima: {min(tirs):.2f}
    TIR máxima: {max(tirs):.2f}

    B/C mínimo: {min(bcs):.2f}
    B/C máximo: {max(bcs):.2f}

    MÉTRICAS DE RIESGO:
    Elasticidad VPN: {elasticidad_vpn:.2f}
    Elasticidad TIR: {elasticidad_tir:.2f}
    Elasticidad B/C: {elasticidad_bc:.2f}

    Índice de estabilidad: {estabilidad:.2f}
    Pendiente del VPN: {pendiente:.2f}
    """

    if punto_equilibrio is not None:
        resumen += f"\nPunto de equilibrio (VPN = 0): {punto_equilibrio:+.1f}%\n"

    if escenarios:
        resumen += f"\nEscenarios críticos identificados: {escenarios}\n"

    prompt = f"""
    Eres un analista financiero senior especializado en evaluación de proyectos.

    Con base en la siguiente información del análisis de sensibilidad univariada:

    {resumen}

    Explica de forma clara, intuitiva y estructurada:

    1. Qué significa este análisis y por qué es importante.
    2. Cómo afecta la variable analizada a la rentabilidad del proyecto.
    3. Interpretación del comportamiento del VPN, TIR y B/C.
    4. Qué indican las elasticidades sobre el riesgo del proyecto.
    5. Qué nos dice el índice de estabilidad y la pendiente del VPN.
    6. Cómo interpretar el gráfico de sensibilidad (tendencias y riesgos).
    7. Qué implica el punto de equilibrio y el margen de seguridad.
    8. Evaluación general del riesgo del proyecto.
    9. Recomendaciones prácticas para la toma de decisiones.

    Usa un lenguaje comprensible para usuarios no expertos,
    con viñetas claras y conclusiones accionables.
    """

    return consultar_groq(prompt)



def grafico_sensibilidad_univariada(
    variaciones,
    vpns,
    tirs,
    bcs,
    variable,
    tmar
):
    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=[
            "Sensibilidad VPN",
            "Sensibilidad TIR",
            "Sensibilidad B/C"
        ]
    )

    # VPN
    fig.add_trace(
        go.Scatter(
            x=variaciones,
            y=vpns,
            mode="lines+markers",
            line=dict(width=3),
            name="VPN"
        ),
        row=1, col=1
    )
    fig.add_hline(y=0, line_dash="dash", row=1, col=1)

    # TIR
    fig.add_trace(
        go.Scatter(
            x=variaciones,
            y=tirs,
            mode="lines+markers",
            line=dict(width=3),
            name="TIR"
        ),
        row=1, col=2
    )
    fig.add_hline(y=tmar, line_dash="dash", row=1, col=2)

    # B/C
    fig.add_trace(
        go.Scatter(
            x=variaciones,
            y=bcs,
            mode="lines+markers",
            line=dict(width=3),
            name="B/C"
        ),
        row=1, col=3
    )
    fig.add_hline(y=1, line_dash="dash", row=1, col=3)

    # Ejes
    for col in [1, 2, 3]:
        fig.update_xaxes(
            title_text=f"Variación de {variable} (%)",
            row=1, col=col
        )

    fig.update_yaxes(title_text="VPN ($)", row=1, col=1)
    fig.update_yaxes(title_text="TIR (%)", row=1, col=2)
    fig.update_yaxes(title_text="B/C", row=1, col=3)

    fig.update_layout(
        height=400,
        showlegend=False
    )

    return fig

def aplicar_variacion(
    variable,
    flujos_base,
    tasa_base,
    variacion_pct
):
    flujos = flujos_base.copy()
    tasa = tasa_base

    if variable == "Flujos de Caja":
        factor = 1 + variacion_pct / 100
        flujos = [flujos[0]] + [f * factor for f in flujos[1:]]

    elif variable == "Tasa de Descuento":
        tasa = tasa_base * (1 + variacion_pct / 100)

    elif variable == "Inversión Inicial":
        factor = 1 + variacion_pct / 100
        flujos[0] = flujos[0] * factor

    return flujos, tasa


def calcular_sensibilidad_univariada(
    variable,
    flujos_base,
    tasa_base,
    rango_pct,
    puntos=20
):
    variaciones = np.linspace(-rango_pct, rango_pct, puntos)

    vpns = []
    tirs = []
    bcs = []

    for v in variaciones:
        flujos_mod, tasa_mod = aplicar_variacion(
            variable,
            flujos_base,
            tasa_base,
            v
        )

        vpns.append(calcular_vpn(flujos_mod, tasa_mod / 100))
        tirs.append(calcular_tir(flujos_mod) or 0)
        bcs.append(calcular_bc(flujos_mod, tasa_mod / 100))

    # Punto de equilibrio
    vpn_positivos = [i for i, v in enumerate(vpns) if v > 0]
    punto_equilibrio = (
        variaciones[min(vpn_positivos, key=lambda i: abs(vpns[i]))]
        if vpn_positivos else None
    )

    return {
        "variaciones": variaciones,
        "vpns": vpns,
        "tirs": tirs,
        "bcs": bcs,
        "punto_equilibrio": punto_equilibrio
    }


















#Sensibilidad Bivariada

def interpretar_sensibilidad_bivariada_ia(
    var1,
    var2,
    vars1,
    vars2,
    vpn_matrix,
    vpn_min,
    vpn_max,
    pct_positivo
):
    """
    Genera una interpretación completa y pedagógica
    del análisis de sensibilidad bivariada para usuarios no expertos.
    """

    resumen = f"""
    ANÁLISIS REALIZADO:
    Sensibilidad Bivariada

    VARIABLES ANALIZADAS:
    Variable 1: {var1}
    Variable 2: {var2}

    RANGO DE VARIACIÓN:
    {var1}: desde {min(vars1):+.1f}% hasta {max(vars1):+.1f}%
    {var2}: desde {min(vars2):+.1f}% hasta {max(vars2):+.1f}%

    RESULTADOS DEL VPN:
    VPN mínimo: {vpn_min:,.2f}
    VPN máximo: {vpn_max:,.2f}

    ROBUSTEZ DEL PROYECTO:
    Porcentaje de escenarios con VPN positivo: {pct_positivo:.1f}%
    """

    prompt = f"""
    Eres un analista financiero senior especializado en evaluación de proyectos.

    A partir del siguiente análisis de sensibilidad bivariada:

    {resumen}

    Explica de forma clara, intuitiva y estructurada lo siguiente:

    1. Qué es la sensibilidad bivariada y por qué es importante.
    2. Cómo interactúan ambas variables y por qué analizarlas juntas.
    3. Cómo interpretar el mapa de sensibilidad (colores, zonas y patrones).
    4. Identificación de:
       • Zonas de alto riesgo
       • Zonas de oportunidad
       • Zonas de estabilidad
    5. Qué indica el VPN mínimo y máximo sobre el riesgo total.
    6. Qué significa el porcentaje de VPN positivo para la robustez del proyecto.
    7. Evaluación general del nivel de riesgo conjunto.
    8. Recomendaciones prácticas para:
       • Gestión del riesgo
       • Toma de decisiones
       • Variables a monitorear

    Usa un lenguaje comprensible para usuarios no expertos,
    con viñetas claras, ejemplos simples y conclusiones accionables.
    """

    return consultar_groq(prompt)


def aplicar_variacion(
    variable,
    flujos_base,
    tasa_base,
    variacion_pct
):
    flujos = flujos_base.copy()
    tasa = tasa_base

    if variable == "Flujos de Caja":
        flujos = [flujos[0]] + [f * (1 + variacion_pct / 100) for f in flujos[1:]]

    elif variable == "Tasa de Descuento":
        tasa = tasa_base * (1 + variacion_pct / 100)

    elif variable == "Inversión Inicial":
        flujos[0] = flujos[0] * (1 + variacion_pct / 100)

    return flujos, tasa



def calcular_sensibilidad_bivariada(
    var1,
    var2,
    flujos_base,
    tasa_base,
    rango1,
    rango2,
    puntos=15
):
    vars1 = np.linspace(-rango1, rango1, puntos)
    vars2 = np.linspace(-rango2, rango2, puntos)

    vpn_matrix = np.zeros((len(vars1), len(vars2)))

    for i, v1 in enumerate(vars1):
        for j, v2 in enumerate(vars2):
            # Aplicar variación 1
            flujos_1, tasa_1 = aplicar_variacion(
                var1, flujos_base, tasa_base, v1
            )

            # Aplicar variación 2 sobre el resultado
            flujos_2, tasa_2 = aplicar_variacion(
                var2, flujos_1, tasa_1, v2
            )

            vpn_matrix[i, j] = calcular_vpn(flujos_2, tasa_2 / 100)

    # Métricas clave
    vpn_min = vpn_matrix.min()
    vpn_max = vpn_matrix.max()
    pct_positivo = (vpn_matrix > 0).sum() / vpn_matrix.size * 100

    return {
        "vars1": vars1,
        "vars2": vars2,
        "vpn_matrix": vpn_matrix,
        "vpn_min": vpn_min,
        "vpn_max": vpn_max,
        "pct_positivo": pct_positivo
    }


def grafico_sensibilidad_bivariada(
    vpn_matrix,
    vars1,
    vars2,
    var1,
    var2
):
    """
    Genera el mapa de contorno para el análisis de sensibilidad bivariada.
    Incluye la línea VPN = 0.
    """

    fig = go.Figure(
        data=go.Contour(
            z=vpn_matrix,
            x=vars2,
            y=vars1,
            colorscale="RdYlGn",
            contours=dict(
                start=vpn_matrix.min(),
                end=vpn_matrix.max(),
                size=(vpn_matrix.max() - vpn_matrix.min()) / 20,
                showlabels=True
            ),
            colorbar=dict(title="VPN ($)")
        )
    )

    # Línea crítica VPN = 0
    fig.add_contour(
        z=vpn_matrix,
        x=vars2,
        y=vars1,
        showscale=False,
        contours=dict(
            start=0,
            end=0,
            size=1,
            coloring="lines"
        ),
        line=dict(color="red", width=3)
    )

    fig.update_layout(
        title="Mapa de Sensibilidad (Línea roja: VPN = 0)",
        xaxis_title=f"Variación {var2} (%)",
        yaxis_title=f"Variación {var1} (%)",
        height=600
    )

    return fig










#Analisis Tornado

def interpretar_tornado_completo_ia(vars_ordenadas, rango):
    """
    Genera una interpretación pedagógica y completa del Análisis Tornado,
    orientada a usuarios inexpertos.
    """

    # Extraer variable crítica
    var_critica, datos_criticos = vars_ordenadas[0]

    # Crear resumen estructurado
    resumen = f"""
    ANÁLISIS REALIZADO:
    Análisis Tornado (Sensibilidad Univariada Comparativa)

    RANGO DE VARIACIÓN ANALIZADO:
    ±{rango}%

    VARIABLE MÁS CRÍTICA:
    {var_critica}

    IMPACTO DE LA VARIABLE CRÍTICA:
    Cambio máximo en el VPN: {datos_criticos['rango']:,.2f}

    RANKING DE VARIABLES (de mayor a menor impacto):
    """

    for v, d in vars_ordenadas:
        resumen += f"- {v}: impacto VPN = {d['rango']:,.2f}\n"

    prompt = f"""
    Eres un analista financiero experto en evaluación y gestión de riesgos,
    y debes explicar los resultados a una persona sin conocimientos técnicos.

    Con base en el siguiente análisis Tornado:

    {resumen}

    Proporciona una explicación clara, didáctica y estructurada que incluya:

    1. Qué es el Análisis Tornado y por qué se utiliza.
    2. Cómo interpretar el gráfico Tornado:
       • Qué representan las barras
       • Por qué están ordenadas
       • Qué significa la longitud de cada barra
    3. Explicación detallada de la variable más crítica:
       • Por qué es la más riesgosa
       • Qué implicaciones tiene para el proyecto
    4. Interpretación del impacto en el VPN:
       • Qué significa un impacto alto o bajo
       • Cómo afecta la creación de valor
    5. Análisis del ranking completo de variables:
       • Diferencia entre riesgos altos, medios y bajos
       • Cómo usar esta información para priorizar esfuerzos
    6. Evaluación general del nivel de riesgo del proyecto.
    7. Recomendaciones prácticas y accionables para:
       • Mitigar riesgos
       • Monitorear variables críticas
       • Tomar mejores decisiones financieras

    Usa un lenguaje sencillo, ejemplos intuitivos y conclusiones claras.
    Evita tecnicismos innecesarios.
    """

    return consultar_groq(prompt)




def grafico_tornado(vars_ordenadas, vpn_base, rango_tornado):
    """
    Genera el diagrama tornado del VPN.
    """

    fig = go.Figure()

    for i, (var_name, datos) in enumerate(vars_ordenadas):

        fig.add_trace(go.Bar(
            y=[var_name],
            x=[datos["min"] - vpn_base],
            orientation="h",
            name=f"-{rango_tornado}%",
            marker_color="#ff6b6b",
            showlegend=(i == 0),
            text=f"${datos['min']:,.0f}",
            textposition="inside"
        ))

        fig.add_trace(go.Bar(
            y=[var_name],
            x=[datos["max"] - vpn_base],
            orientation="h",
            name=f"+{rango_tornado}%",
            marker_color="#6bcf7f",
            showlegend=(i == 0),
            text=f"${datos['max']:,.0f}",
            textposition="inside"
        ))

    fig.add_vline(x=0, line_dash="dash", line_color="black", line_width=2)

    fig.update_layout(
        title=f"Diagrama Tornado – Variación del VPN (±{rango_tornado}%)",
        xaxis_title="Variación del VPN respecto al caso base ($)",
        yaxis_title="Variables",
        barmode="overlay",
        height=400,
        showlegend=True
    )

    return fig


def calcular_tornado(
    flujos_base,
    tasa_base,
    vpn_base,
    rango_tornado,
    calcular_vpn
):
    """
    Calcula el impacto de cada variable sobre el VPN.
    Retorna lista ordenada por impacto.
    """

    variables = {}

    for var_name in ["Flujos de Caja", "Tasa de Descuento", "Inversión Inicial"]:

        if var_name == "Flujos de Caja":
            flujos_min = [flujos_base[0]] + [f * (1 - rango_tornado/100) for f in flujos_base[1:]]
            flujos_max = [flujos_base[0]] + [f * (1 + rango_tornado/100) for f in flujos_base[1:]]

            vpn_min = calcular_vpn(flujos_min, tasa_base/100)
            vpn_max = calcular_vpn(flujos_max, tasa_base/100)

        elif var_name == "Tasa de Descuento":
            tasa_min = tasa_base * (1 - rango_tornado/100)
            tasa_max = tasa_base * (1 + rango_tornado/100)

            vpn_min = calcular_vpn(flujos_base, tasa_max/100)
            vpn_max = calcular_vpn(flujos_base, tasa_min/100)

        else:  # Inversión Inicial
            flujos_min = [flujos_base[0] * (1 + rango_tornado/100)] + flujos_base[1:]
            flujos_max = [flujos_base[0] * (1 - rango_tornado/100)] + flujos_base[1:]

            vpn_min = calcular_vpn(flujos_min, tasa_base/100)
            vpn_max = calcular_vpn(flujos_max, tasa_base/100)

        variables[var_name] = {
            "min": vpn_min,
            "max": vpn_max,
            "rango": abs(vpn_max - vpn_min)
        }

    # Ordenar por impacto
    return sorted(variables.items(), key=lambda x: x[1]["rango"], reverse=True)



def tabla_tornado(vars_ordenadas):
    """
    Construye la tabla de impacto del análisis tornado.
    """

    max_rango = max(v["rango"] for _, v in vars_ordenadas)

    return pd.DataFrame([
        {
            "Variable": var,
            "VPN Mínimo": f"${datos['min']:,.2f}",
            "VPN Máximo": f"${datos['max']:,.2f}",
            "Rango": f"${datos['rango']:,.2f}",
            "Sensibilidad": "🔴" * int((datos["rango"] / max_rango) * 5)
        }
        for var, datos in vars_ordenadas
    ])
    
    

def interpretar_resumen_riesgo_ia(riesgo, vpns_mc, vars_ordenadas):
    """
    Interpretación integral del Resumen Ejecutivo de Riesgo,
    orientada a usuarios inexpertos.
    """

    # Variable más crítica
    var_critica, datos_criticos = vars_ordenadas[0]

    resumen = f"""
    RESUMEN EJECUTIVO DE RIESGO DEL PROYECTO

    SIMULACIÓN MONTE CARLO:
    - Número de escenarios simulados: {len(vpns_mc)}

    INDICADORES DE RIESGO:
    """

    for k, v in riesgo.items():
        resumen += f"- {k}: {v}\n"

    resumen += f"""
    VARIABLE MÁS CRÍTICA:
    - {var_critica}
    - Impacto máximo en el VPN: {datos_criticos['rango']:,.2f}
    """

    prompt = f"""
    Eres un consultor financiero experto en evaluación de proyectos
    y debes explicar los resultados a un usuario sin conocimientos técnicos.

    Con base en la siguiente información:

    {resumen}

    Proporciona una explicación clara, completa y didáctica que incluya:

    1. Qué es el Resumen Ejecutivo de Riesgo y para qué sirve.
    2. Explicación sencilla de la Simulación Monte Carlo:
       • Qué significa simular miles de escenarios
       • Por qué es importante para medir riesgo real
    3. Interpretación de cada indicador de riesgo:
       • VPN Esperado
       • Probabilidad de VPN negativo
       • VaR 95%
       • CVaR 95%
       Explica qué significa cada uno y cómo leer valores altos o bajos.
    4. Explicación del gráfico de distribución del VPN:
       • Qué representan las barras
       • Qué significa la zona positiva y negativa
       • Cómo identificar proyectos riesgosos o estables
    5. Interpretación del semáforo de riesgo:
       • Qué significa verde, amarillo y rojo
       • Qué decisión tomar en cada caso
    6. Análisis del ranking de variables críticas:
       • Por qué una variable es más peligrosa que otra
       • Cómo usar este ranking para priorizar controles
    7. Evaluación global del proyecto:
       • Nivel de riesgo general
       • Robustez del proyecto ante incertidumbre
    8. Recomendaciones prácticas y accionables para:
       • Reducir riesgo
       • Mejorar estabilidad financiera
       • Apoyar la toma de decisiones gerenciales

    Usa un lenguaje sencillo, ejemplos intuitivos
    y conclusiones claras.
    Evita tecnicismos innecesarios.
    """

    return consultar_groq(prompt)
