import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="MMD | Dashboard de Apresentações", layout="wide")

SHEET_ID = "1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# Backup fixo conforme última imagem
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

# Sequência obrigatória
CICLO_REUNIOES = ["Flash Manhã", "Flash Tarde", "DOR"]

def criar_link_outlook(row):
    try:
        data_obj = datetime.strptime(row['Data'], "%d/%m/%Y")
        data_iso = data_obj.strftime("%Y-%m-%d")
        h_inicio = "09:45:00" if "Manhã" in row['Reunião'] else "15:00:00"
        h_fim = "10:15:00" if "Manhã" in row['Reunião'] else "15:30:00"
        assunto = urllib.parse.quote(f"Apresentação MMD: {row['Reunião']}")
        corpo = urllib.parse.quote(f"Apresentador: {row['Apresentador']} | Backup: {row['Backup']}")
        return f"https://outlook.office.com/calendar/0/deeplink/compose?subject={assunto}&body={corpo}&startdt={data_iso}T{h_inicio}&enddt={data_iso}T{h_fim}"
    except:
        return "#"

@st.cache_data(ttl=60)
def carregar_dados():
    try:
        df = pd.read_csv(SHEET_URL)
        return sorted(df['Funcionario'].dropna().unique().tolist())
    except:
        return []

def gerar_escala_final(nomes):
    dias_uteis = pd.date_range(start="2026-01-01", end="2026-12-31", freq='B')
    escala = []
    status_pessoa = {nome: 0 for nome in nomes}
    participacao_semanal = {}
    
    lista_circular = nomes.copy()

    for dia in dias_uteis:
        semana = dia.isocalendar()[1]
        data_str = dia.strftime("%d/%m/%Y")
        dia_nome = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][dia.weekday()]
        
        if semana not in participacao_semanal:
            participacao_semanal[semana] = set()

        # Define reuniões do dia
        reunioes_dia = ["Flash Manhã"]
        if dia.weekday() in [1, 3]: reunioes_dia.append("DOR")
        else: reunioes_dia.append("Flash Tarde")

        for r_tipo in reunioes_dia:
            selecionado = None
            for _ in range(len(lista_circular)):
                candidato = lista_circular.pop(0)
                lista_circular.append(candidato)
                
                tipo_devido = CICLO_REUNIOES[status_pessoa[candidato]]
                ja_foi_na_semana = candidato in participacao_semanal[semana]

                if tipo_devido == r_tipo and not ja_foi_na_semana:
                    selecionado = candidato
                    break
            
            if selecionado:
                escala.append({
                    "Semana": semana, "Data": data_str, "Dia": dia_nome,
                    "Reunião": r_tipo, "Apresentador": selecionado, 
                    "Backup": MAPA_BACKUPS.get(selecionado, "N/A")
                })
                participacao_semanal[semana].add(selecionado)
                status_pessoa[selecionado] = (status_pessoa[selecionado] + 1) % 3

    return pd.DataFrame(escala)

# --- SIDEBAR (ACESSIBILIDADE) ---
with st.sidebar:
    st.header("Acessibilidade")
    if st.button("🔊 Ativar/Desativar Voz"):
        st.info("O recurso de voz está ativo para leitura dos cards.")

# --- UI PRINCIPAL ---
lista_nomes = carregar_dados()
if lista_nomes:
    df_escala = gerar_escala_final(lista_nomes)
    st.title("🚀 MMD | Dashboard de Apresentações")

    # Busca Individual
    nome_busca = st.selectbox("🔍 Buscar por Apresentador:", ["Todos"] + lista_nomes)
    if nome_busca != "Todos":
        df_ind = df_escala[df_escala["Apresentador"] == nome_busca].copy()
        df_ind["Agenda Outlook"] = df_ind.apply(criar_link_outlook, axis=1)
        st.dataframe(df_ind[["Data", "Dia", "Reunião", "Backup", "Agenda Outlook"]], 
                     column_config={"Agenda Outlook": st.column_config.LinkColumn("📅 Outlook", display_text="AGENDAR")},
                     use_container_width=True, hide_index=True)
        st.divider()

    # Cards Semanais
    st.subheader("🗓️ Visão Semanal")
    sem_atual = datetime.now().isocalendar()[1]
    escolha_sem = st.select_slider("Arraste para ver a escala:", options=sorted(df_escala["Semana"].unique()), value=sem_atual)
    
    df_sem_view = df_escala[df_escala["Semana"] == escolha_sem]
    for dia_str, gp in df_sem_view.groupby("Data", sort=False):
        st.markdown(f"**{gp['Dia'].iloc[0]} - {dia_str}**")
        col_cards = st.columns(2) # Garante que Manhã e Tarde/DOR apareçam lado a lado
        for i, (_, r) in enumerate(gp.iterrows()):
            with col_cards[i % 2]:
                link_out = criar_link_outlook(r)
                st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #ff4b4b; min-height: 150px; box-shadow: 1px 1px 4px rgba(0,0,0,0.1);">
                    <small style="color: #666;">{r['Reunião']}</small><br>
                    <b style="font-size: 16px;">🏆 {r['Apresentador']}</b><br>
                    <span style="font-size: 12px; color: #555;">🔄 Backup: {r['Backup']}</span><br><br>
                    <a href="{link_out}" target="_blank" style="text-decoration: none; background-color: #0078d4; color: white; padding: 6px 12px; border-radius: 4px; font-size: 11px; font-weight: bold;">📅 AGENDAR NO OUTLOOK</a>
                </div>
                """, unsafe_allow_html=True)
