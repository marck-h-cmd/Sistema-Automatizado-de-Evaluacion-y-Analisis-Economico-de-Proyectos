import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from datetime import datetime
import os

from src.components.ui.header import render_header
from src.components.ui.footer import render_footer
from src.components.forms.eval_basica_form import show_eval_basica_form
from src.components.forms.escenarios_form import show_escenarios_form
from src.components.forms.sensibilidad_form import show_sensibilidad_form
from src.components.forms.wacc_form import show_wacc_form
from src.components.forms.informe_form import show_informe_form
from src.components.styles.style import render_styles
# Configuración de la página
st.set_page_config(
    page_title="Sistema de Evaluación Económica con IA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

render_styles()



# Inicializar estado de sesión
if 'proyecto_data' not in st.session_state:
    st.session_state.proyecto_data = None
if 'analisis_ia' not in st.session_state:
    st.session_state.analisis_ia = {}

render_header()

# Sidebar con información del proyecto
with st.sidebar:
    st.header("⚙️ Configuración del Proyecto")
    nombre_proyecto = st.text_input("Nombre del Proyecto", "Proyecto de Inversión 2025")
    st.markdown("---")
    
    st.subheader("📅 Información General")
    fecha_analisis = st.date_input("Fecha de Análisis", datetime.now())
    analista = st.text_input("Analista", "Usuario")
    email = st.text_input("Email del Analista")
    
    print( "Email desde sidebar:", email)
    
    if 'email' not in st.session_state:
        st.session_state.email = ""
       
    if email:
        st.session_state.email = email

    
    st.markdown("---")
    st.info("💡 **Tip**: Usa el asistente de IA en cada sección para obtener interpretaciones y recomendaciones personalizadas.")

# Tabs principales
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Evaluación Básica", 
    "🎯 Análisis de Escenarios", 
    "⚠️ Sensibilidad y Riesgo", 
    "💰 Costo de Capital (WACC)",
    "📋 Informe Completo"
])

# TAB 1: EVALUACIÓN BÁSICA
with tab1:
    show_eval_basica_form(nombre_proyecto)
# TAB 2: ANÁLISIS DE ESCENARIOS
with tab2:
    show_escenarios_form()
   
# TAB 3: SENSIBILIDAD Y RIESGO
with tab3:
   show_sensibilidad_form()

# TAB 4: COSTO DE CAPITAL (WACC)
with tab4:
    show_wacc_form()

# TAB 5: INFORME COMPLETO
with tab5:
    show_informe_form(fecha_analisis, analista)
   
render_footer()