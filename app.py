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
        "err_conflito": "❌ Erro: {nome} da equipe {equipe} já possui férias neste período.",
        "sucesso": "✅ Férias registradas!",
        "livre": "Livre",
        "dias_semana_curto": ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"],
        "msg_ferias": "🏖️ EM FÉRIAS - Acionar Backup"
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
        "err_data": "La fecha de inicio no pode ser maior que a data de finalización.",
        "err_conflito": "❌ Error: {nome} del equipo {equipe} ya tiene vacaciones en este periodo.",
        "sucesso": "✅ ¡Vacaciones registradas!",
        "livre": "Libre",
        "dias_semana_curto": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
        "msg_ferias": "🏖️ EN VACACIONES - Contactar Backup"
    }
}

if "lang" not in st.session_state: st.session_state.lang = "PT"
t = I18N[st.session_state.lang]

# --- ACESSIBILIDADE ---
def injetar_leitor_acessibilidade(lang_code):
    components.html(f"""
        <script>
            const synth = window.speechSynthesis;
            let ultimoTexto = "";
            function falar(texto) {{
                if (!texto || texto === ultimoTexto) return;
                synth.cancel(); 
                const ut = new SpeechSynthesisUtterance(texto);
                ut.lang = '{lang_code}';
                ut.rate = 1.1;
                ultimoTexto = texto;
                synth.speak(ut);
                setTimeout(() => {{ ultimoTexto = ""; }}, 800);
            }}
            const docAlvo = window.parent.document;
            docAlvo.addEventListener('mouseover', (e) => {{
                const el = e.target;
                const textoParaLer = (el.innerText || el.textContent).trim();
                if (textoParaLer.length > 0 && !textoParaLer.includes("http")) {{
                    falar(textoParaLer);
                }}
            }}, true);
            docAlvo.addEventListener('mouseout', () => {{ synth.cancel(); }}, true);
        </script>
    """, height=0, width=0)

# --- MOTOR DE REGRAS ESCALA ---
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

def exportar_excel_limpo(df_total, mes_nome=None):
    output = io.BytesIO()
    df_c = df_total.copy()
    df_c['dt_obj'] = pd.to_datetime(df_c['Data'], format='%d/%m/%Y')
    meses_map = {i+1: nome for i, nome in enumerate(t["meses"])}
    df_c['Mês'] = df_c['dt_obj'].dt.month.map(meses_map)
    
    m = df_c[df_c['Reunião'] == t['flash_m']][['Mês', 'Data', 'Dia', 'Apresentador', 'Backup']].rename(columns={'Apresentador':t['resp_m'], 'Backup':t['backup'] + ' M'})
    t_df = df_c[df_c['Reunião'].isin(['Flash Tarde', 'DOR'])][['Data', 'Apresentador', 'Backup', 'Reunião']].rename(columns={'Apresentador':t['resp_t'], 'Backup':t['backup'] + ' T', 'Reunião':t['tipo_t']})
    
    df_f = pd.merge(m, t_df, on='Data', how='outer').fillna("")
    df_f['dt_sort'] = pd.to_datetime(df_f['Data'], format='%d/%m/%Y')
    df_f = df_f.sort_values('dt_sort')
    if mes_nome: df_f = df_f[df_f['Mês'] == mes_nome]

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook, worksheet = writer.book, writer.book.add_worksheet('Escala')
        h_fmt = workbook.add_format({'bold': True, 'bg_color': '#ff4b4b', 'font_color': 'white', 'border': 1, 'align': 'center'})
        m_fmt = workbook.add_format({'bold': True, 'bg_color': '#A6A6A6', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        c_fmt = workbook.add_format({'border': 1, 'align': 'center'})
        cols = ['Data', 'Dia', t['resp_m'], t['backup'] + ' M', t['tipo_t'], t['resp_t'], t['backup'] + ' T']
        for i, col in enumerate(cols): 
            worksheet.write(0, i, col, h_fmt)
            worksheet.set_column(i, i, 18)
        row_idx, mes_atual = 1, ""
        for _, row in df_f.iterrows():
            if row['Mês'] != mes_atual:
                mes_atual = row['Mês']
                worksheet.merge_range(row_idx, 0, row_idx, 6, mes_atual.upper(), m_fmt)
                row_idx += 1
            for j, c in enumerate(cols): worksheet.write(row_idx, j, row[c] if c in row else "", c_fmt)
            row_idx += 1
    return output.getvalue()

def renderizar_card(row, df_ferias_check=None):
    apresentador = row['Apresentador']
    data_reuniao = datetime.strptime(row['Data'], "%d/%m/%Y").date()
    esta_de_ferias = False

    # Lógica de Linkagem entre Escalas e Férias
    if df_ferias_check is not None and not df_ferias_check.empty:
        try:
            df_v = df_ferias_check.copy()
            df_v['Data Início'] = pd.to_datetime(df_v['Data Início'], dayfirst=True).dt.date
            df_v['Data Final'] = pd.to_datetime(df_v['Data Final'], dayfirst=True).dt.date
            
            # Verifica se o apresentador está de férias na data desta reunião
            ferias_ativa = df_v[(df_v['Nome'] == apresentador) & 
                                (data_reuniao >= df_v['Data Início']) & 
                                (data_reuniao <= df_v['Data Final'])]
            
            if not ferias_ativa.empty:
                esta_de_ferias = True
        except:
            esta_de_ferias = False

    # Define o visual do card dependendo do status de férias
    if esta_de_ferias:
        cor_borda = "#f1c40f" # Amarelo para atenção
        status_html = f"""<div style="margin-top:15px; background-color:#fff3cd; color:#856404; padding:8px; border-radius:5px; font-size:11px; text-align:center; font-weight:bold; border: 1px solid #ffeeba;">{t['msg_ferias']}</div>"""
    else:
        cor_borda = "#ff4b4b" # Vermelho padrão
        status_html = f"""<div style="margin-top:15px;"><a href="{row['Link']}" target="_blank" style="display:block;text-decoration:none;color:white;background-color:#0078d4;padding:8px;border-radius:5px;font-size:11px;text-align:center;font-weight:bold;">{t['agendar']}</a></div>"""

    st.markdown(f"""
    <div style="background-color:#f0f2f6;padding:15px;border-radius:10px;border-left:5px solid {cor_borda};min-height:220px;color:#333;margin-bottom:10px;">
        <b style="font-size:14px;color:#555;">{row['Reunião']}</b><br><br>
        <span style="font-size:18px;font-weight:bold;color:#111;">🏆 {apresentador}</span><br><br>
        <span style="font-size:13px;color:#444;">{t['backup']}: {row['Backup']}</span><br>
        <span title="{t['backup_oculto']}: {row['BackupOculto']}" style="font-size:13px;color:#444;cursor:help;">{t['backup2']}: {row['Backup2']}</span>
        {status_html}
    </div>
    """, unsafe_allow_html=True)

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

# --- EXECUÇÃO ---
if check_login():
    # Sidebar
    st.sidebar.title("🌐 Idioma / Lenguaje")
    lang_opt = st.sidebar.radio("Selecione:", ["🇧🇷 Português", "🇪🇸 Español"], index=0 if st.session_state.lang == "PT" else 1)
    if ("Português" in lang_opt and st.session_state.lang == "ES") or ("Español" in lang_opt and st.session_state.lang == "PT"):
        st.session_state.lang = "PT" if "Português" in lang_opt else "ES"
        st.rerun()

    if st.sidebar.toggle(t["acessibilidade"], value=False):
        injetar_leitor_acessibilidade(t["lang_code"])

    st.sidebar.divider()
    with st.sidebar.expander(t["estrutura_tit"]):
        for torre, membros in TORRES.items(): st.markdown(f"**{torre}:** {', '.join(membros)}")
    
    # --- ROTEIROS ---
    with st.sidebar.expander(t["roteiro_ter"]):
        st.markdown("""
        **Terça-feira: Práticas + Iniciativas + Tracker + Work Plan**
        1.  Lista de presença
        2.  Pergunta Timekeeper – E TODOS SE SINTAM A VONTADE PARA SER CHALLENGE E ENGAGE
        3.  Escala de horário
        4.  Behavior (checa as notas da reunião anterior)
        5.  Plano de ação (verificar as ações do dia)
        6.  Práticas (perguntar para cada responsável)
        7.  NPS
        8.  Iniciativas (cada um comenta sua iniciativa)
        9.  Tracker
        10. Work Plan
        11. Plano de ação (perguntar issues e priorizar)
        12. SHE
        13. Behavior (Reconhecimento e notas)
        """)

    with st.sidebar.expander(t["roteiro_qui"]):
        st.markdown("""
        **Quinta-feira: Lead Time e SLA + FTR + CATS/BH + Workplan**
        1.  Lista de presença
        2.  Pergunta Timekeeper, Challenger e Engage
        3.  Escala de horário
        4.  Behavior (checa as notas da reunião anterior)
        5.  Plano de ação (verificar as ações do dia)
        6.  Lead Time (Cristian ou Barreto, Bianca ou Renan)
        7.  FTR (Bianca ou Renan)
        8.  Cats+BH (Amanda)
        9.  Work Plan
        10. Issues
        11. Plano de ação (priorizar Alta, Média e Baixa)
        12. SHE
        13. Behavior (Reconhecimento e notas)
        """)

    tab_escala, tab_ferias = st.tabs(["📅 Escalas", "🌴 " + ("Férias" if st.session_state.lang == "PT" else "Vacaciones")])

    with tab_escala:
        st.title(t["titulo"])
        nomes = sorted(list(MAPA_REFERENCIA.keys()))
        df_total = gerar_escala_balanceada(nomes)
        
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            with st.expander(t["exp_mes"]):
                m_sel = st.selectbox(t["mes_col"] + ":", t["meses"])
                st.download_button(f"{t['baixar']} {m_sel}", exportar_excel_limpo(df_total, m_sel), f"Escala_{m_sel}.xlsx", use_container_width=True)
        with col_e2:
            with st.expander(t["exp_ano"]):
                st.download_button(t["baixar"] + " Escala Anual", exportar_excel_limpo(df_total), "Escala_Anual.xlsx", use_container_width=True)

        st.divider()
        busca = st.selectbox(t["buscar"], [t["todos"]] + nomes)
        
        # Carrega dados de férias para linkagem nos filtros e cards
        sh = conectar_google_sheets()
        df_f_check = pd.DataFrame()
        if sh:
            try:
                ws_f = sh.worksheet("DB_FERIAS")
                df_f_check = pd.DataFrame(ws_f.get_all_records())
            except: pass

        if busca != t["todos"]:
            df_b = df_total[df_total["Apresentador"] == busca].copy()
            st.info(t["stats"].format(nome=busca, total=len(df_b), dor=len(df_b[df_b["Reunião"] == "DOR"])))
            st.dataframe(df_b[["Data", "Dia", "Reunião", "Backup", "Backup2", "Link"]], column_config={"Link": st.column_config.LinkColumn(t["agendar"], display_text=t["agendar"])}, use_container_width=True, hide_index=True)

        st.divider()
        s_idx = st.select_slider(t["semana"], options=sorted(df_total["Semana"].unique()), value=datetime.now().isocalendar()[1])
        df_s = df_total[df_total["Semana"] == s_idx]
        
        for dt, gp in df_s.groupby("Data", sort=False):
            st.markdown(f"**{gp['Dia'].iloc[0]} - {dt}**")
            cols = st.columns(len(gp))
            for i, (_, r) in enumerate(gp.iterrows()):
                with cols[i]: renderizar_card(r, df_f_check)

    with tab_ferias:
        st.title(t["ferias_tit"])
        if sh:
            try:
                ws = sh.worksheet("DB_FERIAS")
                df_ferias = pd.DataFrame(ws.get_all_records())
            except: df_ferias = pd.DataFrame()

            col_form, col_grade = st.columns([1, 2])
            with col_form:
                st.subheader(t["reg_periodo"])
                with st.form("form_ferias", clear_on_submit=True):
                    nome_sel = st.selectbox(t["colaborador"], sorted(list(PESSOA_PARA_TORRE.keys())))
                    user_login = st.text_input(t["usuario_log"])
                    d_ini, d_fim = st.date_input(t["dt_inicio"]), st.date_input(t["dt_fim"])
                    obs_f = st.text_input(t["obs"], value=f"Férias {d_ini.year}")
                    if st.form_submit_button(t["btn_salvar"]):
                        if not user_login: st.error(t["err_user"])
                        elif d_ini > d_fim: st.error(t["err_data"])
                        else:
                            torre_sel = PESSOA_PARA_TORRE.get(nome_sel)
                            conflito = False
                            if not df_ferias.empty:
                                df_check = df_ferias.copy()
                                df_check['Data Início'] = pd.to_datetime(df_check['Data Início'], dayfirst=True).dt.date
                                df_check['Data Final'] = pd.to_datetime(df_check['Data Final'], dayfirst=True).dt.date
                                overlaps = df_check[(df_check['Equipe'] == torre_sel) & (d_ini <= df_check['Data Final']) & (d_fim >= df_check['Data Início'])]
                                if not overlaps.empty:
                                    conflito = True
                                    st.error(t["err_conflito"].format(nome=overlaps.iloc[0]['Nome'], equipe=torre_sel))
                            
                            if not conflito:
                                ws.append_row([nome_sel, d_ini.strftime("%d/%m/%Y"), d_fim.strftime("%d/%m/%Y"), torre_sel, obs_f, datetime.now().strftime("%d/%m/%Y %H:%M:%S"), user_login])
                                st.success(t["sucesso"])
                                st.rerun()

            with col_grade:
                st.subheader(t["grade_tit"])
                c1, c2, c3 = st.columns(3)
                with c1: m_f_sel = st.selectbox(t["sel_mes"], t["meses"], index=datetime.now().month-1, key="mes_f")
                with c2: a_f_sel = st.selectbox(t["sel_ano"], [2026, 2027, 2028, 2029], key="ano_f")
                with c3: eq_sel = st.selectbox(t["filtro_equipe"], sorted(list(TORRES.keys())), key="eq_f")
                m_f_idx = t["meses"].index(m_f_sel) + 1
                st.caption(t["viz_ocupacao"].format(equipe=eq_sel))
                
                cols_h = st.columns(7)
                for i, d_n in enumerate(t["dias_semana_curto"]): cols_h[i].markdown(f"<p style='text-align:center;font-weight:bold;color:gray;'>{d_n}</p>", unsafe_allow_html=True)
                cal = calendar.monthcalendar(a_f_sel, m_f_idx)
                for week in cal:
                    cols_g = st.columns(7)
                    for i, day in enumerate(week):
                        if day == 0: cols_g[i].write("")
                        else:
                            data_c = datetime(a_f_sel, m_f_idx, day).date()
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
                df_log['DT_INI'] = pd.to_datetime(df_log['Data Início'], dayfirst=True)
                df_log = df_log.sort_values('DT_INI').drop(columns=['DT_INI'])
                st.dataframe(df_log, use_container_width=True, hide_index=True)
