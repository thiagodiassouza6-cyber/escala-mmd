import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import streamlit.components.v1 as components
import io
import random

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Portal de Escalas", layout="wide")

# --- DICIONÁRIO DE TRADUÇÃO ---
I18N = {
    "PT": {
        "titulo": "🚀 MMD | Portal de Escalas 2026",
        "login_tit": "Portal de Escalas MMD",
        "usuario": "Usuário",
        "senha": "Senha",
        "acessar": "Acessar Painel",
        "acessibilidade": "Ativar Acessibilidade",
        "roteiro_ter": "📝 Roteiro Terça: Práticas + Iniciativas",
        "roteiro_qui": "📝 Roteiro Quinta: Lead Time + SLA",
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
        "resp_m": "Responsável Manhã",
        "resp_t": "Responsável Tarde",
        "tipo_t": "Tipo Tarde/DOR",
        "mes_col": "Mês"
    },
    "ES": {
        "titulo": "🚀 MMD | Portal de Escalas 2026",
        "login_tit": "Portal de Escalas MMD",
        "usuario": "Usuario",
        "senha": "Contraseña",
        "acessar": "Acceder al Panel",
        "acessibilidade": "Activar Accesibilidad",
        "roteiro_ter": "📝 Guion Martes: Prácticas + Iniciativas",
        "roteiro_qui": "📝 Guion Jueves: Lead Time + SLA",
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
        "resp_m": "Responsable Mañana",
        "resp_t": "Responsable Tarde",
        "tipo_t": "Tipo Tarde/DOR",
        "mes_col": "Mes"
    }
}

# --- SELEÇÃO DE IDIOMA ---
if "lang" not in st.session_state:
    st.session_state.lang = "PT"

# Variável de atalho para os textos
t = I18N[st.session_state.lang]

# --- CONSTANTES ---
SHEET_ID = "1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
USER_ACCESS = "MMD-Board"
PASS_ACCESS = "@MMD123#"

MESES_NOMES = {
    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, 
    "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8, 
    "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
}
MESES_REVERSO = {v: k for k, v in MESES_NOMES.items()}

MAPA_REFERENCIA = {
    "Abigail": "Dani", "Amanda": "Mijal", "Anna Laura": "Soledad", 
    "Ariel": "Rafael", "Bianca M.": "Ariel", "Bruna": "Anna Laura", 
    "Bruno": "Bianca M.", "Dani": "Jesus", "Debora": "Bruna", 
    "Diana": "Julia", "Florencia": "Diana", "Gisele": "Thiago", 
    "Honorato": "Bruno", "Jazmin": "Abigail", "Jesus": "Luca", 
    "Julia": "Honorato", "Livia": "Amanda", "Luca": "Jazmin", 
    "Mijal": "Livia", "Rafael": "Florencia", "Renan": "Debora", 
    "Soledad": "Gisele", "Thiago": "Renan"
}

def encontrar_backup_vivo(nome_apresentador, nomes_ativos):
    proximo = MAPA_REFERENCIA.get(nome_apresentador)
    tentativas = 0
    while proximo and proximo not in nomes_ativos and tentativas < len(MAPA_REFERENCIA):
        proximo = MAPA_REFERENCIA.get(proximo)
        tentativas += 1
    return proximo if proximo in nomes_ativos else "Sem Backup Ativo"

# --- LOGIN ---
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

# --- MOTOR DE REGRAS ---
def gerar_escala_balanceada(nomes):
    random.seed(42)
    fila_base = nomes.copy()
    random.shuffle(fila_base)
    nomes_dor = [n for n in nomes if n not in ["Dani", "Rafael"]]
    random.shuffle(nomes_dor)
    cont_total = {n: 0 for n in nomes}
    cont_dor = {n: 0 for n in nomes_dor}
    ano = datetime.now().year
    dias = pd.date_range(datetime(ano, 1, 1), datetime(ano, 12, 31), freq='B')
    escala = []
    
    for dia in dias:
        data_s = dia.strftime("%d/%m/%Y")
        sem = dia.isocalendar()[1]
        d_sem = dia.weekday()
        d_nome = ["Segunda-Feira", "Terça-Feira", "Quarta-Feira", "Quinta-Feira", "Sexta-Feira"][d_sem]
        quem_ja_foi = [e['Apresentador'] for e in escala if e['Semana'] == sem]
        
        candidatos_m = [n for n in fila_base if n not in quem_ja_foi]
        ap_m = min(candidatos_m, key=lambda x: cont_total[x])
        cont_total[ap_m] += 1
        quem_ja_foi.append(ap_m)
        b1_m = encontrar_backup_vivo(ap_m, nomes)
        b2_m = encontrar_backup_vivo(b1_m, nomes)
        
        escala.append({
            "Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": "Flash Manhã",
            "Apresentador": ap_m, "Backup": b1_m, "Backup2": b2_m, "BackupOculto": encontrar_backup_vivo(b2_m, nomes),
            "Link": f"https://outlook.office.com/calendar/0/deeplink/compose?subject=Flash%20Manhã&startdt={dia.strftime('%Y-%m-%d')}T09:45:00"
        })

        tipo_t = "DOR" if d_sem in [1, 3] else "Flash Tarde"
        if tipo_t == "DOR":
            cand_t = [n for n in nomes_dor if n not in quem_ja_foi]
            ap_t = min(cand_t, key=lambda x: cont_dor[x])
            cont_dor[ap_t] += 1
        else:
            cand_t = [n for n in fila_base if n not in quem_ja_foi]
            ap_t = min(cand_t, key=lambda x: cont_total[x])
        
        cont_total[ap_t] += 1
        b1_t = encontrar_backup_vivo(ap_t, nomes)
        b2_t = encontrar_backup_vivo(b1_t, nomes)
        
        escala.append({
            "Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": tipo_t,
            "Apresentador": ap_t, "Backup": b1_t, "Backup2": b2_t, "BackupOculto": encontrar_backup_vivo(b2_t, nomes),
            "Link": f"https://outlook.office.com/calendar/0/deeplink/compose?subject={tipo_t}&startdt={dia.strftime('%Y-%m-%d')}T15:00:00"
        })
    return pd.DataFrame(escala)

# --- EXCEL ---
def exportar_excel_limpo(df_total, mes_nome=None):
    output = io.BytesIO()
    df_c = df_total.copy()
    df_c['dt_obj'] = pd.to_datetime(df_c['Data'], format='%d/%m/%Y')
    df_c['Mês'] = df_c['dt_obj'].dt.month.map(MESES_REVERSO)
    
    m = df_c[df_c['Reunião'] == 'Flash Manhã'][['Mês', 'Data', 'Dia', 'Apresentador', 'Backup']].rename(columns={'Apresentador':t['resp_m'], 'Backup':t['backup'] + ' M'})
    t_df = df_c[df_c['Reunião'].isin(['Flash Tarde', 'DOR'])][['Data', 'Apresentador', 'Backup', 'Reunião']].rename(columns={'Apresentador':t['resp_t'], 'Backup':t['backup'] + ' T', 'Reunião':t['tipo_t']})
    
    df_f = pd.merge(m, t_df, on='Data', how='outer').fillna("")
    df_f['dt_sort'] = pd.to_datetime(df_f['Data'], format='%d/%m/%Y')
    df_f = df_f.sort_values('dt_sort')
    if mes_nome: df_f = df_f[df_f['Mês'] == mes_nome]

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Escala')
        h_fmt = workbook.add_format({'bold': True, 'bg_color': '#ff4b4b', 'font_color': 'white', 'border': 1, 'align': 'center'})
        m_fmt = workbook.add_format({'bold': True, 'bg_color': '#A6A6A6', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        c_fmt = workbook.add_format({'border': 1, 'align': 'center'})
        
        col_list = ['Data', 'Dia', t['resp_m'], t['backup'] + ' M', t['tipo_t'], t['resp_t'], t['backup'] + ' T']
        for idx, col_n in enumerate(col_list):
            worksheet.write(0, idx, col_n, h_fmt)
            worksheet.set_column(idx, idx, 20)

        row_idx = 1
        mes_atual = ""
        for _, row in df_f.iterrows():
            if row['Mês'] != mes_atual:
                mes_atual = row['Mês']
                worksheet.merge_range(row_idx, 0, row_idx, 6, mes_atual.upper(), m_fmt)
                row_idx += 1
            for col_idx, col_name in enumerate(col_list):
                worksheet.write(row_idx, col_idx, row[col_name] if col_name in row else "", c_fmt)
            row_idx += 1
    return output.getvalue()

# --- CARDS ---
def renderizar_card(row):
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; min-height: 220px; margin-bottom: 10px; color: #333;">
        <b style="font-size: 14px; color: #555;">{row['Reunião']}</b><br><br>
        <span style="font-size: 18px; font-weight: bold; color: #111;">🏆 {row['Apresentador']}</span><br><br>
        <span style="font-size: 13px; color: #444;">{t['backup']}: {row['Backup']}</span><br>
        <span title="{t['backup_oculto']}: {row['BackupOculto']}" style="font-size: 13px; color: #444; cursor: help;">{t['backup2']}: {row['Backup2']}</span>
        <div style="margin-top: 15px;">
            <a href="{row['Link']}" target="_blank" style="display: block; text-decoration: none; color: white; background-color: #0078d4; padding: 8px; border-radius: 5px; font-size: 11px; text-align: center; font-weight: bold;">{t['agendar']}</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- EXECUÇÃO ---
if check_login():
    # BARRA LATERAL - SELETOR DE IDIOMA
    st.sidebar.title("🌐 Idioma / Lenguaje")
    lang_opt = st.sidebar.radio("Selecione:", ["🇧🇷 Português", "🇪🇸 Español"], index=0 if st.session_state.lang == "PT" else 1)
    new_lang = "PT" if "Português" in lang_opt else "ES"
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.sidebar.divider()
    if st.sidebar.toggle(t["acessibilidade"], value=False):
        # (Função de acessibilidade injetada aqui se necessário)
        pass
    
    st.sidebar.divider()
    with st.sidebar.expander(t["roteiro_ter"], expanded=True):
        if st.session_state.lang == "PT":
            st.markdown("**Pauta:** Práticas + Iniciativas + Tracker + Work Plan\n- 📑 Lista de presença\n- ⏱ Pergunta Timekeeper\n- 🗓 Escala\n- 📈 Behavior\n- 🎯 Plano de ação\n- ✅ Práticas\n- 📊 NPS\n- 💡 Iniciativas\n- 📉 Tracker\n- 🛠 Work Plan\n- ⚠️ Plano de ação (Issues)\n- 🛡 SHE\n- 🏆 Behavior")
        else:
            st.markdown("**Pauta:** Prácticas + Iniciativas + Tracker + Work Plan\n- 📑 Lista de asistencia\n- ⏱ Pregunta Timekeeper\n- 🗓 Escala de horarios\n- 📈 Comportamiento\n- 🎯 Plan de acción\n- ✅ Prácticas\n- 📊 NPS\n- 💡 Iniciativas\n- 📉 Tracker\n- 🛠 Work Plan\n- ⚠️ Issues y priorización\n- 🛡 SHE\n- 🏆 Reconocimientos")

    with st.sidebar.expander(t["roteiro_qui"], expanded=True):
        if st.session_state.lang == "PT":
            st.markdown("**Pauta:** Lead Time e SLA + FTR + CATS/BH + Workplan\n- 📑 Lista de presença\n- ⏱ Pergunta Timekeeper\n- 🗓 Escala\n- 📈 Behavior\n- 🎯 Plano de ação\n- 🕒 Lead Time\n- ✅ FTR\n- 📁 Cats+BH\n- 🛠 Work Plan\n- ⚠️ Issues\n- 📍 Plano de ação\n- 🛡 SHE\n- 🏆 Behavior")
        else:
            st.markdown("**Pauta:** Lead Time y SLA + FTR + CATS/BH + Workplan\n- 📑 Lista de asistencia\n- ⏱ Pregunta Timekeeper\n- 🗓 Escala de horarios\n- 📈 Comportamiento\n- 🎯 Plan de acción\n- 🕒 Lead Time\n- ✅ FTR\n- 📁 Cats+BH\n- 🛠 Work Plan\n- ⚠️ Issues\n- 📍 Plan de acción\n- 🛡 SHE\n- 🏆 Reconocimientos")

    try:
        df_csv = pd.read_csv(SHEET_URL)
        nomes = sorted([n for n in df_csv['Funcionario'].dropna().unique() if n not in ["Faiha", "Sonia", "Enrique", "Bianca S."]])
    except: nomes = list(MAPA_REFERENCIA.keys())

    df_total = gerar_escala_balanceada(nomes)
    st.title(t["titulo"])

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        with st.expander(t["exp_mes"]):
            m_sel = st.selectbox(t["mes_col"] + ":", list(MESES_NOMES.keys()))
            st.download_button(f"{t['baixar']} {m_sel}", exportar_excel_limpo(df_total, m_sel), f"Escala_{m_sel}.xlsx", use_container_width=True)
    with col_e2:
        with st.expander(t["exp_ano"]):
            st.download_button(t["baixar"] + " Ano Completo", exportar_excel_limpo(df_total), "Escala_Anual.xlsx", use_container_width=True)

    st.divider()
    busca = st.selectbox(t["buscar"], [t["todos"]] + nomes)
    if busca != t["todos"]:
        df_b = df_total[df_total["Apresentador"] == busca].copy()
        total_ap = len(df_b)
        total_dor = len(df_b[df_b["Reunião"] == "DOR"])
        st.info(t["stats"].format(nome=busca, total=total_ap, dor=total_dor))
        
        st.dataframe(
            df_b[["Data", "Dia", "Reunião", "Backup", "Backup2", "Link"]], 
            column_config={
                "Link": st.column_config.LinkColumn(t["agendar"], display_text=t["agendar"], width="small")
            }, 
            use_container_width=True, hide_index=True
        )

    st.divider()
    s_idx = st.select_slider(t["semana"], options=sorted(df_total["Semana"].unique()), value=datetime.now().isocalendar()[1])
    df_s = df_total[df_total["Semana"] == s_idx]
    for dt, gp in df_s.groupby("Data", sort=False):
        st.markdown(f"**{gp['Dia'].iloc[0]} - {dt}**")
        cols = st.columns(len(gp))
        for i, (_, r) in enumerate(gp.iterrows()):
            with cols[i]: renderizar_card(r)
