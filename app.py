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

MAPA_BACKUPS = {
    "Abigail": "Sonia", "Amanda": "Mijal", "Anna": "Soledad", 
    "Ariel": "Rafael", "Bianca M.": "Ariel", "Bianca S.": "Amanda", 
    "Bruna": "Anna Laura", "Bruno": "Bianca M.", "Enrique": "Jazmin", 
    "Debora": "Bruna", "Diana": "Julia", "Faiha": "Bianca S.", 
    "Florencia": "Diana", "Gisele": "Thiago", "Honorato": "Bruno", 
    "Jazmin": "Abigail", "Jesus": "Luca", "Julia": "Honorato", 
    "Livia": "Faiha", "Luca": "Enrique", "Mijal": "Livia", 
    "Rafael": "Florencia", "Renan": "Debora", "Sonia": "Jesus", 
    "Soledad": "Gisele", "Thiago": "Renan"
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

def gerar_escala_justa(nomes):
    ano_atual = datetime.now().year
    data_inicio = datetime(ano_atual, 1, 1)
    data_fim = datetime(ano_atual, 12, 31)
    dias = pd.date_range(data_inicio, data_fim, freq='B')
    
    escala = []
    idx_fila = 0 # Ponteiro da fila única
    
    # Controle para evitar que a mesma pessoa apresente 2x na semana
    participacao_semanal = {} 

    for dia in dias:
        semana = dia.isocalendar()[1]
        dia_semana = dia.weekday()
        if semana not in participacao_semanal:
            participacao_semanal[semana] = set()

        # Define as reuniões do dia
        reunioes_dia = ["Flash Manhã"]
        if dia_semana in [1, 3]: reunioes_dia.append("DOR")
        else: reunioes_dia.append("Flash Tarde")

        for r_tipo in reunioes_dia:
            tentativas = 0
            encontrou = False
            
            while tentativas < len(nomes):
                candidato = nomes[idx_fila % len(nomes)]
                
                # Regra 1: Não pode repetir na mesma semana
                ja_foi_na_semana = candidato in participacao_semanal[semana]
                # Regra 2: Dani e Rafael não fazem DOR
                bloqueio_especial = (r_tipo == "DOR" and candidato in ["Dani", "Rafael"])

                if not ja_foi_na_semana and not bloqueio_especial:
                    escala.append({
                        "Semana": semana, "Data": dia.strftime("%d/%m/%Y"),
                        "Dia": ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][dia_semana],
                        "Reunião": r_tipo, "Apresentador": candidato,
                        "Backup": MAPA_BACKUPS.get(candidato, "N/A"),
                        "Link": criar_link_outlook(dia.strftime("%d/%m/%Y"), r_tipo, candidato)
                    })
                    participacao_semanal[semana].add(candidato)
                    idx_fila += 1 # Move para o próximo da fila
                    encontrou = True
                    break
                else:
                    # Se ele não pode (por ser DOR ou já ter ido na semana), 
                    # tentamos o próximo da fila para ESTA vaga, mas não avançamos o idx_fila global
                    # para que o pulado seja o primeiro da lista na próxima vaga disponível.
                    idx_fila += 1
                    tentativas += 1
            
            # Se a fila travar (ex: todos já foram na semana), libera a repetição
            if not encontrou:
                candidato = nomes[idx_fila % len(nomes)]
                escala.append({
                    "Semana": semana, "Data": dia.strftime("%d/%m/%Y"),
                    "Reunião": r_tipo, "Apresentador": candidato,
                    "Backup": MAPA_BACKUPS.get(candidato, "N/A"),
                    "Link": criar_link_outlook(dia.strftime("%d/%m/%Y"), r_tipo, candidato)
                })
                idx_fila += 1

    return pd.DataFrame(escala)

def renderizar_card(row):
    audio_text = f"Reunião: {row['Reunião']}. Apresentador: {row['Apresentador']}. Backup: {row['Backup']}."
    st.markdown(f"""
    <div class="card-click" data-audio="{audio_text}" style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; min-height: 190px; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
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
        df_total = gerar_escala_justa(nomes_lista)
        
        # --- ACESSIBILIDADE ---
        if "voz" not in st.session_state: st.session_state.voz = False
        st.sidebar.title("Configurações")
        if st.sidebar.button("🔊 Acessibilidade (Voz)"):
            st.session_state.voz = not st.session_state.voz
            st.rerun()
            
        if st.session_state.voz:
            components.html("""
                <script>
                const synth = window.speechSynthesis;
                function speak(text) {
                    if (synth.speaking) { synth.cancel(); }
                    const utter = new SpeechSynthesisUtterance(text);
                    utter.lang = 'pt-BR';
                    synth.speak(utter);
                }
                setTimeout(() => {
                    parent.document.querySelectorAll('.card-click').forEach(card => {
                        card.addEventListener('mouseenter', () => speak(card.getAttribute('data-audio')));
                    });
                }, 1000);
                </script>
            """, height=0)

        st.title("🚀 MMD | Dashboard de Apresentações")
        
        # --- FILTRO POR APRESENTADOR ---
        opcoes_nomes = ["Todos"] + nomes_lista
        filtro_nome = st.selectbox("🔍 Buscar por Apresentador:", opcoes_nomes)
        
        if filtro_nome != "Todos":
            st.markdown(f"### 📅 Lista de Apresentações: {filtro_nome}")
            df_pessoal = df_total[df_total["Apresentador"] == filtro_nome].copy()
            st.data_editor(
                df_pessoal[["Data", "Reunião", "Apresentador", "Backup", "Link"]],
                column_config={
                    "Link": st.column_config.LinkColumn("Agenda Outlook", display_text="📅 AGENDAR"),
                    "Data": st.column_config.TextColumn("Data"),
                },
                hide_index=True, use_container_width=True, disabled=True
            )
            st.markdown("---")

        # --- CRONOGRAMA SEMANAL ---
        st.subheader("🗓️ Visualização por Semana")
        semana_atual = datetime.now().isocalendar()[1]
        lista_semanas = sorted(df_total["Semana"].unique())
        semana_busca = st.select_slider("Selecione a Semana:", options=lista_semanas, value=semana_atual if semana_atual in lista_semanas else lista_semanas[0])
        
        df_semana = df_total[df_total["Semana"] == semana_busca]
        for data_label, group in df_semana.groupby("Data", sort=False):
            st.markdown(f"**{group['Dia'].iloc[0] if 'Dia' in group.columns else ''} - {data_label}**")
            cols = st.columns(len(group))
            for i, (_, row) in enumerate(group.iterrows()):
                with cols[i]:
                    renderizar_card(row)

        # --- ESCALA COMPLETA ---
        st.markdown("---")
        with st.expander("📂 Ver Escala Completa (Todos os Dias)"):
            for data_label, group in df_total.groupby("Data", sort=False):
                st.write(f"Data: {data_label}")
                cols_full = st.columns(5)
                for i, (_, row) in enumerate(group.iterrows()):
                    with cols_full[i % 5]:
                        renderizar_card(row)
