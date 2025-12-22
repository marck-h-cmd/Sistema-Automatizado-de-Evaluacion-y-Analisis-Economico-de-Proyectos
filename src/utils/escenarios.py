

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from src.utils.eval_basica import calcular_vpn, calcular_tir, calcular_bc


def calcular_escenarios(flujos_base, factor_pesimista, factor_optimista, tasa_descuento):
    """
    Calcula los indicadores (VPN, TIR, B/C) para los tres escenarios.
    
    Args:
        flujos_base: Lista de flujos del escenario base
        factor_pesimista: Factor de reducción para escenario pesimista (0.3-0.9)
        factor_optimista: Factor de incremento para escenario optimista (1.1-2.0)
        tasa_descuento: Tasa de descuento en formato decimal (ej: 0.12 para 12%)
    
    Returns:
        dict: Diccionario con indicadores para cada escenario (pes, base, opt)
    """
    # Pesimista
    flujos_pes = [flujos_base[0]] + [f * factor_pesimista for f in flujos_base[1:]]
    vpn_pes = calcular_vpn(flujos_pes, tasa_descuento)
    tir_pes = calcular_tir(flujos_pes)
    bc_pes = calcular_bc(flujos_pes, tasa_descuento)
    
    # Base
    vpn_base = calcular_vpn(flujos_base, tasa_descuento)
    tir_base = calcular_tir(flujos_base)
    bc_base = calcular_bc(flujos_base, tasa_descuento)
    
    # Optimista
    flujos_opt = [flujos_base[0]] + [f * factor_optimista for f in flujos_base[1:]]
    vpn_opt = calcular_vpn(flujos_opt, tasa_descuento)
    tir_opt = calcular_tir(flujos_opt)
    bc_opt = calcular_bc(flujos_opt, tasa_descuento)
    
    return {
        'pesimista': {'vpn': vpn_pes, 'tir': tir_pes, 'bc': bc_pes, 'flujos': flujos_pes},
        'base': {'vpn': vpn_base, 'tir': tir_base, 'bc': bc_base, 'flujos': flujos_base},
        'optimista': {'vpn': vpn_opt, 'tir': tir_opt, 'bc': bc_opt, 'flujos': flujos_opt}
    }


def calcular_estadisticas_escenarios(vpn_pes, vpn_base, vpn_opt, 
                                     prob_pesimista, prob_base, prob_optimista):
    """
    Calcula estadísticas de riesgo del análisis de escenarios.
    
    Args:
        vpn_pes, vpn_base, vpn_opt: VPN de cada escenario
        prob_pesimista, prob_base, prob_optimista: Probabilidades en porcentaje (0-100)
    
    Returns:
        dict: Diccionario con VPN esperado, desviación estándar, rango, coef. variación y prob. éxito
    """
    # Convertir probabilidades a decimales
    probs = [prob_pesimista/100, prob_base/100, prob_optimista/100]
    vpns = [vpn_pes, vpn_base, vpn_opt]
    
    # VPN Esperado
    vpn_esperado = sum([v * p for v, p in zip(vpns, probs)])
    
    # Desviación Estándar
    desv_std = np.sqrt(sum([p * (v - vpn_esperado)**2 for v, p in zip(vpns, probs)]))
    
    # Rango
    rango = vpn_opt - vpn_pes
    
    # Coeficiente de Variación
    coef_var = (desv_std / abs(vpn_esperado) * 100) if vpn_esperado != 0 else 0
    
    # Probabilidad de éxito
    prob_exito = (prob_base + prob_optimista) if vpn_base > 0 else prob_optimista
    
    return {
        'vpn_esperado': vpn_esperado,
        'desv_std': desv_std,
        'rango': rango,
        'coef_var': coef_var,
        'prob_exito': prob_exito
    }


def crear_tabla_escenarios(prob_pesimista, prob_base, prob_optimista,
                           vpn_pes, vpn_base, vpn_opt,
                           tir_pes, tir_base, tir_opt,
                           bc_pes, bc_base, bc_opt):
    """
    Crea un DataFrame con la tabla comparativa de escenarios.
    
    Returns:
        pd.DataFrame: Tabla con resultados de los tres escenarios
    """
    df = pd.DataFrame({
        'Escenario': ['Pesimista', 'Base', 'Optimista'],
        'Probabilidad': [f"{prob_pesimista}%", f"{prob_base}%", f"{prob_optimista}%"],
        'VPN': [f"${vpn_pes:,.2f}", f"${vpn_base:,.2f}", f"${vpn_opt:,.2f}"],
        'TIR': [f"{tir_pes:.2f}%" if tir_pes else "N/A", 
               f"{tir_base:.2f}%" if tir_base else "N/A",
               f"{tir_opt:.2f}%" if tir_opt else "N/A"],
        'B/C': [f"{bc_pes:.2f}", f"{bc_base:.2f}", f"{bc_opt:.2f}"]
    })
    return df


def crear_grafico_vpn(vpn_pes, vpn_base, vpn_opt):
    """Crea gráfico de barras de VPN por escenario."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=['Pesimista', 'Base', 'Optimista'],
        y=[vpn_pes, vpn_base, vpn_opt],
        marker_color=['#ff6b6b', '#ffd93d', '#6bcf7f'],
        text=[f'${vpn_pes:,.0f}', f'${vpn_base:,.0f}', f'${vpn_opt:,.0f}'],
        textposition='outside',
        showlegend=False
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="gray", 
                 annotation_text="Equilibrio")
    fig.update_layout(
        yaxis_title="VPN ($)",
        height=350,
        margin=dict(t=20, b=20),
        hovermode='x'
    )
    return fig


def crear_grafico_tir(tir_pes, tir_base, tir_opt, wacc=None):
    """
    Crea gráfico de barras de TIR por escenario.
    
    Args:
        tir_pes, tir_base, tir_opt: TIR de cada escenario
        wacc: Tasa de descuento/WACC (opcional) para línea de referencia
    """
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=['Pesimista', 'Base', 'Optimista'],
        y=[tir_pes if tir_pes else 0, tir_base if tir_base else 0, tir_opt if tir_opt else 0],
        marker_color=['#ff8787', '#ffe066', '#8ce99a'],
        text=[f'{tir_pes:.1f}%' if tir_pes else 'N/A', 
              f'{tir_base:.1f}%' if tir_base else 'N/A',
              f'{tir_opt:.1f}%' if tir_opt else 'N/A'],
        textposition='outside',
        showlegend=False
    ))
    
    if wacc is not None:
        fig.add_hline(y=wacc, line_dash="dash", line_color="red", 
                     annotation_text=f"WACC: {wacc}%")
    
    fig.update_layout(
        yaxis_title="TIR (%)",
        height=350,
        margin=dict(t=20, b=20),
        hovermode='x'
    )
    return fig


def crear_grafico_bc(bc_pes, bc_base, bc_opt):
    """Crea gráfico de barras de Relación B/C por escenario."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=['Pesimista', 'Base', 'Optimista'],
        y=[bc_pes, bc_base, bc_opt],
        marker_color=['#ffa8a8', '#ffec99', '#b2f2bb'],
        text=[f'{bc_pes:.2f}', f'{bc_base:.2f}', f'{bc_opt:.2f}'],
        textposition='outside',
        showlegend=False
    ))
    fig.add_hline(y=1, line_dash="dash", line_color="gray", 
                annotation_text="B/C = 1")
    fig.update_layout(
        yaxis_title="Relación B/C",
        height=350,
        margin=dict(t=20, b=20),
        hovermode='x'
    )
    return fig


def crear_grafico_distribucion(vpn_pes, vpn_base, vpn_opt,
                               prob_pesimista, prob_base, prob_optimista,
                               vpn_esperado):
    """Crea gráfico de distribución de probabilidades."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[vpn_pes, vpn_base, vpn_opt],
        y=[prob_pesimista, prob_base, prob_optimista],
        mode='markers+lines',
        marker=dict(
            size=[prob_pesimista*2, prob_base*2, prob_optimista*2],
            color=['#ff6b6b', '#ffd93d', '#6bcf7f'],
            line=dict(width=2, color='white')
        ),
        line=dict(color='gray', dash='dot', width=2),
        name='Distribución'
    ))
    fig.add_vline(x=vpn_esperado, line_dash="dash", line_color="blue", line_width=2,
              annotation_text=f"VPN Esperado: ${vpn_esperado:,.0f}")
    fig.update_layout(
        xaxis_title="VPN ($)", 
        yaxis_title="Probabilidad (%)",
        height=400,
        hovermode='closest',
        showlegend=False
    )
    return fig


def crear_grafico_probabilidades(prob_pesimista, prob_base, prob_optimista):
    """Crea gráfico de dona (pie chart) con las probabilidades."""
    fig = go.Figure(data=[go.Pie(
        labels=['Pesimista', 'Base', 'Optimista'],
        values=[prob_pesimista, prob_base, prob_optimista],
        hole=0.4,
        marker_colors=['#ff6b6b', '#ffd93d', '#6bcf7f']
    )])
    fig.update_layout(height=300)
    return fig
