import streamlit as st
from src.utils.eval_basica import calcular_vpn, calcular_tir, calcular_bc, calcular_periodo_recuperacion
from src.utils.ai import consultar_groq
from src.utils.escenarios import (
    calcular_escenarios, calcular_estadisticas_escenarios, crear_tabla_escenarios,
    crear_grafico_vpn, crear_grafico_tir, crear_grafico_bc,
    crear_grafico_distribucion, crear_grafico_probabilidades
)
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
                prob_pesimista = st.slider(
                    "Probabilidad (%)",
                    0.0,
                    100.0,
                    value=float(st.session_state.get('prob_pes', 20.0)),
                    step=0.1,
                    key="prob_pes"
                )
                factor_pesimista = st.slider("Factor de Reducción", 0.3, 0.9, 0.7, 0.05, key="factor_pes")
                st.info(f"Los flujos se reducen al {factor_pesimista*100:.0f}% del escenario base")
            
            # Escenario Base
            with st.expander("📊 Escenario Base", expanded=True):
                prob_base = st.slider(
                    "Probabilidad (%)",
                    0.0,
                    100.0,
                    value=float(st.session_state.get('prob_base', 50.0)),
                    step=0.1,
                    key="prob_base"
                )
                st.info("Se utilizan los flujos del escenario base sin modificación")
            
            # Escenario Optimista
            with st.expander("📈 Escenario Optimista", expanded=True):
                prob_optimista = st.slider(
                    "Probabilidad (%)",
                    0.0,
                    100.0,
                    value=float(st.session_state.get('prob_opt', 30.0)),
                    step=0.1,
                    key="prob_opt"
                )
                factor_optimista = st.slider("Factor de Incremento", 1.1, 2.0, 1.3, 0.05, key="factor_opt")
                st.info(f"Los flujos se incrementan al {factor_optimista*100:.0f}% del escenario base")
            
            # Validar probabilidades
            suma_prob = prob_pesimista + prob_base + prob_optimista
            if abs(suma_prob - 100.0) > 0.05:
                st.error(f"⚠️ La suma de probabilidades debe ser 100%. Actual: {suma_prob}%")
        
        with col2:
            st.subheader("🎲 Probabilidades")
            
            fig_prob = crear_grafico_probabilidades(prob_pesimista, prob_base, prob_optimista)
            st.plotly_chart(fig_prob, use_container_width=True)
            
            # Preparar petición IA: marcador para procesar después de calcular resultados
            def _request_ia():
                st.session_state['ask_ia_escenarios'] = True

            st.button("🤖 Analizar Escenarios con IA", use_container_width=True, key="btn_ia", on_click=_request_ia)

            # Callback seguro para normalizar probabilidades (actualiza session_state antes de recrear widgets)
            def _normalize_callback():
                suma = st.session_state.get('prob_pes', 0) + st.session_state.get('prob_base', 0) + st.session_state.get('prob_opt', 0)
                if suma > 0:
                    npes = round(st.session_state.get('prob_pes', 0) / suma * 100.0, 1)
                    nbase = round(st.session_state.get('prob_base', 0) / suma * 100.0, 1)
                    nopt = round(st.session_state.get('prob_opt', 0) / suma * 100.0, 1)
                    diff = round(100.0 - (npes + nbase + nopt), 1)
                    vals = [st.session_state.get('prob_pes', 0), st.session_state.get('prob_base', 0), st.session_state.get('prob_opt', 0)]
                    max_idx = int(np.argmax(vals))
                    if max_idx == 0:
                        npes += diff
                    elif max_idx == 1:
                        nbase += diff
                    else:
                        nopt += diff

                    st.session_state['prob_pes'] = float(npes)
                    st.session_state['prob_base'] = float(nbase)
                    st.session_state['prob_opt'] = float(nopt)
                    st.session_state['normalizado_msg'] = f"Probabilidades normalizadas: Pes {npes}%, Base {nbase}%, Opt {nopt}%"
                else:
                    st.session_state['normalizado_msg'] = "No se puede normalizar: la suma de probabilidades es 0."

            # Botón que usa callback
            st.button("🔄 Normalizar Probabilidades", use_container_width=True, key="btn_normalizar", on_click=_normalize_callback)

            # Mostrar mensaje resultante (si existe)
            if 'normalizado_msg' in st.session_state:
                msg = st.session_state.pop('normalizado_msg')
                if msg.startswith('Probabilidades normalizadas'):
                    st.success(msg)
                else:
                    st.warning(msg)
        
        if suma_prob == 100:
            # Calcular escenarios
            flujos_base = st.session_state.proyecto_data['flujos']
            tasa = st.session_state.proyecto_data['tasa_descuento'] / 100
            
            # Usar función para calcular escenarios
            escenarios = calcular_escenarios(flujos_base, factor_pesimista, factor_optimista, tasa)
            vpn_pes = escenarios['pesimista']['vpn']
            tir_pes = escenarios['pesimista']['tir']
            bc_pes = escenarios['pesimista']['bc']
            
            vpn_base = escenarios['base']['vpn']
            tir_base = escenarios['base']['tir']
            bc_base = escenarios['base']['bc']
            
            vpn_opt = escenarios['optimista']['vpn']
            tir_opt = escenarios['optimista']['tir']
            bc_opt = escenarios['optimista']['bc']
            
            # Calcular estadísticas
            stats = calcular_estadisticas_escenarios(vpn_pes, vpn_base, vpn_opt,
                                                      prob_pesimista, prob_base, prob_optimista)
            vpn_esperado = stats['vpn_esperado']
            desv_std = stats['desv_std']
            rango = stats['rango']
            prob_exito = stats['prob_exito']
            coef_var = stats['coef_var']
            
            st.markdown("---")
            st.subheader("📊 Resultados por Escenario")
            
            # Tabla comparativa
            df_escenarios = crear_tabla_escenarios(prob_pesimista, prob_base, prob_optimista,
                                                   vpn_pes, vpn_base, vpn_opt,
                                                   tir_pes, tir_base, tir_opt,
                                                   bc_pes, bc_base, bc_opt)
            
            st.dataframe(df_escenarios, use_container_width=True, hide_index=True)
            
            # Gráficos comparativos individuales
            st.markdown("---")
            st.markdown("### 📊 Gráficos Comparativos por Indicador")
            
            # Tres gráficos lado a lado
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 💰 VPN por Escenario")
                fig_vpn = crear_grafico_vpn(vpn_pes, vpn_base, vpn_opt)
                st.plotly_chart(fig_vpn, use_container_width=True, key="vpn_chart")
                
                # Interpretación de VPN debajo del gráfico (desplegable)
                with st.expander("📝 Ver Interpretación"):
                    if vpn_pes < 0 and vpn_base < 0 and vpn_opt < 0:
                        st.error("⛔ **Alto Riesgo**: El VPN es negativo en todos los escenarios. El proyecto destruye valor en cualquier situación. **Recomendación: Rechazar el proyecto.**")
                    elif vpn_pes < 0 and vpn_base < 0 and vpn_opt > 0:
                        st.warning("⚠️ **Riesgo Muy Alto**: Solo el escenario optimista genera valor. El proyecto es extremadamente riesgoso. **Recomendación: Revisar o buscar alternativas.**")
                    elif vpn_pes < 0 and vpn_base > 0:
                        st.info("📊 **Riesgo Moderado**: El proyecto es viable en condiciones normales y optimistas, pero vulnerable ante escenarios adversos. **Recomendación: Implementar estrategias de mitigación de riesgos.**")
                    elif vpn_pes > 0:
                        st.success("✅ **Bajo Riesgo**: El VPN es positivo incluso en el escenario pesimista. El proyecto es robusto y genera valor en todas las condiciones. **Recomendación: Proceder con el proyecto.**")
            
            with col2:
                st.markdown("#### 📈 TIR por Escenario")
                wacc = st.session_state.proyecto_data.get('tasa_descuento')
                fig_tir = crear_grafico_tir(tir_pes, tir_base, tir_opt, wacc)
                st.plotly_chart(fig_tir, use_container_width=True, key="tir_chart")
                
                # Interpretación de TIR debajo del gráfico (desplegable)
                with st.expander("📝 Ver Interpretación"):
                    wacc = st.session_state.proyecto_data.get('tasa_descuento', 0)
                    if tir_pes and tir_base and tir_opt:
                        if tir_pes > wacc and tir_base > wacc and tir_opt > wacc:
                            st.success(f"✅ **Rentabilidad Alta**: La TIR supera el WACC ({wacc}%) en todos los escenarios, indicando que el proyecto genera retornos superiores al costo del capital.")
                        elif tir_base > wacc and tir_opt > wacc:
                            st.info(f"📊 **Rentabilidad Moderada**: La TIR supera el WACC ({wacc}%) en escenarios base y optimista. En el pesimista, la rentabilidad es marginal.")
                        else:
                            st.warning(f"⚠️ **Rentabilidad Baja**: La TIR está por debajo del WACC ({wacc}%) en algunos escenarios. El proyecto no genera suficiente retorno en condiciones adversas.")
            
            with col3:
                st.markdown("#### ⚖️ B/C por Escenario")
                fig_bc = crear_grafico_bc(bc_pes, bc_base, bc_opt)
                st.plotly_chart(fig_bc, use_container_width=True, key="bc_chart")
                
                # Interpretación de B/C debajo del gráfico (desplegable)
                with st.expander("📝 Ver Interpretación"):
                    if bc_pes > 1 and bc_base > 1 and bc_opt > 1:
                        st.success("✅ **Beneficios Superan Costos**: La relación B/C es mayor a 1 en todos los escenarios. Por cada dólar invertido, se recupera más de un dólar.")
                    elif bc_base > 1 and bc_opt > 1:
                        st.info("📊 **Balance Positivo**: El proyecto genera beneficios superiores a los costos en condiciones normales y optimistas.")
                    else:
                        st.warning("⚠️ **Balance Ajustado**: La relación B/C indica que en algunos escenarios los beneficios no superan significativamente los costos.")
            
            st.markdown("---")

            # Si el usuario solicitó análisis por IA, mostrar aquí (debajo de la tabla)
            if st.session_state.get('ask_ia_escenarios'):
                with st.spinner("🤖 Generando análisis profundo con IA (Groq)... Esto puede tomar unos momentos..."):
                    # Construir un prompt muy detallado y completo para análisis profundo
                    prompt = (
                        "Eres un analista financiero senior especializado en evaluación de proyectos de inversión y gestión de riesgos. "
                        "Tu tarea es proporcionar un análisis ejecutivo COMPLETO y PROFUNDO del siguiente análisis de escenarios.\n\n"

                        "═══════════════════════════════════════════════════════════════\n"
                        "📊 DATOS DEL PROYECTO - ANÁLISIS DE ESCENARIOS\n"
                        "═══════════════════════════════════════════════════════════════\n\n"

                        f"**MÉTRICAS PRINCIPALES:**\n"
                        f"• VPN Esperado (ponderado): ${vpn_esperado:,.2f}\n"
                        f"• Tasa de Descuento: {st.session_state.proyecto_data['tasa_descuento']}%\n"
                        f"• Inversión Inicial: ${abs(flujos_base[0]):,.2f}\n"
                        f"• Horizonte del Proyecto: {len(flujos_base)-1} períodos\n\n"

                        f"**ESCENARIO PESIMISTA (Probabilidad: {prob_pesimista}%):**\n"
                        f"• VPN: ${vpn_pes:,.2f}\n"
                        f"• TIR: {tir_pes:.2f}%\n"
                        f"• Relación Beneficio/Costo: {bc_pes:.2f}\n"
                        f"• Factor de reducción aplicado: {factor_pesimista*100:.0f}% de los flujos base\n\n"

                        f"**ESCENARIO BASE (Probabilidad: {prob_base}%):**\n"
                        f"• VPN: ${vpn_base:,.2f}\n"
                        f"• TIR: {tir_base:.2f}%\n"
                        f"• Relación Beneficio/Costo: {bc_base:.2f}\n"
                        f"• Flujos sin modificación (escenario más probable)\n\n"

                        f"**ESCENARIO OPTIMISTA (Probabilidad: {prob_optimista}%):**\n"
                        f"• VPN: ${vpn_opt:,.2f}\n"
                        f"• TIR: {tir_opt:.2f}%\n"
                        f"• Relación Beneficio/Costo: {bc_opt:.2f}\n"
                        f"• Factor de incremento aplicado: {factor_optimista*100:.0f}% de los flujos base\n\n"

                        f"**ANÁLISIS DE RIESGO:**\n"
                        f"• Desviación Estándar del VPN: ${desv_std:,.2f}\n"
                        f"• Coeficiente de Variación: {(desv_std/abs(vpn_esperado)*100):.2f}%\n"
                        f"• Rango Total de VPN: ${rango:,.2f}\n"
                        f"• Spread: desde ${vpn_pes:,.2f} hasta ${vpn_opt:,.2f}\n"
                        f"• Probabilidad de Éxito (VPN > 0): {prob_exito}%\n"
                        f"• Probabilidad de Fracaso (VPN < 0): {100-prob_exito}%\n\n"

                        "═══════════════════════════════════════════════════════════════\n"
                        "📝 ANÁLISIS REQUERIDO (RESPONDE DE FORMA EXHAUSTIVA)\n"
                        "═══════════════════════════════════════════════════════════════\n\n"

                        "**1. DIAGNÓSTICO GENERAL DEL PROYECTO:**\n"
                        "   - Evalúa la viabilidad financiera del proyecto considerando todos los escenarios\n"
                        "   - ¿Es un proyecto atractivo desde el punto de vista de riesgo-retorno?\n"
                        "   - Compara el VPN esperado con la inversión inicial\n\n"

                        "**2. ANÁLISIS DETALLADO DE CADA ESCENARIO:**\n"
                        "   - Interpreta qué significa cada escenario y su probabilidad asignada\n"
                        "   - Analiza las diferencias entre escenarios (magnitud de variación)\n"
                        "   - ¿Qué escenario tiene más peso en la decisión y por qué?\n"
                        "   - Evalúa si la distribución de probabilidades es equilibrada o sesgada\n\n"

                        "**3. EVALUACIÓN PROFUNDA DEL RIESGO:**\n"
                        "   - Interpreta la desviación estándar y el coeficiente de variación\n"
                        "   - ¿El proyecto es de alto, medio o bajo riesgo?\n"
                        "   - Analiza el rango de VPN y qué implica para la toma de decisiones\n"
                        "   - Evalúa la probabilidad de éxito: ¿es suficientemente alta?\n"
                        "   - ¿Existe exposición significativa a pérdidas?\n\n"

                        "**4. ANÁLISIS DE SENSIBILIDAD:**\n"
                        "   - ¿Qué tan sensible es el VPN a cambios en los flujos?\n"
                        "   - ¿El proyecto es robusto ante cambios adversos?\n"
                        "   - Identifica variables críticas que podrían afectar los resultados\n\n"

                        "**5. RECOMENDACIONES ESTRATÉGICAS CONCRETAS:**\n"
                        "   - ¿Deberías APROBAR, RECHAZAR o REVISAR el proyecto? (da una recomendación clara)\n"
                        "   - ¿Qué condiciones o ajustes mejorarían la viabilidad?\n"
                        "   - ¿Se necesitan garantías, cobertura de riesgos o planes de contingencia?\n"
                        "   - ¿Hay aspectos del proyecto que deberían renegociarse?\n\n"

                        "**6. IDENTIFICACIÓN DE RIESGOS PRINCIPALES:**\n"
                        "   - Lista los 3-5 riesgos más críticos que podrían llevar al escenario pesimista\n"
                        "   - ¿Qué eventos o factores externos podrían impactar negativamente?\n"
                        "   - ¿Hay riesgos de mercado, operacionales, financieros o regulatorios?\n\n"

                        "**7. OPORTUNIDADES Y UPSIDE POTENTIAL:**\n"
                        "   - ¿Qué factores podrían llevar al escenario optimista?\n"
                        "   - ¿Existen oportunidades de mejora o potencial no aprovechado?\n"
                        "   - ¿Cómo se podría maximizar el valor del proyecto?\n\n"

                        "**8. ESTRATEGIAS DE MITIGACIÓN:**\n"
                        "   - Propone 3-5 estrategias concretas para reducir riesgos\n"
                        "   - ¿Se podría implementar el proyecto en fases?\n"
                        "   - ¿Hay opciones de flexibilidad operativa o real options?\n\n"

                        "**9. COMPARACIÓN CON CRITERIOS DE ACEPTACIÓN:**\n"
                        "   - Evalúa si el proyecto cumple con estándares típicos de la industria\n"
                        "   - ¿La TIR supera la tasa de descuento en todos los escenarios?\n"
                        "   - ¿La relación B/C es aceptable?\n\n"

                        "**10. CONCLUSIÓN Y SIGUIENTE PASO:**\n"
                        "   - Resume tu posición sobre el proyecto en 2-3 oraciones\n"
                        "   - ¿Cuál debe ser el siguiente paso inmediato?\n"
                        "   - ¿Se requiere información adicional o análisis complementarios?\n\n"

                        "═══════════════════════════════════════════════════════════════\n"
                        "⚠️ IMPORTANTE: Proporciona un análisis extenso, profesional y accionable.\n"
                        "Usa formato markdown con títulos (##), subtítulos (###), bullets (-) y negritas (**) para facilitar la lectura.\n"
                        "NO uses cursivas (*texto*) ni texto en itálicas porque causa problemas de formato.\n"
                        "Usa saltos de línea dobles entre secciones para mejor legibilidad.\n"
                        "Tu respuesta debe ser de aproximadamente 25-35 líneas de análisis profundo.\n"
                        "Sé específico con los números y proporciona insights valiosos para la toma de decisiones.\n"
                        "═══════════════════════════════════════════════════════════════"
                    )
                    resp = consultar_groq(prompt, max_tokens=2500)
                    st.session_state['analisis_ia_principal'] = resp
                    st.session_state.pop('ask_ia_escenarios', None)

                with st.expander("🤖 Análisis Ejecutivo Completo - Generado por IA", expanded=True):
                    st.info(resp)

            # Métricas del análisis
            st.markdown("---")
            st.markdown("### 🎯 Análisis Estadístico")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("VPN Esperado", f"${vpn_esperado:,.2f}",
                         delta="Ponderado por probabilidades")
            
            with col2:
                st.metric("Desviación Estándar", f"${desv_std:,.2f}",
                         delta="Medida de riesgo")
            
            with col3:
                coef_var = (desv_std / abs(vpn_esperado) * 100) if vpn_esperado != 0 else 0
                st.metric("Coeficiente de Variación", f"{coef_var:.2f}%",
                         delta="Riesgo relativo")
            
            with col4:
                st.metric("Probabilidad de Éxito", f"{prob_exito}%",
                         delta="VPN > 0")
            
            # Distribución de probabilidad con interpretación al lado
            st.markdown("---")
            col_grafico, col_interpretacion = st.columns([1.5, 1])
            
            with col_grafico:
                st.markdown("#### 📊 Distribución de Probabilidades")
                fig_dist = crear_grafico_distribucion(vpn_pes, vpn_base, vpn_opt,
                                                      prob_pesimista, prob_base, prob_optimista,
                                                      vpn_esperado)
                st.plotly_chart(fig_dist, use_container_width=True, key="dist_chart")
            
            with col_interpretacion:
                st.markdown("#### 🤖 Interpretación con IA")
                # Análisis de IA para distribución
                if st.session_state.get('ask_ia_escenarios'):
                    with st.spinner("Analizando distribución..."):
                        prompt_distribucion = (
                            f"Analiza brevemente esta distribución de probabilidades:\n\n"
                            f"• Pesimista: VPN ${vpn_pes:,.0f} con {prob_pesimista}% de probabilidad\n"
                            f"• Base: VPN ${vpn_base:,.0f} con {prob_base}% de probabilidad\n"
                            f"• Optimista: VPN ${vpn_opt:,.0f} con {prob_optimista}% de probabilidad\n"
                            f"• VPN Esperado: ${vpn_esperado:,.0f}\n"
                            f"• Desviación Estándar: ${desv_std:,.0f}\n\n"
                            "Responde en 5-6 líneas máximo:\n"
                            "1. ¿Qué patrón muestra la distribución?\n"
                            "2. ¿Dónde está concentrada la probabilidad?\n"
                            "3. ¿Nivel de riesgo del proyecto?\n"
                            "4. ¿Recomendación breve?\n\n"
                            "NO uses cursivas. Usa negritas (**) para resaltar conceptos clave."
                        )
                        analisis_dist = consultar_groq(prompt_distribucion, max_tokens=400)
                        st.info(analisis_dist)
                else:
                    st.info(f"""
                    **Análisis de Distribución:**
                    
                    • **Escenario más probable**: Base ({prob_base}%)
                    • **Dispersión**: {'Alta' if desv_std > abs(vpn_esperado) * 0.5 else 'Moderada' if desv_std > abs(vpn_esperado) * 0.2 else 'Baja'}
                    • **Riesgo**: {'Alto' if coef_var > 60 else 'Moderado' if coef_var > 30 else 'Bajo'} (CV: {coef_var:.1f}%)
                    • **VPN Esperado**: ${vpn_esperado:,.0f}
                    
                    💡 Click en "Analizar con IA" arriba para análisis detallado.
                    """)
            
            # Interpretación general
            st.markdown("---")
            st.markdown("### 📋 Conclusión del Análisis")
            
            if vpn_esperado > 0:
                st.success(f"""
                **✅ PROYECTO VIABLE BAJO INCERTIDUMBRE**
                
                - El VPN esperado es positivo: ${vpn_esperado:,.2f}
                - Probabilidad de éxito (VPN > 0): {prob_exito}%
                - El proyecto mantiene valor incluso considerando escenarios adversos
                - Coeficiente de Variación: {coef_var:.2f}% ({'Riesgo bajo' if coef_var < 30 else 'Riesgo moderado' if coef_var < 60 else 'Riesgo alto'})
                """)
            else:
                st.warning(f"""
                **⚠️ PROYECTO CON RIESGO ELEVADO**
                
                - El VPN esperado es: ${vpn_esperado:,.2f}
                - Probabilidad de éxito: {prob_exito}%
                - Se recomienda analizar estrategias de mitigación de riesgo
                - Considerar opciones reales o flexibilidad en la implementación
                """)
