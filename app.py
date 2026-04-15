import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import streamlit.components.v1 as components
import io
import random
import gspread
import calendar

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Portal de Gestão", layout="wide")

# --- CONEXÃO COM GOOGLE SHEETS ---
def conectar_google_sheets():
    try:
        creds = st.secrets["gcp_service_account"]
        client = gspread.service_account_from_dict(dict(creds))
        sh = client.open("Escala MMD")
        return sh
    except Exception as e:
        return None

# --- ESTRUTURA DE TIMES ---
TORRES = {
    "Indireto Brasil": ["Debora", "Dani", "Abigail", "Luca", "Bruno", "Thiago", "Anna Laura"],
    "Material Fert Brasil": ["Amanda", "Sabrina", "Douglas"],
    "CRM": ["Julia", "Bruna", "Renan"],
    "Material Direto Brasil": ["Livia", "Rafael"],
    "Material Direto Latam": ["Ariel", "Cristian", "Enrique", "Sonia", "Gisele"],
    "Fert Latam": ["Jazmin", "Florencia", "Jesus", "Bianca", "Soledad", "Mijal", "Silvana", "Andrea", "Honorato", "Faiha"]
}
PESSOA_PARA_TORRE = {p: t for t, pessoas in TORRES.items() for p in pessoas}

# --- DICIONÁRIO DE TRADUÇÃO COMPLETO ---
I18N = {
    "PT": {
        "lang_code": "pt-BR",
        "titulo": "🚀 MMD | Portal de Gestão 2026",
        "login_tit": "Portal de Gestão MMD",
        "usuario": "Usuário",
        "senha": "Senha",
        "acessar": "Acessar Painel",
        "roteiro_ter": "📝 Roteiro Terça: Práticas + Iniciativas",
        "roteiro_qui": "📝 Roteiro Quinta: Lead Time + SLA",
        "estrutura_tit": "👥 Estrutura de Times",
        "buscar": "🔍 Buscar por Apresentador:",
        "todos": "Todos",
        "semana": "Semana:",
        "backup": "🔄 Backup",
        "flash_m": "Flash Manhã",
        "dias": ["Segunda-Feira", "Terça-Feira", "Quarta-Feira", "Quinta-Feira", "Sexta-Feira"],
        "meses": ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"],
        "ferias_tit": "🌴 Planejamento de Férias",
        "reg_periodo": "Registrar Período",
        "colaborador": "Colaborador:",
        "usuario_log": "Seu Usuário (Obrigatório):",
        "dt_inicio": "Data de Início:",
        "dt_fim": "Data de Término:",
        "obs": "Observação:",
        "btn_salvar": "💾 Salvar no Sheets",
        "grade_tit": "Grade de Disponibilidade",
        "sel_mes": "Mês:",
        "sel_ano": "Ano:",
        "filtro_equipe": "Filtrar por Equipe:",
        "viz_ocupacao": "Ocupação: {equipe}",
        "log_tit": "📋 Próximas Férias (Ordem Cronológica)",
        "err_user": "Por favor, informe o seu usuário.",
        "err_data": "A data de início não pode ser maior que a data de término.",
        "err_conflito": "❌ Erro: {nome} já tem férias na equipe '{equipe}' nesse período.",
        "sucesso": "✅ Férias registradas!",
        "livre": "Livre",
        "dias_semana_curto": ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    },
    "ES": {
        "lang_code": "es-ES",
        "titulo": "🚀 MMD | Portal de Gestión 2026",
        "login_tit": "Portal de Gestión MMD",
        "usuario": "Usuario",
        "senha": "Contraseña",
        "acessar": "Acceder al Panel",
        "roteiro_ter": "📝 Guion Martes: Prácticas + Iniciativas",
        "roteiro_qui": "📝 Guion Jueves: Lead Time + SLA",
        "estrutura_tit": "👥 Estructura de Equipos",
        "buscar": "🔍 Buscar por Presentador:",
        "todos": "Todos",
        "semana": "Semana:",
        "backup": "🔄 Backup",
        "flash_m": "Flash Mañana",
        "dias": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
        "meses": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
        "ferias_tit": "🌴 Planeamiento de Vacaciones",
        "reg_periodo": "Registrar Período",
        "colaborador": "Colaborador:",
        "usuario_log": "Tu Usuario (Obligatorio):",
        "dt_inicio": "Fecha de Inicio:",
        "dt_fim": "Fecha de Finalización:",
        "obs": "Observación:",
        "btn_salvar": "💾 Guardar en Sheets",
        "grade_tit": "Cuadrícula de Disponibilidad",
        "sel_mes": "Mes:",
        "sel_ano": "Año:",
        "filtro_equipe": "Filtrar por Equipo:",
        "viz_ocupacao": "Ocupación: {equipe}",
        "log_tit": "📋 Próximas Vacaciones (Orden Cronológico)",
        "err_user": "Por favor, informe su usuario.",
        "err_data": "La fecha de inicio no puede ser mayor que la fecha de finalización.",
        "err_conflito": "❌ Error: {nome} ya tiene vacaciones en el equipo '{equipe}' en este período.",
        "sucesso": "✅ ¡Vacaciones registradas!",
        "livre": "Libre",
        "dias_semana_curto": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    }
}

if "lang" not in st.session_state: st.session_state.lang = "PT"
t = I18N[st.session_state.lang]

# --- LOGIN ---
def check_login():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown(f"<h2 style='text-align: center;'>{t['login_tit']}</h2>", unsafe_allow_html=True)
        _, col2, _ = st.columns([1,1,1])
        with col2:
            with st.form("login"):
                u = st.text_input(t["usuario"]).strip()
                p = st.text_input(t["senha"], type="password").strip()
                if st.form_submit_button(t["acessar"], use_container_width=True):
                    if u == "MMD-Board" and p == "@MMD123#":
                        st.session_state.logged_in = True
                        st.rerun()
                    else: st.error("Acesso negado")
        return False
    return True

# --- MOTOR DE REGRAS ---
MAPA_REFERENCIA = {
    "Abigail": "Dani", "Amanda": "Mijal", "Anna Laura": "Soledad", "Ariel": "Rafael", 
    "Bianca M.": "Ariel", "Bruna": "Anna Laura", "Bruno": "Bianca M.", "Dani": "Jesus", 
    "Debora": "Bruna", "Diana": "Julia", "Florencia": "Diana", "Gisele": "Thiago", 
    "Honorato": "Bruno", "Jazmin": "Abigail", "Jesus": "Luca", "Julia": "Honorato", 
    "Livia": "Amanda", "Luca": "Jazmin", "Mijal": "Livia", "Rafael": "Florencia", 
    "Renan": "Debora", "Soledad": "Gisele", "Thiago": "Renan"
}

def encontrar_backup_vivo(nome, nomes_ativos):
    proximo = MAPA_REFERENCIA.get(nome)
    for _ in range(len(MAPA_REFERENCIA)):
        if proximo in nomes_ativos: return proximo
        proximo = MAPA_REFERENCIA.get(proximo)
    return "Sem Backup"

def gerar_escala_balanceada(nomes):
    random.seed(42)
    fila_base = nomes.copy()
    random.shuffle(fila_base)
    nomes_dor = [n for n in nomes if n not in ["Dani", "Rafael"]]
    random.shuffle(nomes_dor)
    cont_total, cont_dor = {n: 0 for n in nomes}, {n: 0 for n in nomes_dor}
    dias_range = pd.date_range(datetime(2026, 1, 1), datetime(2026, 12, 31), freq='B')
    escala = []
    for dia in dias_range:
        data_s, sem, d_sem = dia.strftime("%d/%m/%Y"), dia.isocalendar()[1], dia.weekday()
        d_nome = t["dias"][d_sem]
        quem_ja_foi = [e['Apresentador'] for e in escala if e['Semana'] == sem]
        ap_m = min([n for n in fila_base if n not in quem_ja_foi], key=lambda x: cont_total[x])
        cont_total[ap_m] += 1
        quem_ja_foi.append(ap_m)
        escala.append({"Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": t["flash_m"], "Apresentador": ap_m, "Backup": encontrar_backup_vivo(ap_m, nomes)})
        
        tipo_t = "DOR" if d_sem in [1, 3] else "Flash Tarde"
        cand_t = [n for n in (nomes_dor if tipo_t == "DOR" else fila_base) if n not in quem_ja_foi]
        ap_t = min(cand_t, key=lambda x: cont_dor[x] if tipo_t == "DOR" else cont_total[x])
        if tipo_t == "DOR": cont_dor[ap_t] += 1
        cont_total[ap_t] += 1
        escala.append({"Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": tipo_t, "Apresentador": ap_t, "Backup": encontrar_backup_vivo(ap_t, nomes)})
    return pd.DataFrame(escala)

# --- EXECUÇÃO ---
if check_login():
    st.sidebar.title("🌐 Idioma / Lenguaje")
    lang_opt = st.sidebar.radio("Selecione:", ["🇧🇷 Português", "🇪🇸 Español"], index=0 if st.session_state.lang == "PT" else 1)
    if ("Português" in lang_opt and st.session_state.lang == "ES") or ("Español" in lang_opt and st.session_state.lang == "PT"):
        st.session_state.lang = "PT" if "Português" in lang_opt else "ES"
        st.rerun()

    st.sidebar.divider()
    with st.sidebar.expander(t["estrutura_tit"]):
        for torre, membros in TORRES.items(): st.markdown(f"**{torre}:** {', '.join(membros)}")
    with st.sidebar.expander(t["roteiro_ter"]): st.markdown("- Lista Presença\n- Timekeeper\n- Escala\n- Behavior\n- Plano de Ação")
    with st.sidebar.expander(t["roteiro_qui"]): st.markdown("- Lead Time\n- FTR\n- Cats+BH\n- Work Plan")

    tab_escala, tab_ferias = st.tabs(["📅 Escalas", "🌴 " + ("Férias" if st.session_state.lang == "PT" else "Vacaciones")])

    with tab_escala:
        st.title(t["titulo"])
        nomes = sorted(list(MAPA_REFERENCIA.keys()))
        df_total = gerar_escala_balanceada(nomes)
        busca = st.selectbox(t["buscar"], [t["todos"]] + nomes)
        s_idx = st.select_slider(t["semana"], options=sorted(df_total["Semana"].unique()), value=datetime.now().isocalendar()[1])
        df_s = df_total[df_total["Semana"] == s_idx]
        if busca != t["todos"]: df_s = df_s[df_s["Apresentador"] == busca]
        for dt, gp in df_s.groupby("Data", sort=False):
            st.markdown(f"**{gp['Dia'].iloc[0]} - {dt}**")
            cols = st.columns(len(gp))
            for i, (_, r) in enumerate(gp.iterrows()):
                with cols[i]:
                    st.markdown(f'<div style="background-color:#f0f2f6;padding:15px;border-radius:10px;border-left:5px solid #ff4b4b;color:#333;"><b>{r["Reunião"]}</b><br><span style="font-size:18px;font-weight:bold;">🏆 {r["Apresentador"]}</span><br><small>{t["backup"]}: {r["Backup"]}</small></div>', unsafe_allow_html=True)

    with tab_ferias:
        st.title(t["ferias_tit"])
        sh = conectar_google_sheets()
        if sh:
            try:
                ws = sh.worksheet("DB_FERIAS")
                df_ferias = pd.DataFrame(ws.get_all_records())
            except: df_ferias = pd.DataFrame()

            col_form, col_grade = st.columns([1, 2])
            with col_form:
                st.subheader(t["reg_periodo"])
                with st.form("form_ferias"):
                    nome_sel = st.selectbox(t["colaborador"], sorted(list(PESSOA_PARA_TORRE.keys())))
                    user_login = st.text_input(t["usuario_log"])
                    d_ini, d_fim = st.date_input(t["dt_inicio"]), st.date_input(t["dt_fim"])
                    obs_f = st.text_input(t["obs"], value=f"Férias {d_ini.year}")
                    if st.form_submit_button(t["btn_salvar"]):
                        if not user_login: st.error(t["err_user"])
                        elif d_ini > d_fim: st.error(t["err_data"])
                        else:
                            torre_sel = PESSOA_PARA_TORRE.get(nome_sel)
                            ws.append_row([nome_sel, d_ini.strftime("%d/%m/%Y"), d_fim.strftime("%d/%m/%Y"), torre_sel, obs_f, datetime.now().strftime("%d/%m/%Y %H:%M:%S"), user_login])
                            st.success(t["sucesso"])
                            st.rerun()

            with col_grade:
                st.subheader(t["grade_tit"])
                c1, c2, c3 = st.columns(3)
                with c1: mes_sel = st.selectbox(t["sel_mes"], t["meses"], index=datetime.now().month-1)
                with c2: ano_sel = st.selectbox(t["sel_ano"], [2026, 2027, 2028, 2029])
                with c3: eq_sel = st.selectbox(t["filtro_equipe"], sorted(list(TORRES.keys())))
                m_idx = t["meses"].index(mes_sel) + 1
                st.caption(t["viz_ocupacao"].format(equipe=eq_sel))
                cols_h = st.columns(7)
                for i, d_n in enumerate(t["dias_semana_curto"]): cols_h[i].markdown(f"<p style='text-align:center;font-weight:bold;color:gray;'>{d_n}</p>", unsafe_allow_html=True)
                cal = calendar.monthcalendar(ano_sel, m_idx)
                for week in cal:
                    cols_g = st.columns(7)
                    for i, day in enumerate(week):
                        if day == 0: cols_g[i].write("")
                        else:
                            data_c = datetime(ano_sel, m_idx, day).date()
                            status, cor = t["livre"], "#28a745"
                            if not df_ferias.empty:
                                df_v = df_ferias.copy()
                                df_v['Data Início'] = pd.to_datetime(df_v['Data Início'], dayfirst=True).dt.date
                                df_v['Data Final'] = pd.to_datetime(df_v['Data Final'], dayfirst=True).dt.date
                                conf_v = df_v[(df_v['Equipe'] == eq_sel) & (data_c >= df_v['Data Início']) & (data_c <= df_v['Data Final'])]
                                if not conf_v.empty: status, cor = conf_v.iloc[0]['Nome'], "#dc3545"
                            cols_g[i].markdown(f'<div style="background-color:{cor};color:white;padding:5px;border-radius:5px;text-align:center;margin-bottom:8px;font-size:11px;height:55px;"><small>{day}</small><br><b>{status}</b></div>', unsafe_allow_html=True)

            st.divider()
            st.subheader(t["log_tit"])
            if not df_ferias.empty:
                df_log = df_ferias.copy()
                df_log['Data_Início_DT'] = pd.to_datetime(df_log['Data Início'], dayfirst=True)
                df_log = df_log.sort_values(by='Data_Início_DT', ascending=True)
                st.dataframe(df_log.drop(columns=['Data_Início_DT']), use_container_width=True, hide_index=True)
