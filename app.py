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
st.set_page_config(page_title="MMD | Portal de Escalas", layout="wide")

# --- CONEXÃO COM GOOGLE SHEETS (PARA ABA FÉRIAS) ---
def conectar_google_sheets():
    try:
        creds = st.secrets["gcp_service_account"]
        client = gspread.service_account_from_dict(dict(creds))
        sh = client.open("Escala MMD")
        return sh
    except Exception as e:
        return None

# --- ESTRUTURA DE TIMES (PARA LÓGICA DE FÉRIAS) ---
TORRES = {
    "Indireto Brasil": ["Debora", "Dani", "Abigail", "Luca", "Bruno", "Thiago", "Anna Laura"],
    "Material Fert Brasil": ["Amanda", "Sabrina", "Douglas"],
    "CRM": ["Julia", "Bruna", "Renan"],
    "Material Direto Brasil": ["Livia", "Rafael"],
    "Material Direto Latam": ["Ariel", "Cristian", "Enrique", "Sonia", "Gisele"],
    "Fert Latam": ["Jazmin", "Florencia", "Jesus", "Bianca", "Soledad", "Mijal", "Silvana", "Andrea", "Honorato", "Faiha"]
}
PESSOA_PARA_TORRE = {p: t for t, pessoas in TORRES.items() for p in pessoas}

# --- DICIONÁRIO DE TRADUÇÃO (SEU CÓDIGO ORIGINAL) ---
I18N = {
    "PT": {
        "lang_code": "pt-BR",
        "titulo": "🚀 MMD | Portal de Escalas 2026",
        "login_tit": "Portal de Escalas MMD",
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
        "reuniao": "Reunião",
        "flash_m": "Flash Manhã",
        "resp_m": "Responsável Manhã",
        "resp_t": "Responsável Tarde",
        "tipo_t": "Tipo Tarde/DOR",
        "mes_col": "Mês",
        "dias": ["Segunda-Feira", "Terça-Feira", "Quarta-Feira", "Quinta-Feira", "Sexta-Feira"],
        "meses": ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"],
        "pauta": {
            "lista": "📑 Lista de presença", "tk": "⏱ Timekeeper", "escala": "🗓 Escala", "behavior": "📈 Behavior",
            "plan": "🎯 Plano de ação", "prac": "✅ Práticas", "nps": "📊 NPS", "ini": "💡 Iniciativas",
            "track": "📉 Tracker", "work": "🛠 Work Plan", "issue": "⚠️ Issues", "she": "🛡 SHE",
            "lt": "🕒 Lead Time", "ftr": "✅ FTR", "cats": "📁 Cats+BH"
        }
    },
    "ES": {
        "lang_code": "es-ES",
        "titulo": "🚀 MMD | Portal de Escalas 2026",
        "login_tit": "Portal de Escalas MMD",
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
        "reuniao": "Reunión",
        "flash_m": "Flash Mañana",
        "resp_m": "Responsable Mañana",
        "resp_t": "Responsable Tarde",
        "tipo_t": "Tipo Tarde/DOR",
        "mes_col": "Mes",
        "dias": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
        "meses": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
        "pauta": {
            "lista": "📑 Lista de presencia", "tk": "⏱ Timekeeper", "escala": "🗓 Escala Horario", "behavior": "📈 Behavior",
            "plan": "🎯 Plan de accion", "prac": "✅ Practicas", "nps": "📊 NPS", "ini": "💡 Iniciativas",
            "track": "📉 Tracker", "work": "🛠 Work Plan", "issue": "⚠️ Issues", "she": "🛡 SHE",
            "lt": "🕒 Lead Time", "ftr": "✅ FTR", "cats": "📁 Cats+BH"
        }
    }
}

if "lang" not in st.session_state:
    st.session_state.lang = "PT"

t = I18N[st.session_state.lang]

# --- ACESSIBILIDADE (SEU CÓDIGO ORIGINAL) ---
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

# --- MOTOR DE REGRAS (SEU CÓDIGO ORIGINAL) ---
SHEET_ID = "1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
USER_ACCESS = "MMD-Board"
PASS_ACCESS = "@MMD123#"

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
    tentativas = 0
    while proximo and proximo not in nomes_ativos and tentativas < len(MAPA_REFERENCIA):
        proximo = MAPA_REFERENCIA.get(proximo)
        tentativas += 1
    return proximo if proximo in nomes_ativos else "Sem Backup Ativo"

def check_login():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown(f"<h2 style='text-align: center;'>{t['login_tit']}</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            with st.form("login"):
                u = st.text_input(t["usuario"]).strip()
                p = st.text_input(t["senha"], type="password").strip()
                if st.form_submit_button(t["acessar"], use_container_width=True):
                    if u == USER_ACCESS and p == PASS_ACCESS:
                        st.session_state.logged_in = True
                        st.rerun()
                    else: st.error("Acesso negado / Acceso denegado")
        return False
    return True

def gerar_escala_balanceada(nomes):
    random.seed(42)
    fila_base = nomes.copy()
    random.shuffle(fila_base)
    nomes_dor = [n for n in nomes if n not in ["Dani", "Rafael"]]
    random.shuffle(nomes_dor)
    cont_total = {n: 0 for n in nomes}
    cont_dor = {n: 0 for n in nomes_dor}
    dias_range = pd.date_range(datetime(2026, 1, 1), datetime(2026, 12, 31), freq='B')
    escala = []
    
    for dia in dias_range:
        data_s, sem, d_sem = dia.strftime("%d/%m/%Y"), dia.isocalendar()[1], dia.weekday()
        d_nome = t["dias"][d_sem]
        quem_ja_foi = [e['Apresentador'] for e in escala if e['Semana'] == sem]
        
        ap_m = min([n for n in fila_base if n not in quem_ja_foi], key=lambda x: cont_total[x])
        cont_total[ap_m] += 1
        quem_ja_foi.append(ap_m)
        escala.append({
            "Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": t["flash_m"],
            "Apresentador": ap_m, "Backup": encontrar_backup_vivo(ap_m, nomes),
            "Backup2": encontrar_backup_vivo(encontrar_backup_vivo(ap_m, nomes), nomes),
            "BackupOculto": encontrar_backup_vivo(encontrar_backup_vivo(encontrar_backup_vivo(ap_m, nomes), nomes), nomes),
            "Link": f"https://outlook.office.com/calendar/0/deeplink/compose?subject={urllib.parse.quote(t['flash_m'])}&startdt={dia.strftime('%Y-%m-%d')}T09:45:00"
        })

        tipo_t = "DOR" if d_sem in [1, 3] else "Flash Tarde"
        cand_t = [n for n in (nomes_dor if tipo_t == "DOR" else fila_base) if n not in quem_ja_foi]
        ap_t = min(cand_t, key=lambda x: cont_dor[x] if tipo_t == "DOR" else cont_total[x])
        if tipo_t == "DOR": cont_dor[ap_t] += 1
        cont_total[ap_t] += 1
        escala.append({
            "Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": tipo_t,
            "Apresentador": ap_t, "Backup": encontrar_backup_vivo(ap_t, nomes),
            "Backup2": encontrar_backup_vivo(encontrar_backup_vivo(ap_t, nomes), nomes),
            "BackupOculto": encontrar_backup_vivo(encontrar_backup_vivo(encontrar_backup_vivo(ap_t, nomes), nomes), nomes),
            "Link": f"https://outlook.office.com/calendar/0/deeplink/compose?subject={urllib.parse.quote(tipo_t)}&startdt={dia.strftime('%Y-%m-%d')}T15:00:00"
        })
    return pd.DataFrame(escala)

def exportar_excel_limpo(df_total, mes_nome=None):
    output = io.BytesIO()
    df_c = df_total.copy()
    df_c['dt_obj'] = pd.to_datetime(df_c['Data'], format='%d/%m/%Y')
    df_c = df_c.sort_values('dt_obj')
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

def renderizar_card(row):
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; min-height: 220px; margin-bottom: 10px; color: #333;">
        <b style="font-size: 14px; color: #555;">{row['Reunião']}</b><br><br>
        <span style="font-size: 18px; font-weight: bold; color: #111;">🏆 {row['Apresentador']}</span><br><br>
        <span style="font-size: 13px; color: #444;">{t['backup']}: {row['Backup']}</span><br>
        <span title="{t['backup_oculto']}: {row['BackupOculto']}" style="font-size: 13px; color: #444; cursor: help;">{t['backup2']}: {row['Backup2']}</span>
        <div style="margin-top: 15px;"><a href="{row['Link']}" target="_blank" style="display: block; text-decoration: none; color: white; background-color: #0078d4; padding: 8px; border-radius: 5px; font-size: 11px; text-align: center; font-weight: bold;">{t['agendar']}</a></div>
    </div>
    """, unsafe_allow_html=True)

# --- EXECUÇÃO PRINCIPAL ---
if check_login():
    # Sidebar
    st.sidebar.title("🌐 Idioma / Lenguaje")
    lang_opt = st.sidebar.radio("Selecione:", ["🇧🇷 Português", "🇪🇸 Español"], index=0 if st.session_state.lang == "PT" else 1)
    new_lang = "PT" if "Português" in lang_opt else "ES"
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.sidebar.divider()
    if st.sidebar.toggle(t["acessibilidade"], value=False):
        injetar_leitor_acessibilidade(t["lang_code"])
    
    st.sidebar.divider()
    with st.sidebar.expander(t["roteiro_ter"], expanded=False):
        st.markdown(f"**Pauta:** {t['pauta']['prac']} + {t['pauta']['ini']} + {t['pauta']['track']} + {t['pauta']['work']}")
        st.markdown(f"- {t['pauta']['lista']}\n- {t['pauta']['tk']}\n- {t['pauta']['escala']}\n- {t['pauta']['behavior']}\n- {t['pauta']['plan']}\n- {t['pauta']['prac']}\n- {t['pauta']['nps']}\n- {t['pauta']['ini']}\n- {t['pauta']['track']}\n- {t['pauta']['work']}\n- {t['pauta']['plan']} ({t['pauta']['issue']})\n- 🛡 SHE\n- 🏆 Behavior")

    with st.sidebar.expander(t["roteiro_qui"], expanded=False):
        st.markdown(f"**Pauta:** {t['pauta']['lt']} + {t['pauta']['ftr']} + {t['pauta']['cats']} + {t['pauta']['work']}")
        st.markdown(f"- {t['pauta']['lista']}\n- {t['pauta']['tk']}\n- {t['pauta']['escala']}\n- {t['pauta']['behavior']}\n- {t['pauta']['plan']}\n- {t['pauta']['lt']}\n- {t['pauta']['ftr']}\n- {t['pauta']['cats']}\n- {t['pauta']['work']}\n- {t['pauta']['issue']}\n- {t['pauta']['plan']}\n- 🛡 SHE\n- 🏆 Behavior")

    with st.sidebar.expander(t["estrutura_tit"], expanded=False):
        st.markdown("""
        **Indireto Brasil:** Debora, Dani, Abigail, Luca, Bruno, Thiago, Anna Laura
        \n**Material Fert Brasil:** Amanda, Sabrina, Douglas
        \n**CRM:** Julia, Bruna, Renan
        \n**Material Direto Brasil:** Livia, Rafael
        \n**Material Direto Latam:** Ariel, Cristian, Enrique, Sonia, Gisele
        \n**Fert Latam:** Jazmin, Florencia, Jesus, Bianca, Soledad, Mijal, Silvana, Andrea, Honorato, Faiha
        """)

    # --- CRIAÇÃO DAS ABAS ---
    tab_escala, tab_ferias = st.tabs(["📅 Escalas", "🌴 Planejamento de Férias"])

    # --- ABA 1: ESCALAS (TODO SEU CÓDIGO ORIGINAL) ---
    with tab_escala:
        try:
            df_csv = pd.read_csv(SHEET_URL)
            nomes = sorted([n for n in df_csv['Funcionario'].dropna().unique() if n not in ["Faiha", "Sonia", "Enrique", "Bianca S."]])
        except: nomes = sorted(list(MAPA_REFERENCIA.keys()))

        df_total = gerar_escala_balanceada(nomes)
        st.title(t["titulo"])

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            with st.expander(t["exp_mes"]):
                m_sel = st.selectbox(t["mes_col"] + ":", t["meses"])
                st.download_button(f"{t['baixar']} {m_sel}", exportar_excel_limpo(df_total, m_sel), f"Escala_{m_sel}.xlsx", use_container_width=True)
        with col_e2:
            with st.expander(t["exp_ano"]):
                st.download_button(t["baixar"] + f" {t['mes_col']} Completo", exportar_excel_limpo(df_total), "Escala_Anual.xlsx", use_container_width=True)

        st.divider()
        busca = st.selectbox(t["buscar"], [t["todos"]] + nomes)
        if busca != t["todos"]:
            df_b = df_total[df_total["Apresentador"] == busca].copy()
            st.info(t["stats"].format(nome=busca, total=len(df_b), dor=len(df_b[df_b["Reunião"] == "DOR"])))
            st.dataframe(df_b[["Data", "Dia", "Reunião", "Backup", "Backup2", "Link"]], column_config={"Link": st.column_config.LinkColumn(t["agendar"], display_text=t["agendar"], width="small")}, use_container_width=True, hide_index=True)

        st.divider()
        s_idx = st.select_slider(t["semana"], options=sorted(df_total["Semana"].unique()), value=datetime.now().isocalendar()[1])
        df_s = df_total[df_total["Semana"] == s_idx]
        for dt, gp in df_s.groupby("Data", sort=False):
            st.markdown(f"**{gp['Dia'].iloc[0]} - {dt}**")
            cols = st.columns(len(gp))
            for i, (_, r) in enumerate(gp.iterrows()):
                with cols[i]: renderizar_card(r)

    # --- ABA 2: FÉRIAS (LÓGICA NOVA COM GOOGLE SHEETS) ---
    with tab_ferias:
        st.title("🌴 Planejamento de Férias Integrado")
        sh = conectar_google_sheets()
        if sh:
            ws = sh.worksheet("DB_FERIAS")
            df_ferias = pd.DataFrame(ws.get_all_records())

            col_form, col_grade = st.columns([1, 2])
            with col_form:
                st.subheader("Registrar Período")
                with st.form("form_ferias", clear_on_submit=True):
                    # Nomes vêm da lista de torres (que inclui Anna Laura)
                    lista_colaboradores = sorted(list(PESSOA_PARA_TORRE.keys()))
                    nome_sel = st.selectbox("Colaborador:", lista_colaboradores)
                    user_login = st.text_input("Seu Usuário (Obrigatório):")
                    d_ini = st.date_input("Data de Início:")
                    d_fim = st.date_input("Data de Término:")
                    obs_f = st.text_input("Observação:", "Férias 2026")
                    
                    if st.form_submit_button("💾 Salvar no Sheets"):
                        if not user_login:
                            st.error("Por favor, informe o seu usuário.")
                        else:
                            torre_sel = PESSOA_PARA_TORRE.get(nome_sel)
                            # Ordem das colunas: Nome, Data Início, Data Final, Equipe, Observação, Data Registro, Usuário Logado
                            nova_linha = [
                                nome_sel, d_ini.strftime("%d/%m/%Y"), d_fim.strftime("%d/%m/%Y"), 
                                torre_sel, obs_f, datetime.now().strftime("%d/%m/%Y %H:%M:%S"), user_login
                            ]
                            ws.append_row(nova_linha)
                            st.success("Férias registradas com sucesso!")
                            st.rerun()

            with col_grade:
                st.subheader("Grade de Disponibilidade")
                mes_f_sel = st.selectbox("Selecione o Mês:", t["meses"], index=datetime.now().month-1)
                m_idx = t["meses"].index(mes_f_sel) + 1
                
                # Pega a torre de quem está selecionado no formulário para mostrar a grade da equipe dele
                torre_atual = PESSOA_PARA_TORRE.get(nome_sel)
                st.caption(f"Visualizando ocupação para a equipe: **{torre_atual}**")
                
                cal = calendar.monthcalendar(2026, m_idx)
                cols_g = st.columns(7)
                for week in cal:
                    for i, day in enumerate(week):
                        if day == 0:
                            cols_g[i].write("")
                        else:
                            data_c = datetime(2026, m_idx, day)
                            status, cor = "Livre", "#28a745" # Verde
                            
                            if not df_ferias.empty:
                                df_ferias['Data Início'] = pd.to_datetime(df_ferias['Data Início'], dayfirst=True)
                                df_ferias['Data Final'] = pd.to_datetime(df_ferias['Data Final'], dayfirst=True)
                                
                                # Verifica se alguém da mesma equipe está de férias
                                conflito = df_ferias[
                                    (df_ferias['Equipe'] == torre_atual) & 
                                    (data_c >= df_ferias['Data Início']) & 
                                    (data_c <= df_ferias['Data Final'])
                                ]
                                if not conflito.empty:
                                    status, cor = conflito.iloc[0]['Nome'], "#dc3545" # Vermelho
                            
                            cols_g[i].markdown(f"""<div style="background-color:{cor}; color:white; padding:5px; border-radius:5px; text-align:center; margin-bottom:5px;"><small>{day}</small><br><b>{status}</b></div>""", unsafe_allow_html=True)
            
            st.divider()
            st.subheader("📋 Log Geral de Registros")
            st.dataframe(df_ferias.tail(10), use_container_width=True)
