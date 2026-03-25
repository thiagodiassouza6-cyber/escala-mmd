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

# --- MAPEAMENTO DE BACKUPS ---
# Baseado na lista enviada
MAPA_BACKUPS = {
    "Amanda": "Mijal", "Anna Laura": "Soledad", "Ariel": "Rafael",
    "Bianca M.": "Ariel", "Bianca S.": "Amanda", "Bruna": "Anna Laura",
    "Bruno": "Bianca M.", "Cristian": "Debora", "Enrique": "Sonia",
    "Debora": "Bruna", "Diana": "Julia", "Faiha": "Bianca S.",
    "Florencia": "Diana", "Gisele": "Thiago", "Honorato": "Bruno",
    "Jesus": "Luca", "Julia": "Honorato", "Livia": "Faiha",
    "Luca": "Enrique", "Mijal": "Livia", "Rafael": "Florencia",
    "Renan": "Cristian", "Sonia": "Jesus", "Soledad": "Gisele",
    "Thiago": "Renan"
}

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
    ano_atual = datetime.now().year
    data_inicio = datetime(ano_atual, 1, 1)
    data_fim = datetime(ano_atual, 12, 31)
    dias = pd.date_range(data_inicio, data_fim, freq='B')
    
    escala = []
    idx_geral = 0 
    participacao_semanal = {}

    for dia in dias:
        semana = dia.isocalendar()[1]
        dia_semana = dia.weekday()
        
        if semana not in participacao_semanal:
            participacao_semanal[semana] = set()

        reunioes_do_dia = ["Flash Manhã"]
        if dia_semana in [1, 3]: 
            reunioes_do_dia.append("DOR")
        else: 
            reunioes_do_dia.append("Flash Tarde")

        for r in reunioes_do_dia:
            tentativas = 0
            while tentativas < len(nomes):
                nome_atual = nomes[idx_geral % len(nomes)]
                ja_apresentou = nome_atual in participacao_semanal[semana]
                bloqueio_dor = (r == "DOR" and nome_atual in ["Dani", "Rafael"])
                
                if ja_apresentou or bloqueio_dor:
                    idx_geral += 1
                    tentativas += 1
                    continue
                
                escala.append({
                    "Semana": semana,
                    "Data": dia.strftime("%d/%m/%Y"),
                    "Dia": ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][dia_semana],
                    "Reunião": r,
                    "Apresentador": nome_atual,
                    "Backup": MAPA_BACKUPS.get(nome_atual, "N/A")
                })
                participacao_semanal[semana].add(nome_atual)
                idx_geral += 1
                break
    return pd.DataFrame(escala)

if check_login():
    nomes_lista = carregar_nomes()
    if nomes_lista:
        df_total = gerar_escala(nomes_lista)
        
        # --- ACESSIBILIDADE ---
        if "voz" not in st.session_state:
            st.session_state.voz = False
        st.sidebar.title("Acessibilidade")
        if st.sidebar.button("🔊 Ativar/Desativar Voz"):
            st.session_state.voz = not st.session_state.voz
            st.rerun()
            
        if st.session_state.voz:
            st.sidebar.success("Leitura de tela ativada!")
            components.html("""
                <script>
                const synth = window.speechSynthesis;
                function speak(text) {
                    if (synth.speaking) { synth.cancel(); }
                    const utter = new SpeechSynthesisUtterance(text);
                    utter.lang = 'pt-BR';
                    synth.speak(utter);
                }
                parent.document.querySelectorAll('.card-click').forEach(card => {
                    card.addEventListener('mouseenter', () => speak(card.getAttribute('data-audio')));
                });
                </script>
            """, height=0)

        st.title("🚀 MMD | Dashboard de Apresentações")
        
        opcoes_nomes = ["Todos"] + nomes_lista
        filtro_nome = st.selectbox("🔍 Buscar por Apresentador:", opcoes_nomes)
        
        if filtro_nome != "Todos":
            st.markdown(f"### 📅 Minhas Apresentações: {filtro_nome}")
            df_pessoal = df_total[df_total["Apresentador"] == filtro_nome].copy()
            st.dataframe(df_pessoal[["Data", "Dia", "Reunião", "Backup"]], use_container_width=True, hide_index=True)
            st.markdown("---")

        st.subheader("🗓️ Cronograma por Semana")
        semana_atual = datetime.now().isocalendar()[1]
        lista_semanas = sorted(df_total["Semana"].unique())
        semana_busca = st.select_slider("Arraste a escala:", options=lista_semanas, value=semana_atual if semana_atual in lista_semanas else lista_semanas[0])
        
        df_semana = df_total[df_total["Semana"] == semana_busca]

        for data_label, group in df_semana.groupby("Data", sort=False):
            st.markdown(f"**{group['Dia'].iloc[0]} - {data_label}**")
            cols = st.columns(len(group))
            for i, (_, row) in enumerate(group.iterrows()):
                with cols[i]:
                    o_link = criar_link_outlook(row['Data'], row['Reunião'], row['Apresentador'])
                    audio_text = f"{row['Reunião']}. Apresentador {row['Apresentador']}. Backup {row['Backup']}."
                    st.markdown(f"""
                    <div class="card-click" data-audio="{audio_text}" style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; min-height: 180px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                        <div>
                            <b style="font-size: 14px; color: #31333F;">{row['Reunião']}</b><br>
                            <span style="font-size: 17px; color: #333; font-weight: bold;">🏆 {row['Apresentador']}</span><br>
                            <span style="font-size: 13px; color: #666;">🔄 Backup: {row['Backup']}</span>
                        </div>
                        <div style="margin-top: 10px;">
                            <a href="{o_link}" target="_blank" style="display: block; text-decoration: none; color: #0078d4; border: 1px solid #0078d4; padding: 6px; border-radius: 5px; font-size: 11px; text-align: center; background-color: white; font-weight: bold;">📧 AGENDAR NO OUTLOOK</a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
