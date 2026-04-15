import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import random
import gspread

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Portal Integrado", layout="wide")

# --- CONEXÃO COM GOOGLE SHEETS ---
def conectar_google_sheets():
    try:
        creds = st.secrets["gcp_service_account"]
        client = gspread.service_account_from_dict(dict(creds))
        sh = client.open("Escala MMD")
        return sh
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return None

# --- ESTRUTURA DE TIMES ATUALIZADA ---
TORRES = {
    "Indireto Brasil": ["Debora", "Dani", "Abigail", "Luca", "Bruno", "Thiago", "Anna Laura"],
    "Material Fert Brasil": ["Amanda", "Sabrina", "Douglas"],
    "CRM": ["Julia", "Bruna", "Renan"],
    "Material Direto Brasil": ["Livia", "Rafael"],
    "Material Direto Latam": ["Ariel", "Cristian", "Enrique", "Sonia", "Gisele"],
    "Fert Latam": ["Jazmin", "Florencia", "Jesus", "Bianca", "Soledad", "Mijal", "Silvana", "Andrea", "Honorato", "Faiha"]
}

PESSOA_PARA_TORRE = {pessoa: torre for torre, pessoas in TORRES.items() for pessoa in pessoas}

# --- TRADUÇÕES E NOMES ---
MESES_PT = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
DIAS_SEM_PT = ["Segunda-Feira", "Terça-Feira", "Quarta-Feira", "Quinta-Feira", "Sexta-Feira"]

# --- LOGIN ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>Portal MMD</h2>", unsafe_allow_html=True)
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login"):
                u = st.text_input("Usuário")
                p = st.text_input("Senha", type="password")
                if st.form_submit_button("Acessar"):
                    if u == "MMD-Board" and p == "@MMD123#":
                        st.session_state.logged_in = True
                        st.rerun()
                    else: st.error("Dados incorretos")
else:
    tab_escala, tab_ferias = st.tabs(["📅 Escalas", "🌴 Planejamento de Férias"])

    # --- ABA 1: ESCALAS ---
    with tab_escala:
        st.title("🚀 MMD | Portal de Gestão 2026")
        # Lógica de Escala Simplificada para Exibição
        nomes_lista = sorted(list(PESSOA_PARA_TORRE.keys()))
        random.seed(42)
        dias_uteis = pd.date_range(start="2026-01-01", end="2026-12-31", freq='B')
        escala_data = []
        for i, data in enumerate(dias_uteis):
            escala_data.append({
                "Semana": data.isocalendar()[1],
                "Data": data.strftime("%d/%m/%Y"),
                "Dia": DIAS_SEM_PT[data.weekday()],
                "Apresentador": nomes_lista[i % len(nomes_lista)]
            })
        st.dataframe(pd.DataFrame(escala_data), use_container_width=True)

    # --- ABA 2: FÉRIAS (LAYOUT ORIGINAL RESTAURADO) ---
    with tab_ferias:
        st.title("🌴 Planejamento de Férias Integrado")
        st.info("Regra: Pessoas da mesma torre não podem sair de férias no mesmo período.")
        
        sh = conectar_google_sheets()
        if sh:
            ws = sh.worksheet("DB_FERIAS")
            df_ferias = pd.DataFrame(ws.get_all_records())

            col_form, col_grade = st.columns([1, 3])

            with col_form:
                st.subheader("Marcar Período")
                with st.form("cad_ferias", clear_on_submit=True):
                    nome_f = st.selectbox("Seu Nome:", nomes_lista)
                    user_login = st.text_input("Seu Usuário (Obrigatório):")
                    d_ini = st.date_input("Início:", value=datetime.today())
                    d_fim = st.date_input("Término:", value=datetime.today() + timedelta(days=10))
                    obs = st.text_input("Observação:", "Férias 2026")
                    
                    if st.form_submit_button("💾 Salvar no Sheets"):
                        if not user_login:
                            st.error("Por favor, insira seu usuário.")
                        else:
                            equipe_sel = PESSOA_PARA_TORRE.get(nome_f)
                            # Colunas: Nome, Data Início, Data Final, Equipe, Observação, Data Registro, Usuário Logado
                            nova_linha = [
                                nome_f, d_ini.strftime("%d/%m/%Y"), d_fim.strftime("%d/%m/%Y"), 
                                equipe_sel, obs, datetime.now().strftime("%d/%m/%Y %H:%M:%S"), user_login
                            ]
                            ws.append_row(nova_linha)
                            st.success("Registrado com sucesso!")
                            st.rerun()

            with col_grade:
                st.write("Visualizar Disponibilidade:")
                mes_nome = st.selectbox("Selecione o Mês:", MESES_PT, index=datetime.now().month-1)
                mes_idx = MESES_PT.index(mes_nome) + 1
                
                st.subheader(f"Grade Mensal: {mes_nome} / 2026")
                
                # Lógica da Grade Colorida baseada na Equipe do nome selecionado
                torre_atual = PESSOA_PARA_TORRE.get(nome_f)
                
                # Criar grid de calendários (7 colunas)
                cols_grade = st.columns(7)
                cal = calendar.monthcalendar(2026, mes_idx)
                
                for week in cal:
                    for i, day in enumerate(week):
                        if day == 0:
                            cols_grade[i].write("")
                        else:
                            data_box = datetime(2026, mes_idx, day)
                            status = "Livre"
                            bg_color = "#28a745" # Verde
                            
                            # Verificar se alguém da mesma equipe está de férias nesta data
                            if not df_ferias.empty:
                                df_ferias['Data Início'] = pd.to_datetime(df_ferias['Data Início'], dayfirst=True)
                                df_ferias['Data Final'] = pd.to_datetime(df_ferias['Data Final'], dayfirst=True)
                                
                                conflito = df_ferias[
                                    (df_ferias['Equipe'] == torre_atual) & 
                                    (data_box >= df_ferias['Data Início']) & 
                                    (data_box <= df_ferias['Data Final'])
                                ]
                                
                                if not conflito.empty:
                                    status = conflito.iloc[0]['Nome']
                                    bg_color = "#dc3545" # Vermelho
                            
                            cols_grade[i].markdown(
                                f"""<div style="background-color:{bg_color}; color:white; padding:5px; 
                                border-radius:5px; text-align:center; margin-bottom:5px;">
                                <span style="font-size:12px;">{day}</span><br><b>{status}</b></div>""", 
                                unsafe_allow_html=True
                            )

            st.divider()
            st.subheader("📋 Log de Férias (Base Sheets)")
            st.dataframe(df_ferias.tail(10), use_container_width=True)
