import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Escala de Apresentações", layout="wide")

# Credenciais
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

def gerar_escala(nomes):
    data_inicio = datetime(2026, 1, 1)
    data_fim = datetime(2026, 12, 31)
    dias = pd.date_range(data_inicio, data_fim, freq='B')
    escala = []
    idx_nome = 0
    for dia in dias:
        semana = dia.isocalendar()[1]
        if semana < 13: continue
        dia_semana = dia.weekday()
        reunioes = ["Flash Manhã", "Flash Tarde"] if dia_semana in [0, 2, 4] else \
                   ["Flash Manhã", "DOR" if dia_semana == 1 else "Flash Tarde"]
        for r in reunioes:
            apresentadores = []
            while len(apresentadores) < 2:
                nome_atual = nomes[idx_nome % len(nomes)]
                if r == "DOR" and nome_atual in ["Dani", "Rafael"]:
                    idx_nome += 1
                    continue
                apresentadores.append(nome_atual)
                idx_nome += 1
            escala.append({
                "Semana": semana,
                "Data": dia.strftime("%d/%m/%Y"),
                "Dia": ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][dia_semana],
                "Reunião": r,
                "Apresentadores": f"{apresentadores[0]} & {apresentadores[1]}"
            })
    return pd.DataFrame(escala)

if check_login():
    nomes_base = ["Debora", "Dani", "Abigail", "Luca", "Bruno", "Thiago", "Anna", "Bianca S.", "Amanda", "Julia", "Bruna", "Renan", "Livia", "Rafael", "Ariel", "Enrique", "Gisele", "Sonia", "Jazmin", "Florencia", "Jesus", "Bianca M.", "Soledad", "Mijal", "Honorato"]
    df = gerar_escala(nomes_base)
    semana_atual_num = datetime.now().isocalendar()[1]
    
    st.title("🚀 MMD | Dashboard de Apresentações")
    st.markdown("---")
    st.subheader(f"📌 Destaque: Semana {semana_atual_num}")
    
    df_hoje = df[df["Semana"] == semana_atual_num]
    if not df_hoje.empty:
        cols = st.columns(len(df_hoje))
        for i, (index, row) in enumerate(df_hoje.iterrows()):
            with cols[i]:
                st.info(f"**{row['Dia']}**\n\n{row['Reunião']}\n\n🏆 {row['Apresentadores']}")
    
    st.markdown("---")
    st.subheader("🗓️ Cronograma Completo")
    semana_busca = st.slider("Selecione a Semana:", 13, 53, int(semana_atual_num))
    df_final = df[df["Semana"] == semana_busca]
    st.table(df_final)
