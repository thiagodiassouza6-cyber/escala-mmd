import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Escala de Apresentações", layout="wide")

# Link da Planilha
SHEET_ID = "1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# Credenciais
USER_ACCESS = "MMD-Board"
PASS_ACCESS = "@MMD123#"

# --- MAPEAMENTO DE BACKUPS ATUALIZADO ---
# Baseado na lista final enviada
MAPA_BACKUPS = {
    "Amanda": "Mijal", "Anna Laura": "Soledad", "Ariel": "Rafael",
    "Bianca M.": "Ariel", "Bianca S.": "Amanda", "Bruna": "Anna Laura",
    "Bruno": "Bianca M.", "Enrique": "Jazmin", "Debora": "Bruna",
    "Diana": "Julia", "Faiha": "Bianca S.", "Florencia": "Diana",
    "Gisele": "Thiago", "Honorato": "Bruno", "Jazmin": "Sonia",
    "Jesus": "Luca", "Julia": "Honorato", "Livia": "Faiha",
    "Luca": "Enrique", "Mijal": "Livia", "Rafael": "Florencia",
    "Renan": "Debora", "Sonia": "Jesus", "Soledad": "Gisele",
    "Thiago": "Renan"
}

def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown("<h2 style='text-align: center;'>Portal de Escalas MMD</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            user = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            if st.button("Acessar Painel", use_container_width=True):
                if user == USER_ACCESS and password == PASS_ACCESS:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
        return False
    return True

def criar_link_outlook(data_str, reuniao, apresentador):
    try:
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        data_iso = data_obj.strftime("%Y-%m-%d")
        hora_start = "09:45:00
