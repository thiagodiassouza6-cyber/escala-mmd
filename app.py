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
        "titulo": "🚀 MMD | Portal de Gestão 2026",
        "login_tit": "Portal de Gestão MMD",
        "usuario": "Usuário",
        "senha": "Senha",
        "acessar": "Acessar Painel",
        "roteiro_ter": "📝 Roteiro Terça",
        "roteiro_qui": "📝 Roteiro Quinta",
        "estrutura_tit": "👥 Estrutura de Times",
        "exp_mes": "📂 Exportar Mês",
        "exp_ano": "📅 Exportar Ano",
        "baixar": "Baixar",
        "buscar": "🔍 Buscar por Apresentador:",
        "todos": "Todos",
        "semana": "Semana:",
        "agendar": "📅 AGENDAR",
        "backup": "Backup",
        "backup2": "Backup 2",
        "stats": "📊 {nome}: {total} reuniões no ano.",
        "flash_m": "Flash Manhã",
        "resp_m": "Responsável Manhã",
        "resp_t": "Responsável Tarde",
        "tipo_t": "Tipo Tarde/DOR",
        "mes_col": "Mês",
        "dias": ["Segunda-Feira", "Terça-Feira", "Quarta-Feira", "Quinta-Feira", "Sexta-Feira"],
        "meses": ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"],
        "ferias_tit": "🌴 Planejamento de Férias",
        "reg_periodo": "Registrar Período",
        "gerenciar_f": "⚙️ Gerenciar Minhas Férias",
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
        "log_tit": "📋 Próximas Férias (Ativas)",
        "err_user": "Informe seu usuário.",
        "err_data": "Início maior que o fim.",
        "err_conflito": "❌ Conflito: {nome} já tem férias.",
        "sucesso": "✅ Registrado!",
        "sucesso_del": "✅ Removido!",
        "livre": "Livre",
        "dias_semana_curto": ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    },
    "ES": {
        "titulo": "🚀 MMD | Portal de Gestión 2026",
        "login_tit": "Portal de Gestión MMD",
        "usuario": "Usuario",
        "senha": "Contraseña",
        "acessar": "Acceder",
        "roteiro_ter": "📝 Guion Martes",
        "roteiro_qui": "📝 Guion Jueves",
        "estrutura_tit": "👥 Equipos",
        "exp_mes": "📂 Exportar Mes",
        "exp_ano": "📅 Exportar Año",
        "baixar": "Descargar",
        "buscar": "🔍 Buscar:",
        "todos": "Todos",
        "semana": "Semana:",
        "agendar": "📅 AGENDAR",
        "backup": "Backup",
        "backup2": "Backup 2",
        "stats": "📊 {nome}: {total} reuniones.",
        "flash_m": "Flash Mañana",
        "resp_m": "Responsable Mañana",
        "resp_t": "Responsable Tarde",
        "tipo_t": "Tipo Tarde/DOR",
        "mes_col": "Mes",
        "dias": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
        "meses": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
        "ferias_tit": "🌴 Vacaciones",
        "reg_periodo": "Registrar",
        "gerenciar_f": "⚙️ Mis Vacaciones",
        "colaborador": "Colaborador:",
        "usuario_log": "Tu Usuario:",
        "dt_inicio": "Inicio:",
        "dt_fim": "Fin:",
        "obs": "Obs:",
        "btn_salvar": "💾 Guardar",
        "grade_tit": "Disponibilidad",
        "sel_mes": "Mes:",
        "sel_ano": "Año:",
        "filtro_equipe": "Equipo:",
        "log_tit": "📋 Próximas Vacaciones",
        "err_user": "Informa usuario.",
        "err_data": "Fecha inválida.",
        "err_conflito": "❌ Conflicto con {nome}.",
        "sucesso": "✅ ¡Registrado!",
        "sucesso_del": "✅ ¡Eliminado!",
        "livre": "Libre",
        "dias_semana_curto": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    }
}

if "lang" not in st.session_state: st.session_state.lang = "PT"
t = I18N[st.session_state.lang]

# --- LÓGICA DE ESCALA (Simplificada para o exemplo) ---
def gerar_escala_balanceada(nomes):
    dias_range = pd.date_range(datetime(2026, 1, 1), datetime(2026, 12, 31), freq='B')
    escala = []
    for dia in dias_range:
        escala.append({
            "Semana": dia.isocalendar()[1], "Data": dia.strftime("%d/%m/%Y"), 
            "Dia": t["dias"][dia.weekday()], "Reunião": t["flash_m"], 
            "Apresentador": random.choice(nomes), "Backup": "Backup", "Backup2": "Backup2", "BackupOculto": "Oculto",
            "Link": "https://outlook.office.com"
        })
    return pd.DataFrame(escala)

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
                if st.form_submit_button(t["acessar"]):
                    if u == "MMD-Board" and p == "@MMD123#":
                        st.session_state.logged_in = True
                        st.rerun()
                    else: st.error("Erro")
        return False
    return True

if check_login():
    tab_escala, tab_ferias = st.tabs(["📅 Escalas", "🌴 " + t["ferias_tit"]])

    with tab_escala:
        st.title(t["titulo"])
        # Conteúdo da escala...
        st.write("Conteúdo da Escala aqui.")

    with tab_ferias:
        st.title(t["ferias_tit"])
        sh = conectar_google_sheets()
        if sh:
            ws = sh.worksheet("DB_FERIAS")
            raw_data = ws.get_all_records()
            df_base = pd.DataFrame(raw_data) if raw_data else pd.DataFrame(columns=["Nome", "Data Início", "Data Final", "Equipe", "Obs", "Data Registro", "Usuário Logado", "ID"])

            # Tratamento de datas para o sistema
            hoje_dt = datetime.now().date()
            if not df_base.empty:
                df_base['Data Final Obj'] = pd.to_datetime(df_base['Data Final'], dayfirst=True, errors='coerce').dt.date
                df_ativas = df_base[df_base['Data Final Obj'] >= hoje_dt].copy()
            else:
                df_ativas = df_base.copy()

            col_form, col_grade = st.columns([1, 2])
            
            with col_form:
                st.subheader(t["reg_periodo"])
                with st.form("form_ferias", clear_on_submit=True):
                    nome_sel = st.selectbox(t["colaborador"], sorted(list(PESSOA_PARA_TORRE.keys())))
                    user_login = st.text_input(t["usuario_log"]).strip().upper()
                    d_ini, d_fim = st.date_input(t["dt_inicio"]), st.date_input(t["dt_fim"])
                    obs_f = st.text_input(t["obs"], value=f"Férias {d_ini.year}")
                    
                    if st.form_submit_button(t["btn_salvar"]):
                        if not user_login: st.error(t["err_user"])
                        elif d_ini > d_fim: st.error(t["err_data"])
                        else:
                            novo_id = datetime.now().strftime("%Y%m%d%H%M%S")
                            ws.append_row([nome_sel, d_ini.strftime("%d/%m/%Y"), d_fim.strftime("%d/%m/%Y"), PESSOA_PARA_TORRE[nome_sel], obs_f, datetime.now().strftime("%d/%m/%Y %H:%M:%S"), user_login, novo_id])
                            st.success(t["sucesso"])
                            st.rerun()

                st.divider()
                # --- GERENCIAMENTO VISUAL (Sem precisar do ID) ---
                st.subheader(t["gerenciar_f"])
                filtro_u = st.text_input("Digite seu Login para editar/excluir:", help="Ex: BRAQUINOLI").strip().upper()
                
                if filtro_u:
                    # Filtra os dados da planilha pelo usuário logado
                    minhas_ferias = df_base[df_base['Usuário Logado'].astype(str).str.upper() == filtro_u]
                    
                    if not minhas_ferias.empty:
                        for _, row in minhas_ferias.iterrows():
                            # Criamos um "card" visual para cada registro de férias dele
                            with st.expander(f"📅 {row['Data Início']} até {row['Data Final']}"):
                                st.write(f"**Colaborador:** {row['Nome']}")
                                st.write(f"**Obs:** {row['Obs']}")
                                
                                # Botão de excluir específico para este ID (escondido)
                                if st.button(f"Excluir este período", key=f"btn_del_{row['ID']}"):
                                    # Lógica de exclusão usando a coluna ID (Coluna H = 8)
                                    col_ids = ws.col_values(8)
                                    try:
                                        linha_para_deletar = col_ids.index(str(row['ID'])) + 1
                                        ws.delete_rows(linha_para_deletar)
                                        st.success(t["sucesso_del"])
                                        st.rerun()
                                    except ValueError:
                                        st.error("Erro ao localizar registro.")
                    else:
                        st.info("Nenhum registro encontrado para este usuário.")

            with col_grade:
                st.subheader(t["grade_tit"])
                # Grid do calendário... (mesma lógica anterior)
                st.write("Calendário de Disponibilidade aqui.")

            st.divider()
            st.subheader(t["log_tit"])
            if not df_ativas.empty:
                st.dataframe(df_ativas[["Nome", "Data Início", "Data Final", "Equipe", "Obs"]], use_container_width=True, hide_index=True)
