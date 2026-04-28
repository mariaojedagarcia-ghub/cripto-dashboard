"""
Dashboard Cripto con Streamlit
================================
VERSIÓN 3: Con histórico usando st.session_state

Equivalente al Paso 4 del notebook de Dash (dcc.Store + dcc.Interval).

En Dash usábamos:
  - dcc.Store  → para guardar el historial entre callbacks
  - dcc.Interval → para refrescar automáticamente

En Streamlit:
  - st.session_state → 🆕 variable que persiste entre recargas del script
  - time.sleep() + st.rerun() → refresco automático (igual que v2)

st.session_state es un diccionario especial de Streamlit.
A diferencia de las variables normales (que se reinician cada vez que el script
se relanza), session_state MANTIENE su valor entre reruns.

    st.session_state['historial'] = []   # primera vez
    st.session_state['historial'].append(nuevo_punto)  # reruns siguientes

Ejecutar con: streamlit run cripto_v3.py
"""
import streamlit as st
import requests
import plotly.express as px
import pandas as pd
from datetime import datetime
import time

# =============================================
# CONFIGURACIÓN
# =============================================
st.set_page_config(
    page_title="Dashboard Cripto — Con Histórico",
    page_icon="🪙",
    layout="wide",
)

INTERVALO_SEGUNDOS = 120

# =============================================
# API
# =============================================
URL = "https://api.coingecko.com/api/v3/simple/price"
PARAMS = {
    "ids": "bitcoin,ethereum,solana",
    "vs_currencies": "eur",
    "include_24hr_change": "true",
}
MONEDAS = {"bitcoin": "Bitcoin", "ethereum": "Ethereum", "solana": "Solana"}

def obtener_precios():
    try:
        r = requests.get(URL, params=PARAMS, timeout=5)
        r.raise_for_status()
        raw = r.json()
        resultado = {}
        for clave, nombre in MONEDAS.items():
            resultado[nombre] = {
                "precio": raw[clave]["eur"],
                "cambio": raw[clave]["eur_24h_change"],
            }
        resultado["timestamp"] = datetime.now().strftime("%H:%M:%S")
        return resultado
    except Exception as e:
        return None

# =============================================
# 🆕 INICIALIZAR SESSION STATE
# Si es la primera vez que arranca, creamos el historial vacío.
# En reruns posteriores esta línea se salta porque 'historial' ya existe.
# Equivalente a: dcc.Store(id='historial', data=[])
# =============================================
if 'historial' not in st.session_state:
    st.session_state['historial'] = []

# =============================================
# CARGAMOS DATOS Y ACTUALIZAMOS HISTORIAL
# =============================================
precios = obtener_precios()

if precios is None:
    st.error("No se pudo conectar con la API. Reintentando...")
    time.sleep(INTERVALO_SEGUNDOS)
    st.rerun()

# Añadimos el nuevo punto al historial — igual que historial.append() en Dash
nuevo_punto = {
    'tiempo':   precios['timestamp'],
    'Bitcoin':  precios['Bitcoin']['precio'],
    'Ethereum': precios['Ethereum']['precio'],
    'Solana':   precios['Solana']['precio'],
}
st.session_state['historial'].append(nuevo_punto)
historial = st.session_state['historial']

# =============================================
# DASHBOARD
# =============================================
st.title("🪙 Dashboard Cripto — Con Histórico")
st.caption(f"Última actualización: {precios['timestamp']}  |  {len(historial)} registros esta sesión  |  Refresco cada {INTERVALO_SEGUNDOS}s")
st.divider()

# --- KPIs ---
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Bitcoin",  f"{precios['Bitcoin']['precio']:,.0f} €",  f"{precios['Bitcoin']['cambio']:+.2f}% (24h)")
kpi2.metric("Ethereum", f"{precios['Ethereum']['precio']:,.0f} €", f"{precios['Ethereum']['cambio']:+.2f}% (24h)")
kpi3.metric("Solana",   f"{precios['Solana']['precio']:,.0f} €",   f"{precios['Solana']['cambio']:+.2f}% (24h)")

st.divider()

# --- Gráficos ---
col_izq, col_der = st.columns([2, 1])

with col_izq:
    # Gráfico de línea con el histórico
    # Necesitamos al menos 2 puntos para dibujar una línea
    if len(historial) >= 2:
        df = pd.DataFrame(historial)
        fig_linea = px.line(
            df,
            x='tiempo',
            y=['Bitcoin', 'Ethereum', 'Solana'],
            title='Evolución de precio durante la sesión',
            template='plotly_white',
            color_discrete_sequence=['orange', 'royalblue', 'purple'],
            labels={'tiempo': 'Hora', 'value': 'Precio (€)', 'variable': 'Moneda'},
            markers=True,
        )
        fig_linea.update_layout(
            yaxis_title='Precio (€)',
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
        )
        st.plotly_chart(fig_linea, width="stretch")
    else:
        # Primera carga — todavía no hay suficientes puntos para la línea
        st.info("⏳ Esperando más datos para mostrar el histórico...")

with col_der:
    nombres = ['Bitcoin', 'Ethereum', 'Solana']
    fig_barras = px.bar(
        x=nombres,
        y=[precios[m]['precio'] for m in nombres],
        color=nombres,
        color_discrete_sequence=['orange', 'royalblue', 'purple'],
        labels={'x': '', 'y': 'Precio (€)'},
        title='Precio actual',
        template='plotly_white',
        text_auto=',.0f',
    )
    fig_barras.update_layout(showlegend=False)
    st.plotly_chart(fig_barras, width="stretch")

# --- Comparativa ---
st.info("""
**Compara con Dash v4 (Store + Interval):**
- `dcc.Store(data=[])` → `st.session_state['historial'] = []`
- `historial.append(nuevo_punto)` dentro del callback → igual, pero fuera de cualquier función
- `State('historial', 'data')` para leer sin disparar → no existe en Streamlit, session_state se lee directamente
- El historial se pierde al cerrar la pestaña — igual que `dcc.Store` con `storage_type='memory'`
""")

# =============================================
# REFRESCO AUTOMÁTICO — siempre al final
# =============================================
time.sleep(INTERVALO_SEGUNDOS)
st.rerun()
