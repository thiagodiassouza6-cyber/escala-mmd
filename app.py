import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Escala de Apresentações", layout="wide")

SHEET_ID = "1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

USER_ACCESS = "MMD-Board"
PASS_ACCESS = "@MMD123#"

# --- LISTA DE BACKUPS ATUALIZADA ---
MAPA_BACKUPS = {
    "Abigail": "Dani", "Amanda": "Mijal", "Anna": "Soledad", 
    "Ariel": "Rafael", "Bianca M.": "Ariel", "Bianca S.": "Amanda", 
    "Bruna": "Anna Laura", "Bruno": "Bianca M.", "Enrique": "Jazmin", 
    "Dani": "Sonia", "Debora": "Bruna", "Diana": "Julia", 
    "Faiha": "Bianca S.", "Florencia": "Diana", "Gisele": "Thiago", 
    "Honorato": "Bruno", "Jazmin": "Abigail", "Jesus": "Luca", 
    "Julia": "Honorato", "Livia": "Faiha", "Luca": "Enrique", 
    "Mijal": "Livia", "Rafael": "Florencia", "Renan": "Debora", 
    "Sonia": "Jesus", "Soledad": "Gisele", "Thiago": "Renan"
}

def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown("<h2 style='text-align: center;'>Portal de Escalas MMD</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            user = st.text_input("Usuário").strip()
            password = st.text_input("Senha", type="password").strip()
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
        hora_start = "09:45:00" if "Manhã" in reuniao else "15:00:00"
        hora_end = "10:15:00" if "Manhã" in reuniao else "15:30:00"
        assunto = urllib.parse.quote(f"🔔 Apresentação MMD: {reuniao}")
        corpo = urllib.parse.quote(f"Apresentador: {apresentador}")
        return f"https://outlook.office.com/calendar/0/deeplink/compose?subject={assunto}&body={corpo}&startdt={data_iso}T{hora_start}&enddt={data_iso}T{hora_end}"
    except:
        return "#"

@st.cache_data(ttl=60)
def carregar_nomes():
    try:
        df_sheets = pd.read_csv(SHEET_URL)
        return sorted(df_sheets['Funcionario'].dropna().unique().tolist())
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return []

def gerar_escala_final(nomes):
    ano_atual = datetime.now().year
    data_inicio = datetime(ano_atual, 1, 1)
    data_fim = datetime(ano_atual, 12, 31)
    dias = pd.date_range(data_inicio, data_fim, freq='B')
    
    fila_flash = nomes.copy()
    fila_dor = [n for n in nomes if n not in ["Dani", "Rafael"]]
    
    idx_f = 0
    idx_d = 0
    escala = []

    for dia in dias:
        dia_semana = dia.weekday() 
        data_s = dia.strftime("%d/%m/%Y")
        sem = dia.isocalendar()[1]
        dia_nome = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][dia_semana]

        ap_m = fila_flash[idx_f % len(fila_flash)]
        escala.append({
            "Semana": sem, "Data": data_s, "Dia": dia_nome,
            "Reunião": "Flash Manhã", "Apresentador": ap_m,
            "Backup": MAPA_BACKUPS.get(ap_m, "N/A"),
            "Link": criar_link_outlook(data_s, "Flash Manhã", ap_m)
        })
        idx_f += 1

        if dia_semana in [1, 3]: 
            ap_d = fila_dor[idx_d % len(fila_dor)]
            if ap_d == ap_m:
                idx_d += 1
                ap_d = fila_dor[idx_d % len(fila_dor)]
            escala.append({
                "Semana": sem, "Data": data_s, "Dia": dia_nome,
                "Reunião": "DOR", "Apresentador": ap_d,
                "Backup": MAPA_BACKUPS.get(ap_d, "N/A"),
                "Link": criar_link_outlook(data_s, "DOR", ap_d)
            })
            idx_d
