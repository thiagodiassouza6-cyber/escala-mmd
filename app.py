import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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

# --- DICIONÁRIO DE TRADUÇÃO ---
I18N = {
    "PT": {
        "titulo": "🚀 MMD | Portal de Gestão 2026",
        "aba_escala": "📅 Escalas",
        "aba_ferias": "🌴 Planejamento de Férias",
        "login_tit": "Portal de Escalas MMD",
        "usuario": "Usuário", "senha": "Senha", "acessar": "Acessar",
        "dias": ["Segunda-Feira", "Terça-Feira", "Quarta-Feira", "Quinta-Feira", "Sexta-Feira"],
        "meses": ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    }
}
t = I18N["PT"]

# --- FUNÇÃO DE ESCALA ---
def gerar_escala_balanceada(nomes):
    random.seed(42)
    fb = nomes.copy()
    random.shuffle(fb)
    c_tot = {n: 0 for n in nomes}
    dias = pd.date_range(datetime(2026, 1, 1), datetime(2026, 12, 31), freq='B')
    esc = []
    for d in dias:
        dt, sem, d_sem = d.strftime("%d/%m/%Y"), d.isocalendar()[1], d.weekday()
        ap_m = min([n for n in fb], key=lambda x: c_tot[x]); c_tot[ap_m] += 1
        esc.append({"Semana": sem, "Data": dt, "Dia": t["dias"][d_sem], "Apresentador": ap_m})
    return pd.DataFrame(esc)

# --- LOGIN ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>Portal MMD</h2>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            if u == "MMD-Board" and p == "@MMD123#":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("Dados incorretos")
else:
    tab_escala, tab_ferias = st.tabs([t["aba_escala"], t["aba_ferias"]])

    # --- ABA 1: ESCALAS ---
    with tab_escala:
        st.title(t["titulo"])
        nomes_lista = sorted(list(PESSOA_PARA_TORRE.keys()))
        df_escala = gerar_escala_balanceada(nomes_lista)
        st.dataframe(df_escala, use_container_width=True)

    # --- ABA 2: FÉRIAS ---
    with tab_ferias:
        st.title(t["aba_ferias"])
        sh = conectar_google_sheets()
        
        if sh:
            ws = sh.worksheet("DB_FERIAS")
            raw_data = ws.get_all_records()
            df_ferias = pd.DataFrame(raw_data)

            col_form, col_grade = st.columns([1, 2])

            with col_form:
                st.subheader("📝 Registrar Período")
                with st.form("form_ferias", clear_on_submit=True):
                    nome_sel = st.selectbox("Colaborador", nomes_lista)
                    login_user = st.text_input("Seu Usuário (Obrigatório)")
                    d_ini = st.date_input("Data de Início")
                    d_fim = st.date_input("Data de Término")
                    obs = st.text_input("Observação", "Férias 2026")
                    
                    if st.form_submit_button("💾 Salvar no Sheets"):
                        if not login_user:
                            st.error("Por favor, preencha seu usuário.")
                        elif d_ini > d_fim:
                            st.error("Data de início não pode ser maior que o término.")
                        else:
                            torre_sel = PESSOA_PARA_TORRE.get(nome_sel)
                            # Ordem das colunas: Nome, Data Início, Data Final, Equipe, Observação, Data Registro, Usuário Logado
                            nova_linha = [
                                nome_sel, 
                                d_ini.strftime("%d/%m/%Y"), 
                                d_fim.strftime("%d/%m/%Y"), 
                                torre_sel, 
                                obs, 
                                datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                login_user
                            ]
                            ws.append_row(nova_linha)
                            st.success("Férias registradas com sucesso!")
                            st.rerun()

            with col_grade:
                st.subheader("📅 Grade de Disponibilidade")
                mes_n = st.selectbox("Selecione o Mês", range(1, 13), format_func=lambda x: t["meses"][x-1])
                
                if not df_ferias.empty:
                    # Filtra apenas quem é da mesma torre para a grade visual
                    user_torre = PESSOA_PARA_TORRE.get(nome_sel)
                    df_view = df_ferias[df_ferias['Equipe'] == user_torre].copy()
                    
                    # Converte datas para comparação
                    df_view['Data Início'] = pd.to_datetime(df_view['Data Início'], dayfirst=True)
                    df_view['Data Final'] = pd.to_datetime(df_view['Data Final'], dayfirst=True)

                    st.write(f"Exibindo férias para a torre: **{user_torre}**")
                    st.dataframe(df_view[['Nome', 'Data Início', 'Data Final', 'Observação']], use_container_width=True)
                
                st.info("Dica: Os dias ocupados na planilha bloqueiam automaticamente a disponibilidade na torre.")

            st.divider()
            st.subheader("📋 Log Geral de Registros")
            st.table(df_ferias.tail(10))
