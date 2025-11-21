
import requests
import streamlit as st


# Función para llamar a la IA (sin await / fetch JS)
def consultar_ia(prompt):
    """Consulta al modelo de IA (requiere ANTHROPIC_API_KEY en variables de entorno).
    Devuelve un mensaje informativo si la key no está configurada o en caso de error."""
    api_key = st.secrets["API_KEY"]
    if not api_key:
        return ("IA no disponible: configure la variable de entorno ANTHROPIC_API_KEY "
                "para habilitar consultas reales. Actualmente se usan respuestas simuladas.")

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        # Manejar distintas formas de respuesta de forma segura
        if isinstance(data, dict):
            if 'content' in data and isinstance(data['content'], list) and len(data['content']) > 0:
                return data['content'][0].get('text', str(data))
            if 'completion' in data:
                return data['completion']
            if 'message' in data:
                return data['message']
        return str(data)
    except Exception as e:
        return f"Error al consultar IA: {e}"