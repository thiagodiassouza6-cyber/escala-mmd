import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import streamlit.components.v1 as components
import io
import random

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Portal de Escalas", layout="wide")

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

# MAPA DE HERANÇA
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

# --- ACESSIBILIDADE ---
def injetar_leitor_acessibilidade():
    components.html("""
        <script>
            const synth = window.speechSynthesis;
            let ultimoTexto = "";
            function falar(texto) {
                if (!texto || texto === ultimoTexto) return;
                synth.cancel(); 
                const ut = new SpeechSynthesisUtterance(texto);
                ut.lang = 'pt-BR';
                ut.rate = 1.1;
                ultimoTexto = texto;
                synth.speak(ut);
                setTimeout(() => { ultimoTexto = ""; }, 800);
            }
            const docAlvo = window.parent.document;
            docAlvo.addEventListener('mouseover', (e) => {
                const el = e.target;
                const textoParaLer = (el.innerText || el.textContent).trim();
                if (textoParaLer.length > 0 && !textoParaLer.includes("http")) {
                    falar(textoParaLer);
                }
            }, true);
            docAlvo.addEventListener('mouseout', () => { synth.cancel(); }, true);
        </script>
    """, height=0, width=0)

# --- LOGIN ---
def check_login():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown("<h2 style='text-align: center;'>Portal de Escalas MMD</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            with st.form("login"):
                u = st.text_input("Usuário").strip()
                p = st.text_input("Senha", type="password").strip()
                if st.form_submit_button("Acessar Painel", use_container_width=True):
                    if u == USER_ACCESS and p == PASS_ACCESS:
                        st.session_state.logged_in = True
                        st.rerun()
                    else: st.error("Acesso negado.")
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
        
        # Flash Manhã
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

        # Tarde
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

# --- EXPORTAÇÃO FORMATO SEGUNDA IMAGEM (MESCLAGEM HORIZONTAL) ---
def exportar_excel_limpo(df_total, mes_nome=None):
    output = io.BytesIO()
    df_c = df_total.copy()
    df_c['dt_obj'] = pd.to_datetime(df_c['Data'], format='%d/%m/%Y')
    df_c['Mês'] = df_c['dt_obj'].dt.month.map(MESES_REVERSO)
    
    m = df_c[df_c['Reunião'] == 'Flash Manhã'][['Mês', 'Data', 'Dia', 'Apresentador', 'Backup']].rename(columns={'Apresentador':'Responsável Manhã', 'Backup':'Backup Manhã'})
    t = df_c[df_c['Reunião'].isin(['Flash Tarde', 'DOR'])][['Data', 'Apresentador', 'Backup', 'Reunião']].rename(columns={'Apresentador':'Responsável Tarde', 'Backup':'Backup Tarde', 'Reunião':'Tipo Tarde/DOR'})
    
    df_f = pd.merge(m, t, on='Data', how='outer').fillna("")
    df_f['dt_sort'] = pd.to_datetime(df_f['Data'], format='%d/%m/%Y')
    df_f = df_f.sort_values('dt_sort')

    if mes_nome:
        df_f = df_f[df_f['Mês'] == mes_nome]

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Escala')
        
        # Formatos
        h_fmt = workbook.add_format({'bold': True, 'bg_color': '#ff4b4b', 'font_color': 'white', 'border': 1, 'align': 'center'})
        m_fmt = workbook.add_format({'bold': True, 'bg_color': '#A6A6A6', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        c_fmt = workbook.add_format({'border': 1, 'align': 'center'})
        
        cols = ['Data', 'Dia', 'Responsável Manhã', 'Backup Manhã', 'Tipo Tarde/DOR', 'Responsável Tarde', 'Backup Tarde']
        for idx, col in enumerate(cols):
            worksheet.write(0, idx, col, h_fmt)
            worksheet.set_column(idx, idx, 20)

        row_idx = 1
        mes_atual = ""
        
        for _, row in df_f.iterrows():
            if row['Mês'] != mes_atual:
                mes_atual = row['Mês']
                # Mescla horizontalmente como na imagem 2
                worksheet.merge_range(row_idx, 0, row_idx, 6, mes_atual.upper(), m_fmt)
                row_idx += 1
            
            for col_idx, col_name in enumerate(cols):
                worksheet.write(row_idx, col_idx, row[col_name], c_fmt)
            row_idx += 1
                
    return output.getvalue()

# --- CARD COM BACKUP 2 VISÍVEL E OCULTO NO HOVER ---
def renderizar_card(row):
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; min-height: 220px; margin-bottom: 10px; color: #333;">
        <b style="font-size: 14px; color: #555;">{row['Reunião']}</b><br><br>
        <span style="font-size: 18px; font-weight: bold; color: #111;">🏆 {row['Apresentador']}</span><br><br>
        <span style="font-size: 13px; color: #444;">🔄 Backup: {row['Backup']}</span><br>
        <span title="Backup Oculto: {row['BackupOculto']}" style="font-size: 13px; color: #444; cursor: help;">🛡️ Backup 2: {row['Backup2']}</span>
        <div style="margin-top: 15px;">
            <a href="{row['Link']}" target="_blank" style="display: block; text-decoration: none; color: white; background-color: #0078d4; padding: 8px; border-radius: 5px; font-size: 11px; text-align: center; font-weight: bold;">📅 AGENDAR</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- EXECUÇÃO ---
if check_login():
    try:
        df_csv = pd.read_csv(SHEET_URL)
        nomes = sorted([n for n in df_csv['Funcionario'].dropna().unique() if n not in ["Faiha", "Sonia", "Enrique", "Bianca S."]])
    except: nomes = list(MAPA_REFERENCIA.keys())

    # --- SIDEBAR COM ROTEIRO COMPLETO ---
    st.sidebar.title("⚙️ Painel")
    if st.sidebar.toggle("Ativar Acessibilidade", value=False):
        injetar_leitor_acessibilidade()
    
    st.sidebar.divider()
    with st.sidebar.expander("📝 Roteiro Terça: Práticas + Iniciativas", expanded=True):
        st.markdown("""
        **Pauta Principal:** Práticas + Iniciativas + Tracker + Work Plan
        - 📑 Lista de presença
        - ⏱ Pergunta Timekeeper (Challenge & Engage)
        - 🗓 Escala de horário
        - 📈 Behavior (Notas reunião anterior)
        - 🎯 Plano de ação (Ações do dia)
        - ✅ Práticas (Verificar com responsáveis)
        - 📊 NPS
        - 💡 Iniciativas (Comentários individuais)
        - 📉 Tracker
        - 🛠 Work Plan
        - ⚠️ Plano de ação (Issues e priorização)
        - 🛡 SHE
        - 🏆 Behavior (Reconhecimento e notas)
        """)

    with st.sidebar.expander("📝 Roteiro Quinta: Lead Time + SLA", expanded=True):
        st.markdown("""
        **Pauta Principal:** Lead Time e SLA + FTR + CATS/BH + Workplan
        - 📑 Lista de presença
        - ⏱ Pergunta Timekeeper, Challenger & Engage
        - 🗓 Escala de horário
        - 📈 Behavior (Notas reunião anterior)
        - 🎯 Plano de ação (Ações do dia)
        - 🕒 Lead Time
        - ✅ FTR (Bianca ou Renan)
        - 📁 Cats+BH (Amanda)
        - 🛠 Work Plan
        - ⚠️ Issues
        - 📍 Plano de ação (Priorizar: A, M, B)
        - 🛡 SHE
        - 🏆 Behavior (Reconhecimento e notas)
        """)

    df_total = gerar_escala_balanceada(nomes)
    st.title(f"🚀 MMD | Portal de Escalas 2026")

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        with st.expander("📂 Exportar Mês"):
            m_sel = st.selectbox("Mês:", list(MESES_NOMES.keys()))
            st.download_button(f"Baixar {m_sel}", exportar_excel_limpo(df_total, m_sel), f"Escala_{m_sel}.xlsx", use_container_width=True)
    with col_e2:
        with st.expander("📅 Exportar Ano"):
            st.download_button("Baixar Ano Completo", exportar_excel_limpo(df_total), "Escala_Anual.xlsx", use_container_width=True)

    st.divider()
    busca = st.selectbox("🔍 Buscar por Apresentador:", ["Todos"] + nomes)
    if busca != "Todos":
        df_b = df_total[df_total["Apresentador"] == busca].copy()
        st.dataframe(df_b[["Data", "Dia", "Reunião", "Backup", "Backup2", "Link"]], use_container_width=True, hide_index=True)

    st.divider()
    s_idx = st.select_slider("Semana:", options=sorted(df_total["Semana"].unique()), value=datetime.now().isocalendar()[1])
    df_s = df_total[df_total["Semana"] == s_idx]
    for dt, gp in df_s.groupby("Data", sort=False):
        st.markdown(f"**{gp['Dia'].iloc[0]} - {dt}**")
        cols = st.columns(len(gp))
        for i, (_, r) in enumerate(gp.iterrows()):
            with cols[i]: renderizar_card(r)
