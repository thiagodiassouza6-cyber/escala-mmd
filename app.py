import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import streamlit.components.v1 as components
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Escala de Apresentações", layout="wide")

SHEET_ID = "1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

USER_ACCESS = "MMD-Board"
PASS_ACCESS = "@MMD123#"

MESES_NOMES = {
    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, 
    "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8, 
    "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
}

MAPA_BACKUPS = {
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

# --- FUNÇÕES DE EXPORTAÇÃO ---
def converter_para_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Escala_MMD')
    return output.getvalue()

def preparar_df_mensal_estruturado(df_mes):
    """Estrutura: Data | Dia | Resp. Manhã | Backup Manhã | Tipo Tarde/DOR | Resp. Tarde | Backup Tarde"""
    manha = df_mes[df_mes['Reunião'] == 'Flash Manhã'][['Data', 'Dia', 'Apresentador', 'Backup']].copy()
    manha.columns = ['Data', 'Dia', 'Responsável Manhã', 'Backup Manhã']
    
    tarde = df_mes[df_mes['Reunião'].isin(['Flash Tarde', 'DOR'])][['Data', 'Apresentador', 'Backup', 'Reunião']].copy()
    tarde.columns = ['Data', 'Responsável Tarde', 'Backup Tarde', 'Tipo Tarde/DOR']
    
    df_final = pd.merge(manha, tarde, on='Data', how='outer')
    cols_ordem = ['Data', 'Dia', 'Responsável Manhã', 'Backup Manhã', 'Tipo Tarde/DOR', 'Responsável Tarde', 'Backup Tarde']
    return df_final[cols_ordem]

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
            docAlvo.addEventListener('mouseout', () => {
                synth.cancel();
            }, true);
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

# --- UTILITÁRIOS ---
def criar_link_outlook(data_str, reuniao, apresentador):
    try:
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        data_iso = data_obj.strftime("%Y-%m-%d")
        hora_start = "09:45:00" if "Manhã" in reuniao else "15:00:00"
        hora_end = "10:15:00" if "Manhã" in reuniao else "15:30:00"
        assunto = urllib.parse.quote(f"🔔 Apresentação MMD: {reuniao}")
        return f"https://outlook.office.com/calendar/0/deeplink/compose?subject={assunto}&startdt={data_iso}T{hora_start}&enddt={data_iso}T{hora_end}"
    except: return "#"

@st.cache_data(ttl=5)
def carregar_nomes():
    try:
        df = pd.read_csv(SHEET_URL)
        nomes = df['Funcionario'].dropna().unique().tolist()
        nomes_filtrados = [n for n in nomes if n not in ["Faiha", "Sonia", "Enrique"]]
        return sorted(nomes_filtrados)
    except: return []

def gerar_escala_final(nomes):
    ano_atual = datetime.now().year 
    dias = pd.date_range(datetime(ano_atual, 1, 1), datetime(ano_atual, 12, 31), freq='B')
    fila_f, escala = nomes.copy(), []
    fila_d = [n for n in nomes if n not in ["Dani", "Rafael"]]
    idx_f, idx_d = 0, 0
    
    for dia in dias:
        data_s, sem, d_sem = dia.strftime("%d/%m/%Y"), dia.isocalendar()[1], dia.weekday()
        d_nome = ["Segunda-Feira", "Terça-Feira", "Quarta-Feira", "Quinta-Feira", "Sexta-Feira"][d_sem]
        aps_sem = [item['Apresentador'] for item in escala if item['Semana'] == sem]
        
        # Lógica Manhã
        while fila_f[idx_f % len(fila_f)] in aps_sem: idx_f += 1
        ap_m = fila_f[idx_f % len(fila_f)]
        b1 = MAPA_BACKUPS.get(ap_m, "N/A")
        b2 = MAPA_BACKUPS.get(b1, "N/A")
        b3 = MAPA_BACKUPS.get(b2, "N/A")
        escala.append({"Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": "Flash Manhã", "Apresentador": ap_m, "Backup": b1, "Backup2": b2, "Backup3": b3, "Link": criar_link_outlook(data_s, "Flash Manhã", ap_m)})
        aps_sem.append(ap_m); idx_f += 1
        
        # Lógica Tarde
        if d_sem in [1, 3]: 
            while fila_d[idx_d % len(fila_d)] in aps_sem: idx_d += 1
            ap_t = fila_d[idx_d % len(fila_d)]
            reuniao_t = "DOR"
            idx_d += 1
        else:
            while fila_f[idx_f % len(fila_f)] in aps_sem: idx_f += 1
            ap_t = fila_f[idx_f % len(fila_f)]
            reuniao_t = "Flash Tarde"
            idx_f += 1
            
        b1_t = MAPA_BACKUPS.get(ap_t, "N/A")
        b2_t = MAPA_BACKUPS.get(b1_t, "N/A")
        b3_t = MAPA_BACKUPS.get(b2_t, "N/A")
        escala.append({"Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": reuniao_t, "Apresentador": ap_t, "Backup": b1_t, "Backup2": b2_t, "Backup3": b3_t, "Link": criar_link_outlook(data_s, reuniao_t, ap_t)})
        
    return pd.DataFrame(escala)

def renderizar_card(row):
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; min-height: 180px; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
        <b style="font-size: 14px; color: #31333F;">{row['Reunião']}</b><br><br>
        <span style="font-size: 18px; color: #333; font-weight: bold;">🏆 {row['Apresentador']}</span><br><br>
        <span style="font-size: 13px; color: #666;">🔄 Backup: {row['Backup']}</span><br>
        <span title="Próximo Backup: {row['Backup3']}" style="font-size: 13px; color: #777; cursor: help; display: block; margin-top: 3px;">🛡️ Backup 2: {row['Backup2']}</span><br>
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
        acessibilidade = st.sidebar.toggle("♿ Ativar Leitura (Acessibilidade)", value=False)
        if acessibilidade: injetar_leitor_acessibilidade()

        df_total = gerar_escala_final(nomes_lista)
        st.title(f"🚀 MMD | Dashboard de Apresentações {datetime.now().year}")
        
        # BUSCA INDIVIDUAL
        filtro_nome = st.selectbox("🔍 Buscar por Apresentador:", ["Todos"] + nomes_lista)
        if filtro_nome != "Todos":
            df_p = df_total[df_total["Apresentador"] == filtro_nome].copy()
            df_exibir = df_p[["Data", "Dia", "Reunião", "Backup", "Semana", "Link"]]
            st.info(f"📊 {filtro_nome} tem **{len(df_exibir)}** apresentações.")
            st.dataframe(df_exibir, column_config={"Link": st.column_config.LinkColumn("📅 Agendar", display_text="Agendar no Outlook")}, use_container_width=True, hide_index=True)
            excel_indiv = converter_para_excel(df_exibir.drop(columns=["Link"]))
            st.download_button(label=f"📥 Baixar escala de {filtro_nome} (.xlsx)", data=excel_indiv, file_name=f'Escala_{filtro_nome}.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)
            st.divider()

        # EXTRAÇÃO MENSAL
        with st.expander("📂 Extrair Planilha Mensal (Flash Manhã vs Tarde)"):
            mes_sel = st.selectbox("Selecione o mês:", list(MESES_NOMES.keys()))
            df_total['Data_Aux'] = pd.to_datetime(df_total['Data'], format='%d/%m/%Y')
            df_mes_raw = df_total[df_total['Data_Aux'].dt.month == MESES_NOMES[mes_sel]].copy()
            if not df_mes_raw.empty:
                df_mes_final = preparar_df_mensal_estruturado(df_mes_raw)
                st.write(f"✅ Escala estruturada pronta para download.")
                excel_mensal = converter_para_excel(df_mes_final)
                st.download_button(label=f"💾 Baixar Escala Consolidada {mes_sel} (.xlsx)", data=excel_mensal, file_name=f'Escala_MMD_{mes_sel}_Completa.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)
        st.divider()

        # VIEW SEMANAL
        sem_atual = datetime.now().isocalendar()[1]
        sem_busca = st.select_slider("Semana:", options=sorted(df_total["Semana"].unique()), value=sem_atual)
        df_semana = df_total[df_total["Semana"] == sem_busca]
        for d_label, group in df_semana.groupby("Data", sort=False):
            st.markdown(f"**{group['Dia'].iloc[0]} - {d_label}**")
            cols = st.columns(len(group))
            for i, (_, row) in enumerate(group.iterrows()):
                with cols[i]: renderizar_card(row)
