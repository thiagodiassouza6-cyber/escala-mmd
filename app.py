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

# --- DICIONÁRIO DE TRADUÇÃO (I18N) ---
I18N = {
    "PT": {
        "lang_code": "pt-BR",
        "titulo": "🚀 MMD | Portal de Gestão 2026",
        "aba_escala": "📅 Escalas",
        "aba_ferias": "🌴 Planejamento de Férias",
        "login_tit": "Portal de Escalas MMD",
        "usuario": "Usuário", "senha": "Senha", "acessar": "Acessar Painel",
        "roteiro_ter": "📝 Roteiro Terça: Práticas + Iniciativas",
        "roteiro_qui": "📝 Roteiro Quinta: Lead Time + SLA",
        "dias": ["Segunda-Feira", "Terça-Feira", "Quarta-Feira", "Quinta-Feira", "Sexta-Feira"],
        "meses": ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    },
    "ES": {
        "lang_code": "es-ES",
        "titulo": "🚀 MMD | Portal de Gestión 2026",
        "aba_escala": "📅 Escalas",
        "aba_ferias": "🌴 Plan de Vacaciones",
        "login_tit": "Portal de Escalas MMD",
        "usuario": "Usuario", "senha": "Contraseña", "acessar": "Acceder al Panel",
        "roteiro_ter": "📝 Guion Martes: Prácticas + Iniciativas",
        "roteiro_qui": "📝 Guion Jueves: Lead Time + SLA",
        "dias": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
        "meses": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    }
}

if "lang" not in st.session_state: st.session_state.lang = "PT"
t = I18N[st.session_state.lang]

# --- LOGIN ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown(f"<h2 style='text-align: center;'>{t['login_tit']}</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        with st.form("login"):
            u, p = st.text_input(t["usuario"]), st.text_input(t["senha"], type="password")
            if st.form_submit_button(t["acessar"], use_container_width=True):
                if u == "MMD-Board" and p == "@MMD123#": 
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Erro de Autenticação")
else:
    # Sidebar Idioma
    st.sidebar.title("🌐 Idioma")
    lang_opt = st.sidebar.radio("Seleccione:", ["🇧🇷 Português", "🇪🇸 Español"], index=0 if st.session_state.lang == "PT" else 1)
    st.session_state.lang = "PT" if "Português" in lang_opt else "ES"
    t = I18N[st.session_state.lang]

    tab_escala, tab_ferias = st.tabs([t["aba_escala"], t["aba_ferias"]])

    # --- ABA 1: ESCALAS (LAYOUT ORIGINAL) ---
    with tab_escala:
        st.title(t["titulo"])
        # Aqui entra sua lógica de escala balanceada original que já tínhamos feito
        nomes_func = sorted(list(PESSOA_PARA_TORRE.keys()))
        
        c1, c2 = st.columns(2)
        with c1: st.info(t["roteiro_ter"])
        with c2: st.success(t["roteiro_qui"])
        
        # Gerar DataFrame de escala para exibição
        dias_uteis = pd.date_range(start="2026-01-01", end="2026-12-31", freq='B')
        df_esc = pd.DataFrame([{
            "Data": d.strftime("%d/%m/%Y"),
            "Dia": t["dias"][d.weekday()],
            "Apresentador": nomes_func[i % len(nomes_func)]
        } for i, d in enumerate(dias_uteis)])
        st.dataframe(df_esc, use_container_width=True)

    # --- ABA 2: FÉRIAS (AJUSTADA) ---
    with tab_ferias:
        st.title(t["aba_ferias"])
        sh = conectar_google_sheets()
        if sh:
            ws = sh.worksheet("DB_FERIAS")
            df_ferias = pd.DataFrame(ws.get_all_records())

            col_form, col_grade = st.columns([1, 2])
            
            with col_form:
                st.subheader("Registrar Período")
                with st.form("cad_ferias", clear_on_submit=True):
                    nome_f = st.selectbox("Colaborador:", nomes_func)
                    user_login = st.text_input("Seu Usuário (Obrigatório):") # AJUSTE 1
                    d_ini = st.date_input("Início:")
                    d_fim = st.date_input("Fim:")
                    obs = st.text_input("Obs:", "Férias 2026")
                    
                    if st.form_submit_button("💾 Salvar no Sheets"):
                        if not user_login:
                            st.error("Usuário é obrigatório!")
                        else:
                            minha_torre = PESSOA_PARA_TORRE.get(nome_f)
                            # AJUSTE 2: Nomes de colunas conforme print (Nome, Data Início, Data Final, Equipe, Observação, Data Registro, Usuário Logado)
                            nova_linha = [
                                nome_f, d_ini.strftime("%d/%m/%Y"), d_fim.strftime("%d/%m/%Y"), 
                                minha_torre, obs, datetime.now().strftime("%d/%m/%Y %H:%M:%S"), user_login
                            ]
                            ws.append_row(nova_linha)
                            st.success("Gravado!")
                            st.rerun()

            with col_grade:
                st.subheader("Grade de Disponibilidade")
                mes_sel = st.selectbox("Mês:", t["meses"], index=datetime.now().month-1)
                mes_idx = t["meses"].index(mes_sel) + 1
                
                # AJUSTE 3: Lógica da Grade Colorida por Torre
                torre_atual = PESSOA_PARA_TORRE.get(nome_f)
                st.caption(f"Visualizando ocupação para a equipe: **{torre_atual}**")
                
                cal = calendar.monthcalendar(2026, mes_idx)
                cols = st.columns(7)
                for week in cal:
                    for i, day in enumerate(week):
                        if day == 0: cols[i].write("")
                        else:
                            data_c = datetime(2026, mes_idx, day)
                            status, cor = "Livre", "#28a745"
                            
                            if not df_ferias.empty:
                                df_ferias['Data Início'] = pd.to_datetime(df_ferias['Data Início'], dayfirst=True)
                                df_ferias['Data Final'] = pd.to_datetime(df_ferias['Data Final'], dayfirst=True)
                                
                                # Verifica se alguém da mesma EQUIPE está de férias
                                ocup = df_ferias[(df_ferias['Equipe'] == torre_atual) & 
                                                 (data_c >= df_ferias['Data Início']) & 
                                                 (data_c <= df_ferias['Data Final'])]
                                if not ocup.empty:
                                    status, cor = ocup.iloc[0]['Nome'], "#dc3545"
                            
                            cols[i].markdown(f"""<div style="background-color:{cor}; color:white; padding:5px; border-radius:5px; text-align:center; margin-bottom:5px;">
                                <small>{day}</small><br><b>{status}</b></div>""", unsafe_allow_html=True)

            st.divider()
            st.subheader("Log de Registros")
            st.dataframe(df_ferias.tail(10), use_container_width=True)
