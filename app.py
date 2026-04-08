import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Escala de Apresentações", layout="wide")

SHEET_ID = "1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

USER_ACCESS = "MMD-Board"
PASS_ACCESS = "@MMD123#"

# Mapa de Backups (Atualizado: Sonia, Enrique e Faiha removidos)
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

# --- FUNÇÕES DE UTILIDADE ---
@st.cache_data
def converter_para_csv(df):
    # utf-8-sig garante que o Excel abra com acentos corretos
    return df.to_csv(index=False).encode('utf-8-sig')

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

# --- LÓGICA DE ESCALA ---
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
        
        while fila_f[idx_f % len(fila_f)] in aps_sem: idx_f += 1
        ap_m = fila_f[idx_f % len(fila_f)]
        bkp1 = MAPA_BACKUPS.get(ap_m, "N/A"); bkp2 = MAPA_BACKUPS.get(bkp1, "N/A"); bkp3 = MAPA_BACKUPS.get(bkp2, "N/A")
        escala.append({"Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": "Flash Manhã", "Apresentador": ap_m, "Backup": bkp1, "Backup2": bkp2, "Backup3": bkp3, "Link": criar_link_outlook(data_s, "Flash Manhã", ap_m)})
        aps_sem.append(ap_m); idx_f += 1
        
        if d_sem in [1, 3]: 
            while fila_d[idx_d % len(fila_d)] in aps_sem: idx_d += 1
            ap_d = fila_d[idx_d % len(fila_d)]
            bkp1_d = MAPA_BACKUPS.get(ap_d, "N/A"); bkp2_d = MAPA_BACKUPS.get(bkp1_d, "N/A"); bkp3_d = MAPA_BACKUPS.get(bkp2_d, "N/A")
            escala.append({"Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": "DOR", "Apresentador": ap_d, "Backup": bkp1_d, "Backup2": bkp2_d, "Backup3": bkp3_d, "Link": criar_link_outlook(data_s, "DOR", ap_d)})
            idx_d += 1
        else:
            while fila_f[idx_f % len(fila_f)] in aps_sem: idx_f += 1
            ap_t = fila_f[idx_f % len(fila_f)]
            bkp1_t = MAPA_BACKUPS.get(ap_t, "N/A"); bkp2_t = MAPA_BACKUPS.get(bkp1_t, "N/A"); bkp3_t = MAPA_BACKUPS.get(bkp2_t, "N/A")
            escala.append({"Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": "Flash Tarde", "Apresentador": ap_t, "Backup": bkp1_t, "Backup2": bkp2_t, "Backup3": bkp3_t, "Link": criar_link_outlook(data_s, "Flash Tarde", ap_t)})
            idx_f += 1
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

# --- INÍCIO DO APP ---
if check_login():
    nomes_lista = carregar_nomes()
    if nomes_lista:
        st.sidebar.title("⚙️ Configurações")
        acessibilidade = st.sidebar.toggle("♿ Ativar Leitura (Acessibilidade)", value=False)
        if acessibilidade: injetar_leitor_acessibilidade()

        df_total = gerar_escala_final(nomes_lista)
        st.title(f"🚀 MMD | Dashboard de Apresentações {datetime.now().year}")
        
        # --- BUSCAR APRESENTADOR ---
        filtro_nome = st.selectbox("🔍 Buscar por Apresentador:", ["Todos"] + nomes_lista)
        
        if filtro_nome != "Todos":
            # Filtragem e adição da coluna Backup para visualização na tabela
            df_p = df_total[df_total["Apresentador"] == filtro_nome].copy()
            df_p["Backup_Atual"] = MAPA_BACKUPS.get(filtro_nome, "N/A")
            
            # Reorganização para a tabela de busca
            df_exibir = df_p[["Data", "Dia", "Reunião", "Backup_Atual", "Semana", "Link"]]
            
            st.info(f"📊 {filtro_nome} tem **{len(df_exibir)}** apresentações em {datetime.now().year}.")
            
            st.dataframe(
                df_exibir,
                column_config={
                    "Data": st.column_config.TextColumn("Data", width="small"),
                    "Dia": st.column_config.TextColumn("Dia", width="small"),
                    "Reunião": st.column_config.TextColumn("Reunião", width="medium"),
                    "Backup_Atual": st.column_config.TextColumn("🔄 Backup", width="medium"),
                    "Semana": st.column_config.NumberColumn("Sem.", width="small"),
                    "Link": st.column_config.LinkColumn("📅 Agendar", display_text="Agendar no Outlook", width="small")
                },
                use_container_width=True,
                hide_index=True
            )

            # --- BOTÃO DE DOWNLOAD (Excel/CSV) ---
            csv_data = converter_para_csv(df_exibir.drop(columns=["Link"])) # Remove link do CSV para ficar limpo
            st.download_button(
                label=f"📥 Baixar escala de {filtro_nome} (Excel/CSV)",
                data=csv_data,
                file_name=f'escala_MMD_{filtro_nome}.csv',
                mime='text/csv',
                use_container_width=True
            )
            st.divider()

        st.subheader("🗓️ Visualização por Semana")
        sem_atual = datetime.now().isocalendar()[1]
        sem_busca = st.select_slider("Semana:", options=sorted(df_total["Semana"].unique()), value=sem_atual)
        
        df_semana = df_total[df_total["Semana"] == sem_busca]
        for d_label, group in df_semana.groupby("Data", sort=False):
            st.markdown(f"**{group['Dia'].iloc[0]} - {d_label}**")
            cols = st.columns(len(group))
            for i, (_, row) in enumerate(group.iterrows()):
                with cols[i]: renderizar_card(row)
