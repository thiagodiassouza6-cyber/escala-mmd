import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Escala de Apresentações", layout="wide")

# Link da Planilha Atualizado
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

def criar_link_agenda(data_str, reuniao, apresentador):
    try:
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        hora = "094500" if "Manhã" in reuniao else "150000"
        data_formatada = data_obj.strftime("%Y%m%d")
        inicio = f"{data_formatada}T{hora}"
        fim_obj = datetime.strptime(inicio, "%Y%m%dT%H%M%S") + timedelta(minutes=30)
        fim = fim_obj.strftime("%Y%m%dT%H%M%S")
        titulo = urllib.parse.quote(f"🔔 Apresentação MMD: {reuniao}")
        detalhes = urllib.parse.quote(f"Apresentador: {apresentador}\nLembrete de 60 min.")
        return f"https://www.google.com/calendar/render?action=TEMPLATE&text={titulo}&dates={inicio}/{fim}&details={detalhes}"
    except:
        return "#"

@st.cache_data(ttl=60)
def carregar_nomes():
    try:
        df_sheets = pd.read_csv(SHEET_URL)
        # Ajustado para o nome exato da sua coluna na planilha
        return sorted(df_sheets['Funcionários'].dropna().unique().tolist())
    except Exception as e:
        st.error(f"Erro ao carregar planilha: {e}")
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
                # Regra para evitar Dani ou Rafael no DOR
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
        st.title("🚀 MMD | Dashboard de Apresentações")
        
        opcoes_nomes = ["Todos"] + nomes_lista
        filtro_nome = st.selectbox("🔍 Buscar por Apresentador (Lista Anual):", opcoes_nomes)
        
        if st.sidebar.button("🔄 Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()

        if filtro_nome != "Todos":
            st.markdown("---")
            st.subheader(f"📅 Cronograma Anual: {filtro_nome}")
            df_pessoal = df_total[df_total["Apresentador"] == filtro_nome].copy()
            df_pessoal["Agenda"] = df_pessoal.apply(lambda x: criar_link_agenda(x["Data"], x["Reunião"], x["Apresentador"]), axis=1)
            
            st.dataframe(
                df_pessoal[["Data", "Dia", "Reunião", "Semana", "Agenda"]],
                use_container_width=True,
                hide_index=True,
                column_config={"Agenda": st.column_config.LinkColumn("📅 Add Google")}
            )
        else:
            st.markdown("---")
            st.subheader("🗓️ Cronograma por Semana")
            semana_busca = st.select_slider("Arraste para ver a escala:", options=sorted(df_total["Semana"].unique()), value=13)
            df_semana = df_total[df_total["Semana"] == semana_busca]

            # Cards com tratamento de erro
            for data_label, group in df_semana.groupby("Data", sort=False):
                st.markdown(f"**{group['Dia'].iloc[0]} - {data_label}**")
                cols = st.columns(len(group))
                for i, (_, row) in enumerate(group.iterrows()):
                    with cols[i]:
                        link = criar_link_agenda(row['Data'], row['Reunião'], row['Apresentador'])
                        # HTML simplificado para evitar quebras
                        card_html = f"""
                        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 8px; border-left: 5px solid #ff4b4b; min-height: 120px;">
                            <b style="font-size: 14px;">{row['Reunião']}</b><br>
                            <span style="font-size: 13px;">🏆 {row['Apresentador']}</span><br><br>
                            <a href="{link}" target="_blank" style="font-size: 12px; color: #ff4b4b; text-decoration: none; border: 1px solid #ff4b4b; padding: 2px 5px; border-radius: 4px;">🔔 Agenda</a>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
                st.write("")
