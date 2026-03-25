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
    idx_flash = 0
    idx_dor = 0
    
    # Dicionário para rastrear quem já apresentou na semana
    # Chave: número da semana, Valor: set de nomes
    participacao_semanal = {}

    for dia in dias:
        semana = dia.isocalendar()[1]
        dia_semana = dia.weekday()
        
        if semana not in participacao_semanal:
            participacao_semanal[semana] = set()

        # 1. SLOT MANHÃ (Flash Manhã)
        nome_flash_manha = nomes[idx_flash % len(nomes)]
        escala.append({
            "Semana": semana,
            "Data": dia.strftime("%d/%m/%Y"),
            "Dia": ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][dia_semana],
            "Reunião": "Flash Manhã",
            "Apresentador": nome_flash_manha
        })
        participacao_semanal[semana].add(nome_flash_manha)
        idx_flash += 1
        
        # 2. SLOT TARDE
        if dia_semana in [1, 3]: # Terça e Quinta (DOR)
            while True:
                nome_dor = nomes[idx_dor % len(nomes)]
                # REGRA: Não pode ser Dani/Rafael E não pode ter apresentado na semana
                if nome_dor in ["Dani", "Rafael"] or nome_dor in participacao_semanal[semana]:
                    idx_dor += 1
                    continue
                
                escala.append({
                    "Semana": semana,
                    "Data": dia.strftime("%d/%m/%Y"),
                    "Dia": ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][dia_semana],
                    "Reunião": "DOR",
                    "Apresentador": nome_dor
                })
                participacao_semanal[semana].add(nome_dor)
                idx_dor += 1
                break
        else: # Segunda, Quarta e Sexta (Flash Tarde)
            nome_flash_tarde = nomes[idx_flash % len(nomes)]
            escala.append({
                "Semana": semana,
                "Data": dia.strftime("%d/%m/%Y"),
                "Dia": ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][dia_semana],
                "Reunião": "Flash Tarde",
                "Apresentador": nome_flash_tarde
            })
            participacao_semanal[semana].add(nome_flash_tarde)
            idx_flash += 1
            
    return pd.DataFrame(escala)

if check_login():
    nomes_lista = carregar_nomes()
    if nomes_lista:
        df_total = gerar_escala(nomes_lista)
        
        # --- ACESSIBILIDADE ---
        if "voz" not in st.session_state:
            st.session_state.voz = False
            
        st.sidebar.title("Acessibilidade")
        if st.sidebar.button("🔊 Voz On/Off"):
            st.session_state.voz = not st.session_state.voz
            st.rerun()
            
        st.title("🚀 MMD | Dashboard de Apresentações")
        
        opcoes_nomes = ["Todos"] + nomes_lista
        filtro_nome = st.selectbox("🔍 Buscar por Apresentador:", opcoes_nomes)
        
        if filtro_nome != "Todos":
            st.markdown(f"### 📅 Minhas Apresentações no Ano: {filtro_nome}")
            df_pessoal = df_total[df_total["Apresentador"] == filtro_nome].copy()
            df_pessoal["Outlook"] = df_pessoal.apply(lambda x: criar_link_outlook(x["Data"], x["Reunião"], x["Apresentador"]), axis=1)
            
            st.dataframe(
                df_pessoal[["Data", "Dia", "Reunião", "Semana", "Outlook"]],
                use_container_width=True,
                hide_index=True,
                column_config={"Outlook": st.column_config.LinkColumn("📧 Agendar")}
            )
            st.markdown("---")

        st.subheader("🗓️ Cronograma por Semana")
        semana_atual = datetime.now().isocalendar()[1]
        lista_semanas = sorted(df_total["Semana"].unique())
        semana_busca = st.select_slider("Selecione a Semana:", options=lista_semanas, value=semana_atual if semana_atual in lista_semanas else lista_semanas[0])
        
        df_semana = df_total[df_total["Semana"] == semana_busca]

        for data_label, group in df_semana.groupby("Data", sort=False):
            st.markdown(f"**{group['Dia'].iloc[0]} - {data_label}**")
            cols = st.columns(len(group))
            for i, (_, row) in enumerate(group.iterrows()):
                with cols[i]:
                    o_link = criar_link_outlook(row['Data'], row['Reunião'], row['Apresentador'])
                    st.markdown(f"""
                    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; min-height: 160px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                        <div>
                            <b style="font-size: 15px; color: #31333F;">{row['Reunião']}</b><br>
                            <span style="font-size: 17px; color: #333; font-weight: bold;">
                                <span style="font-size: 20px;">🏆</span> {row['Apresentador']}
                            </span>
                        </div>
                        <div style="margin-top: 15px;">
                            <a href="{o_link}" target="_blank" style="display: block; text-decoration: none; color: #0078d4; border: 1px solid #0078d4; padding: 8px; border-radius: 5px; font-size: 11px; text-align: center; background-color: white; font-weight: bold; width: 100%;">📧 AGENDAR NO OUTLOOK</a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            st.write("")
