import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Escala de Apresentações", layout="wide")

# CONFIGURAÇÃO DO GOOGLE SHEETS
# (Mantenho o seu ID para não quebrar a conexão)
SHEET_ID = "1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

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

@st.cache_data(ttl=600)
def carregar_nomes():
    try:
        # Lê a planilha e busca a coluna 'Funcionário'
        df_sheets = pd.read_csv(SHEET_URL)
        return df_sheets['Funcionário'].dropna().tolist()
    except Exception as e:
        st.error("Erro ao ler a planilha. Verifique se o nome da coluna é 'Funcionário'.")
        return []

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
        
        # DEFINIÇÃO DAS REUNIÕES DO DIA (Lógica Corrigida)
        if dia_semana in [1, 3]: # Terça (1) e Quinta (3)
            # Apenas 2 reuniões: Manhã e DOR
            reunioes = ["Flash Manhã", "DOR"]
        else: # Segunda (0), Quarta (2) e Sexta (4)
            # Apenas 2 reuniões: Manhã e Tarde
            reunioes = ["Flash Manhã", "Flash Tarde"]
            
        for r in reunioes:
            while True:
                nome_atual = nomes[idx_nome % len(nomes)]
                # Regra DOR: Dani e Rafael não apresentam
                if r == "DOR" and nome_atual in ["Dani", "Rafael"]:
                    idx_nome += 1
                    continue
                
                escala.append({
                    "Semana": semana,
                    "Data": dia.strftime("%d/%m/%Y"),
                    "Dia": ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][dia_semana],
                    "Reunião": r,
                    "Apresentador": nome_atual
                })
                idx_nome += 1
                break
                
    return pd.DataFrame(escala)

if check_login():
    nomes_dinamicos = carregar_nomes()
    
    if nomes_dinamicos:
        df = gerar_escala(nomes_dinamicos)
        # Hoje é 25/03/2026, semana 13
        semana_atual_num = 13 
        
        st.title("🚀 MMD | Dashboard de Apresentações")
        st.sidebar.button("🔄 Atualizar Dados da Planilha", on_click=st.cache_data.clear)
        
        st.markdown("---")
        st.subheader(f"📌 Destaque da Semana {semana_atual_num}")
        
        df_semana = df[df["Semana"] == semana_atual_num]
        
        if not df_semana.empty:
            # Exibição organizada por data
            for data_label, group in df_semana.groupby("Data", sort=False):
                st.markdown(f"#### 📅 {group['Dia'].iloc[0]} ({data_label})")
                cols = st.columns(len(group))
                for i, (_, row) in enumerate(group.iterrows()):
                    with cols[i]:
                        st.info(f"**{row['Reunião']}**\n\n🏆 {row['Apresentador']}")
        
        st.markdown("---")
        st.subheader("🗓️ Consulta de Outras Semanas")
        semana_busca = st.select_slider("Arraste para ver o cronograma:", options=sorted(df["Semana"].unique()), value=semana_atual_num)
        
        # Filtra e exibe a tabela da semana selecionada
        df_final = df[df["Semana"] == semana_busca].drop(columns=["Semana"])
        st.dataframe(df_final, use_container_width=True, hide_index=True)
        
    else:
        st.warning("Aguardando lista de nomes da planilha... Verifique se a célula A1 é 'Funcionário'.")
