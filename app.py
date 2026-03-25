import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Escala de Apresentações", layout="wide")

# CONFIGURAÇÃO DO GOOGLE SHEETS
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

def criar_link_agenda(data_str, reuniao, apresentador):
    data_obj = datetime.strptime(data_str, "%d/%m/%Y")
    hora = "094500" if "Manhã" in reuniao else "150000"
    data_formatada = data_obj.strftime("%Y%m%d")
    inicio = f"{data_formatada}T{hora}"
    fim_obj = datetime.strptime(inicio, "%Y%m%dT%H%M%S") + timedelta(minutes=30)
    fim = fim_obj.strftime("%Y%m%dT%H%M%S")
    titulo = urllib.parse.quote(f"🔔 Apresentação MMD: {reuniao}")
    detalhes = urllib.parse.quote(f"Apresentador: {apresentador}\nLembrete de 60 minutos configurado.")
    return f"https://www.google.com/calendar/render?action=TEMPLATE&text={titulo}&dates={inicio}/{fim}&details={detalhes}"

@st.cache_data(ttl=600)
def carregar_nomes():
    try:
        df_sheets = pd.read_csv(SHEET_URL)
        return sorted(df_sheets['Funcionário'].dropna().unique().tolist())
    except:
        return []

def gerar_escala(nomes):
    data_inicio = datetime(2026, 1, 1)
    data_fim = datetime(2026, 12, 31)
    dias = pd.date_range(data_inicio, data_fim, freq='B')
    escala = []
    idx_nome = 0
    for dia in dias:
        semana = dia.isocalendar()[1]
        if semana < 13: continue # Começando na semana atual do projeto
        dia_semana = dia.weekday()
        
        # Terças e Quintas: Apenas Manhã e DOR (2 reuniões)
        reunioes = ["Flash Manhã", "DOR"] if dia_semana in [1, 3] else ["Flash Manhã", "Flash Tarde"]
        
        for r in reunioes:
            while True:
                nome_atual = nomes[idx_nome % len(nomes)]
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
    nomes_lista = carregar_nomes()
    if nomes_lista:
        df_total = gerar_escala(nomes_lista)
        
        st.title("🚀 MMD | Dashboard de Apresentações")
        
        # --- FILTRO POR NOME ---
        opcoes_nomes = ["Todos"] + nomes_lista
        filtro_nome = st.selectbox("🔍 Buscar por Apresentador (Listar todos os dias do ano):", opcoes_nomes)
        
        st.sidebar.button("🔄 Atualizar Dados", on_click=st.cache_data.clear)

        if filtro_nome != "Todos":
            # --- VISÃO FILTRADA (LISTAGEM ANUAL) ---
            st.markdown("---")
            st.subheader(f"📅 Cronograma Anual: {filtro_nome}")
            
            df_pessoal = df_total[df_total["Apresentador"] == filtro_nome].copy()
            
            if not df_pessoal.empty:
                # Criar coluna com link de agenda para a tabela
                df_pessoal["Lembrete Google"] = df_pessoal.apply(
                    lambda x: criar_link_agenda(x["Data"], x["Reunião"], x["Apresentador"]), axis=1
                )
                
                # Exibe a tabela completa com as colunas relevantes
                st.dataframe(
                    df_pessoal[["Data", "Dia", "Reunião", "Semana"]],
                    use_container_width=True,
                    hide_index=True
                )
                
                st.info(f"O apresentador **{filtro_nome}** possui {len(df_pessoal)} apresentações até o fim de 2026.")
            else:
                st.warning("Nenhuma apresentação encontrada para este nome.")
        
        else:
            # --- VISÃO GERAL (CRONOGRAMA POR SEMANA) ---
            st.markdown("---")
            st.subheader("🗓️ Cronograma Geral por Semana")
            
            semana_busca = st.select_slider("Arraste para ver a escala da semana:", 
                                            options=sorted(df_total["Semana"].unique()), 
                                            value=13)
            
            df_semana = df_total[df_total["Semana"] == semana_busca].drop(columns=["Semana"])
            
            # Exibição em Cards para facilitar leitura rápida
            cols = st.columns(len(df_semana) if len(df_semana) > 0 else 1)
            for i, (_, row) in enumerate(df_semana.iterrows()):
                with cols[i]:
                    st.info(f"**{row['Data']}** ({row['Dia']})\n\n**{row['Reunião']}**\n\n🏆 {row['Apresentador']}")
            
            st.table(df_semana)
