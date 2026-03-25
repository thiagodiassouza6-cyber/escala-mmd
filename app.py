import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Escala de Apresentações", layout="wide")

# Link da Planilha
SHEET_ID = "1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# Credenciais
USER_ACCESS = "MMD-Board"
PASS_ACCESS = "@MMD123#"

def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown("<h2 style='text-align: center;'>Portal de Escalas MMD</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            user = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            if st.button("Acessar Painel", use_container_width=True):
                if user == USER_ACCESS and password == PASS_ACCESS:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
        return False
    return True

def criar_link_google(data_str, reuniao, apresentador):
    try:
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        hora = "094500" if "Manhã" in reuniao else "150000"
        data_formatada = data_obj.strftime("%Y%m%d")
        inicio = f"{data_formatada}T{hora}"
        fim_obj = datetime.strptime(inicio, "%Y%m%dT%H%M%S") + timedelta(minutes=30)
        fim = fim_obj.strftime("%Y%m%dT%H%M%S")
        titulo = urllib.parse.quote(f"🔔 Apresentação MMD: {reuniao}")
        detalhes = urllib.parse.quote(f"Apresentador: {apresentador}")
        return f"https://www.google.com/calendar/render?action=TEMPLATE&text={titulo}&dates={inicio}/{fim}&details={detalhes}"
    except:
        return "#"

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

def gerar_escala(nomes):
    data_inicio = datetime(2026, 1, 1)
    data_fim = datetime(2026, 12, 31)
    dias = pd.date_range(data_inicio, data_fim, freq='B')
    escala = []
    idx_nome = 0
    for dia in dias:
        semana = dia.isocalendar()[1]
        if semana < 13: continue
        dia_semana = dia.weekday()
        reunioes = ["Flash Manhã", "DOR"] if dia_semana in [1, 3] else ["Flash Manhã", "Flash Tarde"]
        for r in reunioes:
            while True:
                nome_atual = nomes[idx_nome % len(nomes)]
                if r == "DOR" and nome_atual in ["Dani", "Rafael"]:
                    idx_nome += 1
                    continue
                escala.append({
                    "Semana": semana,
                    "Data": dia.strftime("%d/%m/%Y"),
                    "Dia": ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][dia_semana],
                    "Reunião": r,
                    "Apresentador": nome_atual
                })
                idx_nome += 1
                break
    return pd.DataFrame(escala)

if check_login():
    nomes_lista = carregar_nomes()
    if nomes_lista:
        df_total = gerar_escala(nomes_lista)
        
        # --- ACESSIBILIDADE AJUSTADA ---
        if "voz" not in st.session_state:
            st.session_state.voz = False
            
        st.sidebar.title("Acessibilidade")
        if st.sidebar.button("🔊 Ativar/Desativar Voz"):
            st.session_state.voz = not st.session_state.voz
            st.rerun()
            
        if st.session_state.voz:
            st.sidebar.success("Leitura ativada!")
            components.html("""
                <script>
                const synth = window.speechSynthesis;
                function speak(text) {
                    if (synth.speaking) { synth.cancel(); }
                    const utter = new SpeechSynthesisUtterance(text);
                    utter.lang = 'pt-BR';
                    utter.rate = 1.0; 
                    synth.speak(utter);
                }
                parent.document.querySelectorAll('.card-click').forEach(card => {
                    card.addEventListener('mouseenter', () => {
                        speak(card.getAttribute('data-audio'));
                    });
                });
                </script>
            """, height=0)

        st.title("🚀 MMD | Dashboard de Apresentações")
        
        opcoes_nomes = ["Todos"] + nomes_lista
        filtro_nome = st.selectbox("🔍 Buscar por Apresentador:", opcoes_nomes)
        
        if filtro_nome != "Todos":
            st.markdown(f"### 📅 Minhas Apresentações no Ano: {filtro_nome}")
            df_pessoal = df_total[df_total["Apresentador"] == filtro_nome].copy()
            df_pessoal["Google"] = df_pessoal.apply(lambda x: criar_link_google(x["Data"], x["Reunião"], x["Apresentador"]), axis=1)
            df_pessoal["Outlook"] = df_pessoal.apply(lambda x: criar_link_outlook(x["Data"], x["Reunião"], x["Apresentador"]), axis=1)
            
            st.dataframe(
                df_pessoal[["Data", "Dia", "Reunião", "Semana", "Google", "Outlook"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Google": st.column_config.LinkColumn("📅 Agenda"),
                    "Outlook": st.column_config.LinkColumn("📧 Teams")
                }
            )
            st.markdown("---")

        st.subheader("🗓️ Cronograma por Semana")
        semana_busca = st.select_slider("Arraste para ver a escala:", options=sorted(df_total["Semana"].unique()), value=13)
        df_semana = df_total[df_total["Semana"] == semana_busca]

        for data_label, group in df_semana.groupby("Data", sort=False):
            st.markdown(f"**{group['Dia'].iloc[0]} - {data_label}**")
            cols = st.columns(len(group))
            for i, (_, row) in enumerate(group.iterrows()):
                with cols[i]:
                    g_link = criar_link_google(row['Data'], row['Reunião'], row['Apresentador'])
                    o_link = criar_link_outlook(row['Data'], row['Reunião'], row['Apresentador'])
                    
                    # PADRÃO DE VOZ CORRIGIDO: Data - Dia - Reunião - Apresentador
                    audio_text = f"{row['Data']}. {row['Dia']}. {row['Reunião']}. Apresentador {row['Apresentador']}."
                    
                    st.markdown(f"""
                    <div class="card-click" data-audio="{audio_text}" style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b;
