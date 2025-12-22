

import numpy as np
import plotly.graph_objects as go


def calcular_wacc(patrimonio, deuda, costo_patrimonio, costo_deuda, tasa_impuesto):
    """Calcula el Costo Promedio Ponderado de Capital (WACC)"""
    total = patrimonio + deuda
    if total == 0:
        return 0
    wacc = (patrimonio/total * costo_patrimonio/100) + (deuda/total * costo_deuda/100 * (1 - tasa_impuesto/100))
    return wacc * 100


def calcular_capm(tasa_libre_riesgo, beta, prima_mercado, prima_pais):
    """
    Calcula el costo del patrimonio usando CAPM.
    
    Args:
        tasa_libre_riesgo: Tasa libre de riesgo (%)
        beta: Beta del sector
        prima_mercado: Prima de riesgo del mercado (%)
        prima_pais: Prima de riesgo país (%)
    
    Returns:
        Costo del patrimonio según CAPM (%)
    """
    return tasa_libre_riesgo + beta * prima_mercado + prima_pais


def calcular_proporciones_capital(patrimonio, deuda):
    """
    Calcula las proporciones de patrimonio y deuda.
    
    Returns:
        Tupla con (prop_patrimonio, prop_deuda, total_inversion)
    """
    total = patrimonio + deuda
    if total == 0:
        return 0, 0, 0
    return patrimonio / total, deuda / total, total


def calcular_escudo_fiscal(deuda, costo_deuda, tasa_impuesto):
    """
    Calcula el ahorro fiscal anual por uso de deuda.
    
    Returns:
        Escudo fiscal en unidades monetarias
    """
    return deuda * (costo_deuda / 100) * (tasa_impuesto / 100)


def crear_grafico_estructura_capital(patrimonio, deuda, prop_patrimonio, prop_deuda):
    """Crea gráfico de dona de la estructura de capital."""
    fig = go.Figure(data=[go.Pie(
        labels=['Patrimonio', 'Deuda'],
        values=[patrimonio, deuda],
        hole=0.4,
        marker_colors=['#4CAF50', '#FF9800'],
        text=[f"${patrimonio:,.0f}<br>{prop_patrimonio*100:.1f}%",
              f"${deuda:,.0f}<br>{prop_deuda*100:.1f}%"],
        textposition='auto'
    )])
    fig.update_layout(title="Estructura de Capital", height=400)
    return fig


def crear_grafico_componentes_wacc(costo_patrimonio_ponderado, costo_deuda_ponderado, wacc):
    """Crea gráfico de barras con componentes del WACC."""
    fig = go.Figure(data=[go.Bar(
        x=['Costo Patrimonio', 'Costo Deuda (después impuestos)', 'WACC'],
        y=[costo_patrimonio_ponderado, costo_deuda_ponderado, wacc],
        marker_color=['#4CAF50', '#FF9800', '#2196F3'],
        text=[f"{costo_patrimonio_ponderado:.2f}%", 
              f"{costo_deuda_ponderado:.2f}%",
              f"{wacc:.2f}%"],
        textposition='auto'
    )])
    fig.update_layout(title="Componentes del WACC (%)", yaxis_title="Tasa (%)", height=400)
    return fig


def calcular_sensibilidad_wacc(total_inversion, costo_patrimonio, costo_deuda, tasa_impuesto):
    """
    Calcula la sensibilidad del WACC respecto a diferentes relaciones D/E.
    
    Returns:
        Tupla con (ratios_de, waccs)
    """
    ratios_de = np.linspace(0, 2, 20)
    waccs = []
    
    for ratio in ratios_de:
        if ratio == 0:
            d = 0
            e = total_inversion
        else:
            d = total_inversion * ratio / (1 + ratio)
            e = total_inversion - d
        wacc_temp = calcular_wacc(e, d, costo_patrimonio, costo_deuda, tasa_impuesto)
        waccs.append(wacc_temp)
    
    return ratios_de, waccs


def crear_grafico_sensibilidad_wacc(ratios_de, waccs, ratio_actual):
    """Crea gráfico de sensibilidad del WACC vs D/E ratio."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ratios_de, y=waccs, mode='lines+markers',
        line=dict(color='blue', width=3),
        marker=dict(size=8)
    ))
    fig.add_vline(x=ratio_actual, 
                  line_dash="dash", line_color="red",
                  annotation_text="Estructura Actual")
    fig.update_layout(
        title="WACC vs Relación Deuda/Patrimonio",
        xaxis_title="D/E Ratio",
        yaxis_title="WACC (%)",
        height=400
    )
    return fig