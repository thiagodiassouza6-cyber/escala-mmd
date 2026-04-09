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

# --- LÓGICA DE HERANÇA ---
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

# --- EXCEL E ESTRUTURA ---
def converter_para_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Escala_MMD')
    return output.getvalue()

def preparar_df_estruturado(df_input):
    manha = df_input[df_input['Reunião'] == 'Flash Manhã'][['Data', 'Dia', 'Apresentador', 'Backup']].copy()
    manha.columns = ['Data', 'Dia', 'Responsável Manhã', 'Backup Manhã']
    tarde = df_input[df_input['Reunião'].isin(['Flash Tarde', 'DOR'])][['Data', 'Apresentador', 'Backup', 'Reunião']].copy()
    tarde.columns = ['Data', 'Responsável Tarde', 'Backup Tarde', 'Tipo Tarde/DOR']
    df_final = pd.merge(manha, tarde, on='Data', how='outer')
    cols_ordem = ['Data', 'Dia', 'Responsável Manhã', 'Backup Manhã', 'Tipo Tarde/DOR', 'Responsável Tarde', 'Backup Tarde']
    return df_final[cols_ordem]

def criar_link_outlook(data_str, reuniao):
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
        return sorted([n for n in nomes if n not in ["Faiha", "Sonia", "Enrique"]])
    except: return []

# --- GERAÇÃO DA ESCALA ---
def gerar_escala_final(nomes):
    ano_atual = datetime.now().year 
    dias = pd.date_range(datetime(ano_atual, 1, 1), datetime(ano_atual, 12, 31), freq='B')
    fila_f, escala = nomes.copy(), []
    nomes_dor = [n for n in nomes if n not in ["Dani", "Rafael"]]
    idx_f, idx_d = 0, 0
    
    for dia in dias:
        data_s, sem, d_sem = dia.strftime("%d/%m/%Y"), dia.isocalendar()[1], dia.weekday()
        d_nome = ["Segunda-Feira", "Terça-Feira", "Quarta-Feira", "Quinta-Feira", "Sexta-Feira"][d_sem]
        aps_sem = [item['Apresentador'] for item in escala if item['Semana'] == sem]
        
        # Flash Manhã
        while fila_f[idx_f % len(fila_f)] in aps_sem: idx_f += 1
        ap_m = fila_f[idx_f % len(fila_f)]
        b1_m = encontrar_backup_vivo(ap_m, nomes)
        escala.append({"Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": "Flash Manhã", "Apresentador": ap_m, "Backup": b1_m, "Link": criar_link_outlook(data_s, "Flash Manhã")})
        aps_sem.append(ap_m); idx_f += 1
        
        # Tarde (DOR ou Flash Tarde)
        if d_sem in [1, 3]: 
            while nomes_dor[idx_d % len(nomes_dor)] in aps_sem: idx_d += 1
            ap_t = nomes_dor[idx_d % len(nomes_dor)]
            reuniao_t = "DOR"
            idx_d += 1
        else:
            while fila_f[idx_f % len(fila_f)] in aps_sem: idx_f += 1
            ap_t = fila_f[idx_f % len(fila_f)]
            reuniao_t = "Flash Tarde"
            idx_f += 1
            
        b1_t = encontrar_backup_vivo(ap_t, nomes)
        escala.append({"Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": reuniao_t, "Apresentador": ap_t, "Backup": b1_t, "Link": criar_link_outlook(data_s, reuniao_t)})
        
    return pd.DataFrame(escala)

def renderizar_card(row):
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; min-height: 160px; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
        <b style="font-size: 14px; color: #31333F;">{row['Reunião']}</b><br><br>
        <span style="font-size: 18px; color: #333; font-weight: bold;">🏆 {row['Apresentador']}</span><br><br>
        <span style="font-size: 13px; color: #666;">🔄 Backup: {row['Backup']}</span><br>
        <div style="margin-top: 15px;">
            <a href="{row['Link']}" target="_blank" style="display: block; text-decoration: none; color: white; background-color: #0078d4; padding: 8px; border-radius: 5px; font-size: 11px; text-align: center; font-weight: bold;">📅 AGENDAR</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- EXECUÇÃO DO APP ---
if check_login():
    nomes_lista = carregar_nomes()
    if nomes_lista:
        # Sidebar com Acessibilidade
        st.sidebar.title("⚙️ Configurações")
        acess = st.sidebar.toggle("♿ Ativar Leitura (Acessibilidade)", value=False)
        if acess: injetar_leitor_acessibilidade()
        
        df_total = gerar_escala_final(nomes_lista)
        st.title(f"🚀 MMD | Dashboard de Apresentações {datetime.now().year}")

        # Seção de Exportação
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            with st.expander("📂 Exportar Mês Específico"):
                mes_sel = st.selectbox("Mês:", list(MESES_NOMES.keys()))
                df_total['dt_aux'] = pd.to_datetime(df_total['Data'], format='%d/%m/%Y')
                df_mes = df_total[df_total['dt_aux'].dt.month == MESES_NOMES[mes_sel]].copy()
                st.download_button(f"📥 Baixar Excel {mes_sel}", converter_para_excel(preparar_df_estruturado(df_mes)), f"Escala_MMD_{mes_sel}.xlsx", use_container_width=True)
        with col_exp2:
            with st.expander("📅 Exportar Ano Completo"):
                st.write("Baixe a escala anual estruturada (Manhã e Tarde).")
                st.download_button("📥 Baixar Planilha Anual", converter_para_excel(preparar_df_estruturado(df_total)), f"Escala_Anual_MMD_{datetime.now().year}.xlsx", use_container_width=True)

        st.divider()
        # Busca Individual
        filtro_nome = st.selectbox("🔍 Buscar por Apresentador:", ["Todos"] + nomes_lista)
        if filtro_nome != "Todos":
            df_p = df_total[df_total["Apresentador"] == filtro_nome].copy()
            st.info(f"📊 {filtro_nome} tem **{len(df_p)}** apresentações no ano.")
            st.dataframe(df_p[["Data", "Dia", "Reunião", "Backup", "Link"]], column_config={"Link": st.column_config.LinkColumn("📅 Agendar", display_text="Agendar")}, use_container_width=True, hide_index=True)

        st.divider()
        # View Semanal com Cards
        sem_atual = datetime.now().isocalendar()[1]
        sem_busca = st.select_slider("Semana:", options=sorted(df_total["Semana"].unique()), value=sem_atual)
        df_sem = df_total[df_total["Semana"] == sem_busca]
        
        for data, group in df_sem.groupby("Data", sort=False):
            st.markdown(f"**{group['Dia'].iloc[0]} - {data}**")
            cols = st.columns(len(group))
            for i, (_, row) in enumerate(group.iterrows()):
                with cols[i]: renderizar_card(row)
