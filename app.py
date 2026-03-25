import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Escala de Apresentações", layout="wide")

# Link da Planilha (ID extraído do seu link original)
SHEET_ID = "1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# Credenciais de Acesso
USER_ACCESS = "MMD-Board"
PASS_ACCESS = "@MMD123#"

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

def criar_link_google(data_str, reuniao, apresentador):
    try:
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        hora = "094500" if "Manhã" in reuniao else "150000"
        data_formatada = data_obj.strftime("%Y%m%d")
        inicio = f"{data_formatada}T{hora}"
        fim_obj = datetime.strptime(inicio, "%Y%m%dT%H%M%S") + timedelta(minutes=30)
        fim = fim_obj.strftime("%Y%m%dT%H%M%S")
        titulo = urllib.parse.quote(f"🔔 Apresentação MMD: {reuniao}")
        detalhes = urllib.parse.quote(f"Apresentador: {apresentador}")
        return f"https://www.google.com/calendar/render?action=TEMPLATE&text={titulo}&dates={inicio}/{fim}&details={detalhes}"
    except:
        return "#"

def criar_link_outlook(data_str, reuniao, apresentador):
    try:
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        data_iso = data_obj.strftime("%Y-%m-%d")
        hora_start = "09:45:00" if "Manhã" in reuniao else "15:00:00"
        hora_end = "10:15:00" if "Manhã" in reuniao else "15:30:00"
        assunto = urllib.parse.quote(f"🔔 Apresentação MMD: {reuniao}")
        corpo = urllib.parse.quote(f"Apresentador: {ap
