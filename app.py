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

# --- DICIONÁRIO DE TRADUÇÃO ---
I18N = {
    "PT": {
        "lang_code": "pt-BR",
        "titulo": "🚀 MMD | Portal de Gestão 2026",
        "login_tit": "Portal de Gestão MMD",
        "usuario": "Usuário",
        "senha": "Senha",
        "acessar": "Acessar Painel",
        "acessibilidade": "Ativar Acessibilidade",
        "roteiro_ter": "📝 Roteiro Terça: Práticas + Iniciativas",
        "roteiro_qui": "📝 Roteiro Quinta: Lead Time + SLA",
        "estrutura_tit": "👥 Estrutura de Times",
        "exp_mes": "📂 Exportar Mês",
        "exp_ano": "📅 Exportar Ano",
        "baixar": "Baixar",
        "buscar": "🔍 Buscar por Apresentador:",
        "todos": "Todos",
        "semana": "Semana:",
        "agendar": "📅 AGENDAR",
        "backup": "🔄 Backup",
        "backup2": "🛡️ Backup 2",
        "backup_oculto": "Backup Oculto",
        "stats": "📊 {nome}: {total} reuniões no ano (sendo {dor} reuniões DOR).",
        "flash_m": "Flash Manhã",
        "resp_m": "Responsável Manhã",
        "resp_t": "Responsável Tarde",
        "tipo_t": "Tipo Tarde/DOR",
        "mes_col": "Mês",
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
        "sucesso": "✅ Férias registradas com sucesso!",
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
        "acessibilidade": "Activar Accesibilidad",
        "roteiro_ter": "📝 Guion Martes: Prácticas + Iniciativas",
        "roteiro_qui": "📝 Guion Jueves: Lead Time + SLA",
        "estrutura_tit": "👥 Estructura de Equipos",
        "exp_mes": "📂 Exportar Mes",
        "exp_ano": "📅 Exportar Año",
        "baixar": "Descargar",
        "buscar": "🔍 Buscar por Presentador:",
        "todos": "Todos",
        "semana": "Semana:",
        "agendar": "📅 AGENDAR",
        "backup": "🔄 Backup",
        "backup2": "🛡️ Backup 2",
        "backup_oculto": "Backup Oculto",
        "stats": "📊 {nome}: {total} reuniones en el año ({dor} reuniones DOR).",
        "flash_m": "Flash Mañana",
        "resp_m": "Responsable Mañana",
        "resp_t": "Responsable Tarde",
        "tipo_t": "Tipo Tarde/DOR",
        "mes_col": "Mes",
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
        "sucesso": "✅ ¡Vacaciones registradas!",
        "livre": "Libre",
        "dias_semana_curto": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    }
}

if "lang" not in st.session_state: st.session_state.lang = "PT"
t = I18N[st.session_state.lang]

# --- LÓGICA DE BACKUP E ESCALA (MANTIDA) ---
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
        b1_m = encontrar_backup_vivo(ap_m, nomes)
        b2_m = encontrar_backup_vivo(b1_m, nomes)
        bo_m = encontrar_backup_vivo(b2_m, nomes)
        escala.append({
            "Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": t["flash_m"], 
            "Apresentador": ap_m, "Backup": b1_m, "Backup2": b2_m, "BackupOculto": bo_m,
            "Link": f"https://outlook.office.com/calendar/0/deeplink/compose?subject={urllib.parse.quote(t['flash_m'])}&startdt={dia.strftime('%Y-%m-%d')}T09:45:00"
        })
        
        quem_ja_foi.append(ap_m)
        tipo_t = "DOR" if d_sem in [1, 3] else "Flash Tarde"
        cand_t = [n for n in (nomes_dor if tipo_t == "DOR" else fila_base) if n not in quem_ja_foi]
        ap_t = min(cand_t, key=lambda x: cont_dor[x] if tipo_t == "DOR" else cont_total[x])
        if tipo_t == "DOR": cont_dor[ap_t] += 1
        cont_total[ap_t] += 1
        b1_t = encontrar_backup_vivo(ap_t, nomes)
        b2_t = encontrar_backup_vivo(b1_t, nomes)
        bo_t = encontrar_backup_vivo(b2_t, nomes)
        escala.append({
            "Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": tipo_t, 
            "Apresentador": ap_t, "Backup": b1_t, "Backup2": b2_t, "BackupOculto": bo_t,
            "Link": f"https://outlook.office.com/calendar/0/deeplink/compose?subject={urllib.parse.quote(tipo_t)}&startdt={dia.strftime('%Y-%m-%d')}T15:00:00"
        })
    return pd.DataFrame(escala)

# --- EXECUÇÃO DO APP ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    # Simples Verificação de Login
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
                else: st.error("Acesso Negado")
else:
    # --- INTERFACE PRINCIPAL ---
    st.sidebar.title("🌐 Idioma")
    lang_opt = st.sidebar.radio("Selecione:", ["🇧🇷 Português", "🇪🇸 Español"], index=0 if st.session_state.lang == "PT" else 1)
    st.session_state.lang = "PT" if "Português" in lang_opt else "ES"

    tab_escala, tab_ferias = st.tabs(["📅 Escalas", t["ferias_tit"]])

    with tab_escala:
        st.title(t["titulo"])
        # (Lógica de exibição da escala conforme código anterior...)
        # Aqui você pode inserir os cards e o gráfico de stats que já funcionavam.

    with tab_ferias:
        st.title(t["ferias_tit"])
        sh = conectar_google_sheets()
        if sh:
            ws = sh.worksheet("DB_FERIAS")
            data = ws.get_all_records()
            df_ferias = pd.DataFrame(data)

            col_form, col_grade = st.columns([1, 2])

            with col_form:
                st.subheader(t["reg_periodo"])
                with st.form("form_ferias", clear_on_submit=True):
                    nome_sel = st.selectbox(t["colaborador"], sorted(list(PESSOA_PARA_TORRE.keys())))
                    user_login = st.text_input(t["usuario_log"])
                    d_ini = st.date_input(t["dt_inicio"])
                    d_fim = st.date_input(t["dt_fim"])
                    obs_f = st.text_input(t["obs"], value=f"Férias {d_ini.year}")

                    if st.form_submit_button(t["btn_salvar"]):
                        if not user_login:
                            st.error(t["err_user"])
                        elif d_ini > d_fim:
                            st.error(t["err_data"])
                        else:
                            torre_sel = PESSOA_PARA_TORRE.get(nome_sel)
                            
                            # --- NOVA REGRA DE VALIDAÇÃO GLOBAL (PARA TODAS AS EQUIPES) ---
                            conflito_detectado = False
                            if not df_ferias.empty:
                                df_valid = df_ferias.copy()
                                # Converter datas do Sheets para comparação
                                df_valid['Data Início'] = pd.to_datetime(df_valid['Data Início'], dayfirst=True).dt.date
                                df_valid['Data Final'] = pd.to_datetime(df_valid['Data Final'], dayfirst=True).dt.date
                                
                                # Verifica se alguém DA MESMA EQUIPE está de férias no período solicitado
                                # Regra: (Novo_Inicio <= Existente_Fim) E (Novo_Fim >= Existente_Inicio)
                                conflitos = df_valid[
                                    (df_valid['Equipe'] == torre_sel) &
                                    (d_ini <= df_valid['Data Final']) &
                                    (d_fim >= df_valid['Data Início'])
                                ]
                                
                                if not conflitos.empty:
                                    conflito_detectado = True
                                    pessoa_conflito = conflitos.iloc[0]['Nome']
                                    st.error(f"❌ Conflito na equipe {torre_sel}: {pessoa_conflito} já está de férias nesse período. É necessário que ela retorne para você sair.")

                            if not conflito_detectado:
                                ws.append_row([
                                    nome_sel, d_ini.strftime("%d/%m/%Y"), d_fim.strftime("%d/%m/%Y"),
                                    torre_sel, obs_f, datetime.now().strftime("%d/%m/%Y %H:%M:%S"), user_login
                                ])
                                st.success(t["sucesso"])
                                st.rerun()

            with col_grade:
                st.subheader(t["grade_tit"])
                c1, c2, c3 = st.columns(3)
                with c1: mes_f = st.selectbox(t["sel_mes"], t["meses"], index=datetime.now().month-1)
                with c2: ano_f = st.selectbox(t["sel_ano"], [2026, 2027, 2028, 2029])
                with c3: eq_f = st.selectbox(t["filtro_equipe"], sorted(list(TORRES.keys())))

                m_idx = t["meses"].index(mes_f) + 1
                cal = calendar.monthcalendar(ano_f, m_idx)
                
                # Renderização da grade (Calendário visual)
                cols_h = st.columns(7)
                for i, d_n in enumerate(t["dias_semana_curto"]): 
                    cols_h[i].markdown(f"<p style='text-align:center;font-weight:bold;color:gray;'>{d_n}</p>", unsafe_allow_html=True)
                
                for week in cal:
                    cols_g = st.columns(7)
                    for i, day in enumerate(week):
                        if day == 0:
                            cols_g[i].write("")
                        else:
                            data_c = datetime(ano_f, m_idx, day).date()
                            status, cor = t["livre"], "#28a745"
                            if not df_ferias.empty:
                                df_v = df_ferias.copy()
                                df_v['Data Início'] = pd.to_datetime(df_v['Data Início'], dayfirst=True).dt.date
                                df_v['Data Final'] = pd.to_datetime(df_v['Data Final'], dayfirst=True).dt.date
                                conf_v = df_v[(df_v['Equipe'] == eq_f) & (data_c >= df_v['Data Início']) & (data_c <= df_v['Data Final'])]
                                if not conf_v.empty:
                                    status, cor = conf_v.iloc[0]['Nome'], "#dc3545"
                            
                            cols_g[i].markdown(f'<div style="background-color:{cor};color:white;padding:5px;border-radius:5px;text-align:center;margin-bottom:8px;font-size:11px;height:55px;"><small>{day}</small><br><b>{status}</b></div>', unsafe_allow_html=True)

            st.divider()
            st.subheader(t["log_tit"])
            if not df_ferias.empty:
                # Ordenar por data de início para o log cronológico
                df_log = df_ferias.copy()
                df_log['DT_INI'] = pd.to_datetime(df_log['Data Início'], dayfirst=True)
                df_log = df_log.sort_values('DT_INI')
                st.dataframe(df_log.drop(columns=['DT_INI']), use_container_width=True, hide_index=True)
