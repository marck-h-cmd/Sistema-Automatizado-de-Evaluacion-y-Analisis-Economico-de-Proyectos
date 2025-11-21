import streamlit as st

def render_footer():
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p><strong>Sistema de Evaluación Económica de Proyectos con IA</strong></p>
        <p> © 2025</p>
        <p style="font-size: 0.9rem;">
            📧 Soporte: soporte@evaluacionproyectos.com | 
            📚 Documentación: docs.evaluacionproyectos.com
        </p>
    </div>
    """, unsafe_allow_html=True)