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

# --- LISTA DE BACKUPS ATUALIZADA (Faiha removida e Livia atualizada) ---
MAPA_BACKUPS = {
    "Abigail": "Dani", "Amanda": "Mijal", "Anna": "Soledad", 
    "Ariel": "Rafael", "Bianca M.": "Ariel", "Bianca S.": "Amanda", 
    "Bruna": "Anna Laura", "Bruno": "Bianca M.", "Enrique": "Jazmin", 
    "Dani": "Sonia", "Debora": "Bruna", "Diana": "Julia", 
    "Florencia": "Diana", "Gisele": "Thiago", 
    "Honorato": "Bruno", "Jazmin": "Abigail", "Jesus": "Luca", 
    "Julia": "Honorato", "Livia": "Bianca S.", "Luca": "Enrique", 
    "Mijal": "Livia", "Rafael": "Florencia", "Renan": "Debora", 
    "Sonia": "Jesus", "Soledad": "Gisele", "Thiago": "Renan"
}

def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown("<h2 style='text-align: center;'>Portal de Escalas MMD</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            user = st.text_input("Usuário").strip()
            password = st.text_input("Senha", type="password").strip()
            if st.button("Acessar Painel", use_container_width=True):
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
        corpo = urllib.parse.quote(f"Apresentador: {apresentador}")
        return f"https://outlook.office.com/calendar/0/deeplink/compose?subject={assunto}&body={corpo}&startdt={data_iso}T{hora_start}&enddt={data_iso}T{hora_end}"
    except:
        return "#"

@st.cache_data(ttl=60)
def carregar_nomes():
    try:
        df_sheets = pd.read_csv(SHEET_URL)
        return sorted(df_sheets['Funcionario'].dropna().unique().tolist())
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return []

def gerar_escala_final(nomes):
    ano_atual = datetime.now().year
    data_inicio = datetime(ano_atual, 1, 1)
    data_fim = datetime(ano_atual, 12, 31)
    dias = pd.date_range(data_inicio, data_fim, freq='B')
    
    fila_flash = nomes.copy()
    fila_dor = [n for n in nomes if n not in ["Dani", "Rafael"]]
    
    idx_f = 0
    idx_d = 0
    escala = []

    for dia in dias:
        dia_semana = dia.weekday() 
        data_s = dia.strftime("%d/%m/%Y")
        sem = dia.isocalendar()[1]
        dia_nome = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][dia_semana]

        ap_m = fila_flash[idx_f % len(fila_flash)]
        escala.append({
            "Semana": sem, "Data": data_s, "Dia": dia_nome,
            "Reunião": "Flash Manhã", "Apresentador": ap_m,
            "Backup": MAPA_BACKUPS.get(ap_m, "N/A"),
            "Link": criar_link_outlook(data_s, "Flash Manhã", ap_m)
        })
        idx_f += 1

        if dia_semana in [1, 3]: 
            ap_d = fila_dor[idx_d % len(fila_dor)]
            if ap_d == ap_m:
                idx_d += 1
                ap_d = fila_dor[idx_d % len(fila_dor)]
            escala.append({
                "Semana": sem, "Data": data_s, "Dia": dia_nome,
                "Reunião": "DOR", "Apresentador": ap_d,
                "Backup": MAPA_BACKUPS.get(ap_d, "N/A"),
                "Link": criar_link_outlook(data_s, "DOR", ap_d)
            })
            idx_d += 1
        elif dia_semana in [0, 2, 4]:
            ap_t = fila_flash[idx_f % len(fila_flash)]
            if ap_t == ap_m:
                idx_f += 1
                ap_t = fila_flash[idx_f % len(fila_flash)]
            escala.append({
                "Semana": sem, "Data": data_s, "Dia": dia_nome,
                "Reunião": "Flash Tarde", "Apresentador": ap_t,
                "Backup": MAPA_BACKUPS.get(ap_t, "N/A"),
                "Link": criar_link_outlook(data_s, "Flash Tarde", ap_t)
            })
            idx_f += 1
    return pd.DataFrame(escala)

def renderizar_card(row):
    st.markdown(f"""
    <div class="card-click" style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; min-height: 190px; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
        <div>
            <b style="font-size: 14px; color: #31333F;">{row['Reunião']}</b><br>
            <span style="font-size: 18px; color: #333; font-weight: bold;">🏆 {row['Apresentador']}</span><br>
            <span style="font-size: 13px; color: #666;">🔄 Backup: {row['Backup']}</span>
        </div>
        <div style="margin-top: 10px;">
            <a href="{row['Link']}" target="_blank" style="display: block; text-decoration: none; color: white; background-color: #0078d4; padding: 8px; border-radius: 5px; font-size: 11px; text-align: center; font-weight: bold; width: 100%;">📅 AGENDAR OUTLOOK</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

if check_login():
    nomes_lista = carregar_nomes()
    if nomes_lista:
        df_total = gerar_escala_final(nomes_lista)
        
        # --- ACESSIBILIDADE GLOBAL ---
        if "voz" not in st.session_state: st.session_state.voz = False
        st.sidebar.title("Configurações")
        
        btn_label = "🔴 Desativar Leitura de Tela" if st.session_state.voz else "🔊 Ativar Leitura de Tela"
        if st.sidebar.button(btn_label):
            st.session_state.voz = not st.session_state.voz
            st.rerun()
            
        if st.session_state.voz:
            components.html("""
                <script>
                const synth = window.speechSynthesis;
                let lastText = "";

                function speak(text) {
                    const cleanText = text.trim();
                    if (cleanText === "" || cleanText === lastText) return;
                    if (synth.speaking) { synth.cancel(); }
                    
                    const utter = new SpeechSynthesisUtterance(cleanText);
                    utter.lang = 'pt-BR';
                    utter.rate = 1.0;
                    synth.speak(utter);
                    lastText = cleanText;
                }

                parent.document.addEventListener('mouseover', (e) => {
                    const targetText = e.target.innerText || e.target.textContent;
                    if (targetText && targetText.length < 300) {
                        speak(targetText);
                    }
                });
                </script>
            """, height=0)
        else:
            components.html("""
                <script>
                window.speechSynthesis.cancel();
                </script>
            """, height=0)

        st.title("🚀 MMD | Dashboard de Apresentações")
        
        opcoes_nomes = ["Todos"] + nomes_lista
        filtro_nome = st.selectbox("🔍 Buscar por Apresentador:", opcoes_nomes)
        
        if filtro_nome != "Todos":
            st.markdown(f"### 📅 Lista de Apresentações: {filtro_nome}")
            df_pessoal = df_total[df_total["Apresentador"] == filtro_nome].copy()
            st.data_editor(
                df_pessoal[["Data", "Dia", "Reunião", "Backup", "Link"]],
                column_config={
                    "Link": st.column_config.LinkColumn("Agenda Outlook", display_text="📅 AGENDAR"),
                },
                hide_index=True, use_container_width=True, disabled=True
            )
            st.markdown("---")

        st.subheader("🗓️ Visualização por Semana")
        sem_atual = datetime.now().isocalendar()[1]
        lista_s = sorted(df_total["Semana"].unique())
        sem_busca = st.select_slider("Selecione a Semana:", options=lista_s, value=sem_atual if sem_atual in lista_s else lista_s[0])
        
        df_semana = df_total[df_total["Semana"] == sem_busca]
        for d_label, group in df_semana.groupby("Data", sort=False):
            st.markdown(f"**{group['Dia'].iloc[0]} - {d_label}**")
            cols = st.columns(len(group))
            for i, (_, row) in enumerate(group.iterrows()):
                with cols[i]:
                    renderizar_card(row)
