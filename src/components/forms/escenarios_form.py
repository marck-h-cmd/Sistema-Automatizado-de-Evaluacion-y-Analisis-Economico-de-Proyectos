import streamlit as st
from src.utils.eval_basica import calcular_vpn, calcular_tir, calcular_bc, calcular_periodo_recuperacion
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def show_escenarios_form():
    st.header("🎯 Análisis de Escenarios")
    st.markdown("Evalúa el proyecto bajo diferentes situaciones considerando la incertidumbre del futuro.")
    
    if st.session_state.proyecto_data is None:
        st.warning("⚠️ Primero completa la Evaluación Básica en la pestaña anterior.")
    else:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("📊 Configuración de Escenarios")
            
            # Escenario Pesimista
            with st.expander("📉 Escenario Pesimista", expanded=True):
                prob_pesimista = st.slider("Probabilidad (%)", 0, 100, 20, key="prob_pes")
                factor_pesimista = st.slider("Factor de Reducción", 0.3, 0.9, 0.7, 0.05, key="factor_pes")
                st.info(f"Los flujos se reducen al {factor_pesimista*100:.0f}% del escenario base")
            
            # Escenario Base
            with st.expander("📊 Escenario Base", expanded=True):
                prob_base = st.slider("Probabilidad (%)", 0, 100, 50, key="prob_base")
                st.info("Se utilizan los flujos del escenario base sin modificación")
            
            # Escenario Optimista
            with st.expander("📈 Escenario Optimista", expanded=True):
                prob_optimista = st.slider("Probabilidad (%)", 0, 100, 30, key="prob_opt")
                factor_optimista = st.slider("Factor de Incremento", 1.1, 2.0, 1.3, 0.05, key="factor_opt")
                st.info(f"Los flujos se incrementan al {factor_optimista*100:.0f}% del escenario base")
            
            # Validar probabilidades
            suma_prob = prob_pesimista + prob_base + prob_optimista
            if suma_prob != 100:
                st.error(f"⚠️ La suma de probabilidades debe ser 100%. Actual: {suma_prob}%")
        
        with col2:
            st.subheader("🎲 Probabilidades")
            
            fig_prob = go.Figure(data=[go.Pie(
                labels=['Pesimista', 'Base', 'Optimista'],
                values=[prob_pesimista, prob_base, prob_optimista],
                hole=0.4,
                marker_colors=['#ff6b6b', '#ffd93d', '#6bcf7f']
            )])
            fig_prob.update_layout(height=300)
            st.plotly_chart(fig_prob, use_container_width=True)
            
            if st.button("🤖 Analizar Escenarios con IA", use_container_width=True):
                st.info("💬 Análisis de IA disponible en versión completa")
        
        if suma_prob == 100:
            # Calcular escenarios
            flujos_base = st.session_state.proyecto_data['flujos']
            tasa = st.session_state.proyecto_data['tasa_descuento'] / 100
            
            # Pesimista
            flujos_pes = [flujos_base[0]] + [f * factor_pesimista for f in flujos_base[1:]]
            vpn_pes = calcular_vpn(flujos_pes, tasa)
            tir_pes = calcular_tir(flujos_pes)
            bc_pes = calcular_bc(flujos_pes, tasa)
            
            # Base
            vpn_base = st.session_state.proyecto_data['vpn']
            tir_base = st.session_state.proyecto_data['tir']
            bc_base = st.session_state.proyecto_data['bc']
            
            # Optimista
            flujos_opt = [flujos_base[0]] + [f * factor_optimista for f in flujos_base[1:]]
            vpn_opt = calcular_vpn(flujos_opt, tasa)
            tir_opt = calcular_tir(flujos_opt)
            bc_opt = calcular_bc(flujos_opt, tasa)
            
            # VPN Esperado
            vpn_esperado = (vpn_pes * prob_pesimista + vpn_base * prob_base + vpn_opt * prob_optimista) / 100
            
            # Estadísticas
            vpns = [vpn_pes, vpn_base, vpn_opt]
            probs = [prob_pesimista/100, prob_base/100, prob_optimista/100]
            desv_std = np.sqrt(sum([p * (v - vpn_esperado)**2 for v, p in zip(vpns, probs)]))
            rango = vpn_opt - vpn_pes
            prob_exito = (prob_base + prob_optimista) if vpn_base > 0 else prob_optimista
            
            st.markdown("---")
            st.subheader("📊 Resultados por Escenario")
            
            # Tabla comparativa
            df_escenarios = pd.DataFrame({
                'Escenario': ['Pesimista', 'Base', 'Optimista'],
                'Probabilidad': [f"{prob_pesimista}%", f"{prob_base}%", f"{prob_optimista}%"],
                'VPN': [f"${vpn_pes:,.2f}", f"${vpn_base:,.2f}", f"${vpn_opt:,.2f}"],
                'TIR': [f"{tir_pes:.2f}%" if tir_pes else "N/A", 
                       f"{tir_base:.2f}%" if tir_base else "N/A",
                       f"{tir_opt:.2f}%" if tir_opt else "N/A"],
                'B/C': [f"{bc_pes:.2f}", f"{bc_base:.2f}", f"{bc_opt:.2f}"]
            })
            
            st.dataframe(df_escenarios, use_container_width=True, hide_index=True)
            
            # Métricas del análisis
            st.markdown("### 🎯 Análisis Estadístico")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("VPN Esperado", f"${vpn_esperado:,.2f}",
                         delta="Ponderado por probabilidades")
            
            with col2:
                st.metric("Desviación Estándar", f"${desv_std:,.2f}",
                         delta="Medida de riesgo")
            
            with col3:
                st.metric("Rango", f"${rango:,.2f}",
                         delta=f"${vpn_pes:,.0f} a ${vpn_opt:,.0f}")
            
            with col4:
                st.metric("Probabilidad de Éxito", f"{prob_exito}%",
                         delta="VPN > 0")
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de barras comparativo
                fig1 = go.Figure()
                fig1.add_trace(go.Bar(
                    x=['Pesimista', 'Base', 'Optimista'],
                    y=[vpn_pes, vpn_base, vpn_opt],
                    marker_color=['#ff6b6b', '#ffd93d', '#6bcf7f'],
                    text=[f"${v:,.0f}" for v in [vpn_pes, vpn_base, vpn_opt]],
                    textposition='auto'
                ))
                fig1.add_hline(y=0, line_dash="dash", line_color="red")
                fig1.add_hline(y=vpn_esperado, line_dash="dash", line_color="blue", 
                              annotation_text=f"VPN Esperado: ${vpn_esperado:,.0f}")
                fig1.update_layout(title="VPN por Escenario", yaxis_title="VPN ($)", height=400)
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Distribución de probabilidad
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=[vpn_pes, vpn_base, vpn_opt],
                    y=[prob_pesimista, prob_base, prob_optimista],
                    mode='markers+lines',
                    marker=dict(size=[prob_pesimista*2, prob_base*2, prob_optimista*2],
                               color=['#ff6b6b', '#ffd93d', '#6bcf7f']),
                    line=dict(color='gray', dash='dot')
                ))
                fig2.add_vline(x=vpn_esperado, line_dash="dash", line_color="blue",
                              annotation_text="VPN Esperado")
                fig2.update_layout(title="Distribución de Probabilidad", 
                                  xaxis_title="VPN ($)", yaxis_title="Probabilidad (%)",
                                  height=400)
                st.plotly_chart(fig2, use_container_width=True)
            
            # Interpretación
            st.markdown("### 📋 Interpretación del Análisis")
            
            if vpn_esperado > 0:
                st.success(f"""
                **✅ PROYECTO VIABLE BAJO INCERTIDUMBRE**
                
                - El VPN esperado es positivo: ${vpn_esperado:,.2f}
                - Probabilidad de éxito (VPN > 0): {prob_exito}%
                - El proyecto mantiene valor incluso considerando escenarios adversos
                - Desviación estándar: ${desv_std:,.2f} indica el nivel de riesgo
                """)
            else:
                st.warning(f"""
                **⚠️ PROYECTO CON RIESGO ELEVADO**
                
                - El VPN esperado es: ${vpn_esperado:,.2f}
                - Probabilidad de éxito: {prob_exito}%
                - Se recomienda analizar estrategias de mitigación de riesgo
                - Considerar opciones reales o flexibilidad en la implementación
                """)
