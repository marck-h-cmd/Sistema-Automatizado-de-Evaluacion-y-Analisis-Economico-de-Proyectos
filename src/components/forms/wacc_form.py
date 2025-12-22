import streamlit as st
from plotly.subplots import make_subplots   
import plotly.graph_objects as go
from src.utils.wacc import (
    calcular_wacc,
    calcular_capm,
    calcular_proporciones_capital,
    calcular_escudo_fiscal,
    crear_grafico_estructura_capital,
    crear_grafico_componentes_wacc,
    calcular_sensibilidad_wacc,
    crear_grafico_sensibilidad_wacc
)
from src.utils.eval_basica import calcular_vpn, calcular_tir
from src.utils.ai import consultar_groq, project_context
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
    
    # Cálculos
    wacc = calcular_wacc(patrimonio, deuda, costo_patrimonio, costo_deuda, tasa_impuesto)
    
    # CAPM
    ke_capm = calcular_capm(tasa_libre_riesgo, beta, prima_mercado, prima_pais)
    
    # Proporciones de capital
    prop_patrimonio, prop_deuda, total_inversion = calcular_proporciones_capital(patrimonio, deuda)
    
    # Escudo fiscal
    escudo_fiscal = calcular_escudo_fiscal(deuda, costo_deuda, tasa_impuesto)
    
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
    
    # Botón de análisis IA
    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 2])
    with col_btn2:
        if st.button("🤖 Explicar WACC con IA", key="ia_wacc", use_container_width=True):
            with st.spinner("Consultando al asistente de IA..."):
                # Crear contexto específico para WACC
                contexto_wacc = f"""
                Análisis del Costo de Capital (WACC):
                
                Estructura de Capital:
                - Patrimonio: ${patrimonio:,.2f} ({prop_patrimonio*100:.1f}%)
                - Deuda: ${deuda:,.2f} ({prop_deuda*100:.1f}%)
                - Total inversión: ${total_inversion:,.2f}
                
                Costos:
                - Costo del Patrimonio: {costo_patrimonio:.2f}%
                - Costo de la Deuda: {costo_deuda:.2f}%
                - Tasa de Impuesto: {tasa_impuesto:.2f}%
                - WACC Calculado: {wacc:.2f}%
                - Ke (CAPM): {ke_capm:.2f}%
                
                Métricas:
                - Escudo Fiscal Anual: ${escudo_fiscal:,.2f}
                - Relación D/E: {f"{(deuda/patrimonio):.2f}" if patrimonio > 0 else 'N/A'}
                
                Pregunta: Explica de manera clara y profesional qué significa este WACC, cómo afecta la estructura de capital al costo de financiamiento, y qué recomendaciones darías sobre la estructura actual. Incluye análisis sobre el beneficio del escudo fiscal.
                """
                respuesta_ia = consultar_groq(contexto_wacc, max_tokens=800)
                st.session_state.respuesta_ia_wacc = respuesta_ia
    
    # Mostrar análisis de IA si existe
    if 'respuesta_ia_wacc' in st.session_state:
        st.markdown("---")
        st.markdown("### 🤖 Explicación Inteligente del WACC")
        st.info(st.session_state.respuesta_ia_wacc)
    
    # Gráficos
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = crear_grafico_estructura_capital(patrimonio, deuda, prop_patrimonio, prop_deuda)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        costo_patrimonio_ponderado = prop_patrimonio * costo_patrimonio
        costo_deuda_ponderado = prop_deuda * costo_deuda * (1 - tasa_impuesto/100)
        
        fig2 = crear_grafico_componentes_wacc(costo_patrimonio_ponderado, costo_deuda_ponderado, wacc)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Análisis de sensibilidad del WACC
    st.markdown("### 📈 Sensibilidad del WACC")
    
    ratios_de, waccs = calcular_sensibilidad_wacc(total_inversion, costo_patrimonio, costo_deuda, tasa_impuesto)
    ratio_actual = deuda / patrimonio if patrimonio > 0 else 0
    
    fig3 = crear_grafico_sensibilidad_wacc(ratios_de, waccs, ratio_actual)
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