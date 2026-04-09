import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import streamlit.components.v1 as components
import io

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

MAPA_REFERENCIA = {
    "Abigail": "Dani", "Amanda": "Mijal", "Anna Laura": "Soledad", 
    "Ariel": "Rafael", "Bianca M.": "Ariel", "Bianca S.": "Amanda", 
    "Bruna": "Anna Laura", "Bruno": "Bianca M.", 
    "Dani": "Jesus", "Debora": "Bruna", "Diana": "Julia", 
    "Florencia": "Diana", "Gisele": "Thiago", 
    "Honorato": "Bruno", "Jazmin": "Abigail", "Jesus": "Luca", 
    "Julia": "Honorato", "Livia": "Bianca S.", "Luca": "Jazmin", 
    "Mijal": "Livia", "Rafael": "Florencia", "Renan": "Debora", 
    "Soledad": "Gisele", "Thiago": "Renan"
}

# --- LÓGICA DE BACKUPS ---
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
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown("<h2 style='text-align: center;'>Portal de Escalas MMD</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            with st.form("login_system"):
                user = st.text_input("Usuário").strip()
                password = st.text_input("Senha", type="password").strip()
                if st.form_submit_button("Acessar Painel", use_container_width=True):
                    if user == USER_ACCESS and password == PASS_ACCESS:
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
        return False
    return True

# --- EXPORTAÇÃO EXCEL ESTRUTURADA ---
def exportar_excel_mmd(df_total, apenas_um_mes=None):
    output = io.BytesIO()
    df_base = preparar_df_estruturado(df_total)
    df_base['dt_obj'] = pd.to_datetime(df_base['Data'], format='%d/%m/%Y')
    df_base = df_base.sort_values('dt_obj')
    
    if apenas_um_mes:
        df_base = df_base[df_base['dt_obj'].dt.month == MESES_NOMES[apenas_um_mes]]

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook  = writer.book
        worksheet = workbook.add_worksheet('Escala MMD')
        
        fmt_mes = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'align': 'center', 'border': 1})
        fmt_head = workbook.add_format({'bold': True, 'bg_color': '#ff4b4b', 'font_color': 'white', 'border': 1})
        fmt_cell = workbook.add_format({'border': 1})

        colunas = ['Data', 'Dia', 'Responsável Manhã', 'Backup Manhã', 'Tipo Tarde/DOR', 'Responsável Tarde', 'Backup Tarde']
        for col_num, value in enumerate(colunas):
            worksheet.write(0, col_num, value, fmt_head)
            worksheet.set_column(col_num, col_num, 18)

        current_row = 1
        meses_a_processar = [apenas_um_mes] if apenas_um_mes else list(MESES_NOMES.keys())

        for mes_nome in meses_a_processar:
            df_mes = df_base[df_base['dt_obj'].dt.month == MESES_NOMES[mes_nome]]
            if df_mes.empty: continue
            
            # Divisor de Mês (Mesclado)
            worksheet.merge_range(current_row, 0, current_row, 6, mes_nome.upper(), fmt_mes)
            current_row += 1
            
            for _, row in df_mes.iterrows():
                for col_num, col_name in enumerate(colunas):
                    worksheet.write(current_row, col_num, str(row[col_name]), fmt_cell)
                current_row += 1
            
    return output.getvalue()

def preparar_df_estruturado(df_input):
    df_input['dt_aux'] = pd.to_datetime(df_input['Data'], format='%d/%m/%Y')
    df_sorted = df_input.sort_values('dt_aux')
    
    manha = df_sorted[df_sorted['Reunião'] == 'Flash Manhã'][['Data', 'Dia', 'Apresentador', 'Backup']].copy()
    manha.columns = ['Data', 'Dia', 'Responsável Manhã', 'Backup Manhã']
    
    tarde = df_sorted[df_sorted['Reunião'].isin(['Flash Tarde', 'DOR'])][['Data', 'Apresentador', 'Backup', 'Reunião']].copy()
    tarde.columns = ['Data', 'Responsável Tarde', 'Backup Tarde', 'Tipo Tarde/DOR']
    
    return pd.merge(manha, tarde, on='Data', how='outer').fillna("")

def criar_link_outlook(data_str, reuniao):
    try:
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        data_iso = data_obj.strftime("%Y-%m-%d")
        hora_start = "09:45:00" if "Manhã" in reuniao else "15:00:00"
        assunto = urllib.parse.quote(f"🔔 Apresentação MMD: {reuniao}")
        return f"https://outlook.office.com/calendar/0/deeplink/compose?subject={assunto}&startdt={data_iso}T{hora_start}&enddt={data_iso}T{hora_start}"
    except: return "#"

@st.cache_data(ttl=5)
def carregar_nomes():
    try:
        df = pd.read_csv(SHEET_URL)
        nomes = df['Funcionario'].dropna().unique().tolist()
        return sorted([n for n in nomes if n not in ["Faiha", "Sonia", "Enrique"]])
    except: return []

def gerar_escala_final(nomes):
    ano_atual = datetime.now().year 
    dias = pd.date_range(datetime(ano_atual, 1, 1), datetime(ano_atual, 12, 31), freq='B')
    fila_f, escala = nomes.copy(), []
    nomes_dor = [n for n in nomes if n not in ["Dani", "Rafael"]] # 21 pessoas
    idx_f, idx_d = 0, 0
    
    for dia in dias:
        data_s, sem, d_sem = dia.strftime("%d/%m/%Y"), dia.isocalendar()[1], dia.weekday()
        d_nome = ["Segunda-Feira", "Terça-Feira", "Quarta-Feira", "Quinta-Feira", "Sexta-Feira"][d_sem]
        aps_no_dia = []
        
        # Manhã
        ap_m = fila_f[idx_f % len(fila_f)]
        b1_m = encontrar_backup_vivo(ap_m, nomes); b2_m = encontrar_backup_vivo(b1_m, nomes); b3_m = encontrar_backup_vivo(b2_m, nomes)
        escala.append({"Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": "Flash Manhã", "Apresentador": ap_m, "Backup": b1_m, "Backup2": b2_m, "Backup3": b3_m, "Link": criar_link_outlook(data_s, "Flash Manhã")})
        aps_no_dia.append(ap_m); idx_f += 1
        
        # Tarde (DOR ou Flash)
        if d_sem in [1, 3]:
            while nomes_dor[idx_d % len(nomes_dor)] in aps_no_dia: idx_d += 1
            ap_t, reuniao_t = nomes_dor[idx_d % len(nomes_dor)], "DOR"
            idx_d += 1
        else:
            while fila_f[idx_f % len(fila_f)] in aps_no_dia: idx_f += 1
            ap_t, reuniao_t = fila_f[idx_f % len(fila_f)], "Flash Tarde"
            idx_f += 1
            
        b1_t = encontrar_backup_vivo(ap_t, nomes); b2_t = encontrar_backup_vivo(b1_t, nomes); b3_t = encontrar_backup_vivo(b2_t, nomes)
        escala.append({"Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": reuniao_t, "Apresentador": ap_t, "Backup": b1_t, "Backup2": b2_t, "Backup3": b3_t, "Link": criar_link_outlook(data_s, reuniao_t)})
        
    return pd.DataFrame(escala)

def renderizar_card(row):
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; min-height: 220px; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
        <b style="font-size: 14px; color: #31333F;">{row['Reunião']}</b><br><br>
        <span style="font-size: 18px; color: #333; font-weight: bold;">🏆 {row['Apresentador']}</span><br><br>
        <span style="font-size: 13px; color: #666;">🔄 Backup: {row['Backup']}</span><br>
        <span style="font-size: 13px; color: #777;">🛡️ Backup 2: {row['Backup2']}</span><br>
        <span title="Backup 3: {row['Backup3']}" style="font-size: 11px; color: #bbb; cursor: help;">🔍 Backup 3 (Passe o mouse)</span>
        <div style="margin-top: 15px;">
            <a href="{row['Link']}" target="_blank" style="display: block; text-decoration: none; color: white; background-color: #0078d4; padding: 8px; border-radius: 5px; font-size: 11px; text-align: center; font-weight: bold;">📅 AGENDAR</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- EXECUÇÃO ---
if check_login():
    nomes_lista = carregar_nomes()
    if nomes_lista:
        st.sidebar.title("⚙️ Configurações")
        if st.sidebar.toggle("♿ Ativar Acessibilidade", value=False): injetar_leitor_acessibilidade()
        
        df_total = gerar_escala_final(nomes_lista)
        st.title(f"🚀 MMD | Dashboard de Escalas {datetime.now().year}")

        c1, c2 = st.columns(2)
        with c1:
            with st.expander("📂 Exportar Mês"):
                m_sel = st.selectbox("Mês:", list(MESES_NOMES.keys()))
                st.download_button(f"📥 Baixar {m_sel}", exportar_excel_mmd(df_total, m_sel), f"Escala_{m_sel}.xlsx", use_container_width=True)
        with c2:
            with st.expander("📅 Exportar Ano"):
                st.download_button("📥 Baixar Ano Completo", exportar_excel_mmd(df_total), f"Escala_Anual_{datetime.now().year}.xlsx", use_container_width=True)

        st.divider()
        sem_atual = datetime.now().isocalendar()[1]
        sem_busca = st.select_slider("Semana:", options=sorted(df_total["Semana"].unique()), value=sem_atual)
        df_sem = df_total[df_total["Semana"] == sem_busca]
        
        for data, gp in df_sem.groupby("Data", sort=False):
            st.markdown(f"**{gp['Dia'].iloc[0]} - {data}**")
            cols = st.columns(len(gp))
            for i, (_, r) in enumerate(gp.iterrows()):
                with cols[i]: renderizar_card(r)
