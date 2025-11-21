import streamlit as st
from plotly.subplots import make_subplots   
import plotly.graph_objects as go
from src.utils.wacc import calcular_wacc
from src.utils.eval_basica import calcular_vpn, calcular_tir
import numpy as np

def show_wacc_form():
    st.header("💰 Cálculo del Costo de Capital (WACC)")
    st.markdown("Determina la tasa de descuento apropiada para evaluar el proyecto.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🏦 Estructura de Financiamiento")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            patrimonio = st.number_input("Patrimonio / Capital Propio ($)", 
                                        min_value=0.0, value=60000.0, step=1000.0)
            costo_patrimonio = st.number_input("Costo del Patrimonio (%)", 
                                              min_value=0.0, value=15.0, step=0.5,
                                              help="Rentabilidad esperada por los accionistas")
        
        with col_b:
            deuda = st.number_input("Deuda / Financiamiento ($)", 
                                   min_value=0.0, value=40000.0, step=1000.0)
            costo_deuda = st.number_input("Costo de la Deuda (%)", 
                                         min_value=0.0, value=8.0, step=0.5,
                                         help="Tasa de interés de la deuda")
        
        tasa_impuesto = st.number_input("Tasa de Impuesto (%)", 
                                       min_value=0.0, max_value=100.0, value=30.0, step=1.0)
        
        st.markdown("---")
        st.subheader("📊 Tasas de Referencia")
        
        col_c, col_d = st.columns(2)
        
        with col_c:
            tasa_libre_riesgo = st.number_input("Tasa Libre de Riesgo (%)", 
                                               value=5.0, step=0.5,
                                               help="Bonos del tesoro o inversión sin riesgo")
            beta = st.number_input("Beta del Sector", value=1.2, step=0.1,
                                  help="Medida de riesgo sistemático")
        
        with col_d:
            prima_mercado = st.number_input("Prima de Riesgo del Mercado (%)", 
                                           value=8.0, step=0.5)
            prima_pais = st.number_input("Prima de Riesgo País (%)", 
                                        value=2.0, step=0.5)
    
    with col2:
        st.subheader("🎯 Método CAPM")
        st.markdown("""
        **Capital Asset Pricing Model**
        
        ```
        Ke = Rf + β(Rm - Rf) + Rp
        ```
        
        Donde:
        - Ke: Costo del patrimonio
        - Rf: Tasa libre de riesgo
        - β: Beta del sector
        - Rm: Prima de mercado
        - Rp: Riesgo país
        """)
        
        if st.button("🤖 Explicar WACC con IA", use_container_width=True):
            st.info("💬 Explicación detallada disponible en versión completa")
    
    # Cálculos
    wacc = calcular_wacc(patrimonio, deuda, costo_patrimonio, costo_deuda, tasa_impuesto)
    
    # CAPM
    ke_capm = tasa_libre_riesgo + beta * prima_mercado + prima_pais
    
    total_inversion = patrimonio + deuda
    prop_patrimonio = patrimonio / total_inversion if total_inversion > 0 else 0
    prop_deuda = deuda / total_inversion if total_inversion > 0 else 0
    
    escudo_fiscal = deuda * (costo_deuda/100) * (tasa_impuesto/100)
    
    st.markdown("---")
    st.subheader("📊 Resultados del Análisis")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("WACC", f"{wacc:.2f}%", 
                 delta="Tasa de descuento sugerida")
    
    with col2:
        st.metric("Ke (CAPM)", f"{ke_capm:.2f}%",
                 delta=f"vs {costo_patrimonio:.2f}% directo")
    
    with col3:
        st.metric("Escudo Fiscal", f"${escudo_fiscal:,.2f}",
                 delta="Ahorro anual por impuestos")
    
    with col4:
        st.metric("D/E Ratio", f"{(deuda/patrimonio):.2f}" if patrimonio > 0 else "N/A",
                 delta="Apalancamiento")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Estructura de capital
        fig1 = go.Figure(data=[go.Pie(
            labels=['Patrimonio', 'Deuda'],
            values=[patrimonio, deuda],
            hole=0.4,
            marker_colors=['#4CAF50', '#FF9800'],
            text=[f"${patrimonio:,.0f}<br>{prop_patrimonio*100:.1f}%",
                  f"${deuda:,.0f}<br>{prop_deuda*100:.1f}%"],
            textposition='auto'
        )])
        fig1.update_layout(title="Estructura de Capital", height=400)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Componentes del WACC
        costo_patrimonio_ponderado = prop_patrimonio * costo_patrimonio
        costo_deuda_ponderado = prop_deuda * costo_deuda * (1 - tasa_impuesto/100)
        
        fig2 = go.Figure(data=[go.Bar(
            x=['Costo Patrimonio', 'Costo Deuda (después impuestos)', 'WACC'],
            y=[costo_patrimonio_ponderado, costo_deuda_ponderado, wacc],
            marker_color=['#4CAF50', '#FF9800', '#2196F3'],
            text=[f"{costo_patrimonio_ponderado:.2f}%", 
                  f"{costo_deuda_ponderado:.2f}%",
                  f"{wacc:.2f}%"],
            textposition='auto'
        )])
        fig2.update_layout(title="Componentes del WACC (%)", yaxis_title="Tasa (%)", height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Análisis de sensibilidad del WACC
    st.markdown("### 📈 Sensibilidad del WACC")
    
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
    
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=ratios_de, y=waccs, mode='lines+markers',
        line=dict(color='blue', width=3),
        marker=dict(size=8)
    ))
    fig3.add_vline(x=deuda/patrimonio if patrimonio > 0 else 0, 
                   line_dash="dash", line_color="red",
                   annotation_text="Estructura Actual")
    fig3.update_layout(
        title="WACC vs Relación Deuda/Patrimonio",
        xaxis_title="D/E Ratio",
        yaxis_title="WACC (%)",
        height=400
    )
    st.plotly_chart(fig3, use_container_width=True)
    
    # Recomendaciones
    st.markdown("### 📋 Interpretación y Recomendaciones")
    
    if wacc < costo_patrimonio:
        st.success(f"""
        **✅ ESTRUCTURA DE CAPITAL EFICIENTE**
        
        - El WACC ({wacc:.2f}%) es menor que el costo del patrimonio ({costo_patrimonio:.2f}%)
        - El uso de deuda genera un escudo fiscal de ${escudo_fiscal:,.2f} anuales
        - La estructura actual aprovecha el beneficio tributario del financiamiento
        - **Recomendación**: Usar {wacc:.2f}% como tasa de descuento para evaluar el proyecto
        """)
    else:
        st.info(f"""
        **📊 ANÁLISIS DE ESTRUCTURA DE CAPITAL**
        
        - El WACC actual es {wacc:.2f}%
        - Relación D/E: {(deuda/patrimonio):.2f}" if patrimonio > 0 else "N/A
        - Considerar ajustar la estructura de capital para optimizar el WACC
        - Evaluar el equilibrio entre beneficio fiscal y riesgo financiero
        """)
    
    # Comparación con proyecto
    if st.session_state.proyecto_data:
        st.markdown("### 🎯 Comparación con el Proyecto Evaluado")
        
        tasa_proyecto = st.session_state.proyecto_data['tasa_descuento']
        vpn_proyecto = st.session_state.proyecto_data['vpn']
        
        # Recalcular VPN con WACC
        flujos = st.session_state.proyecto_data['flujos']
        vpn_wacc = calcular_vpn(flujos, wacc/100)
        tir = st.session_state.proyecto_data['tir']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("VPN (Tasa Original)", f"${vpn_proyecto:,.2f}",
                     delta=f"Tasa: {tasa_proyecto}%")
        
        with col2:
            st.metric("VPN (con WACC)", f"${vpn_wacc:,.2f}",
                     delta=f"Tasa: {wacc:.2f}%")
        
        with col3:
            diferencia = vpn_wacc - vpn_proyecto
            st.metric("Diferencia", f"${diferencia:,.2f}",
                     delta=f"{(diferencia/abs(vpn_proyecto)*100):.1f}%" if vpn_proyecto != 0 else "N/A")
        
        if tir and tir > wacc:
            st.success(f"""
            ✅ **PROYECTO VIABLE CON WACC**
            
            TIR ({tir:.2f}%) > WACC ({wacc:.2f}%)
            
            El proyecto supera el costo de capital y genera valor para los inversionistas.
            """)
        elif tir:
            st.warning(f"""
            ⚠️ **PROYECTO NO SUPERA EL COSTO DE CAPITAL**
            
            TIR ({tir:.2f}%) < WACC ({wacc:.2f}%)
            
            El proyecto no cubre el costo de oportunidad del capital invertido.
            """)