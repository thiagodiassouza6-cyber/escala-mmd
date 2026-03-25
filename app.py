import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Dashboard de Escalas", layout="wide")

SHEET_ID = "1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# Mapa de Backups Atualizado
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
        df_base = pd.read_csv(SHEET_URL)
        return sorted(df_base['Funcionario'].dropna().unique().tolist())
    except:
        return []

def gerar_escala_completa(nomes):
    dias_uteis = pd.date_range(start="2026-01-01", end="2026-12-31", freq='B')
    escala_final = []
    status_pessoa = {nome: 0 for nome in nomes}
    participacao_semanal = {}

    for dia in dias_uteis:
        semana = dia.isocalendar()[1]
        data_str = dia.strftime("%d/%m/%Y")
        dia_nome = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][dia.weekday()]
        
        if semana not in participacao_semanal:
            participacao_semanal[semana] = set()

        # GARANTIA: Flash Manhã sempre incluída em todos os dias úteis
        reunioes_dia = ["Flash Manhã"]
        if dia.weekday() in [1, 3]: # Terça e Quinta
            reunioes_dia.append("DOR")
        else: # Segunda, Quarta e Sexta
            reunioes_dia.append("Flash Tarde")

        for r_tipo in reunioes_dia:
            selecionado = None
            for _ in range(len(nomes)):
                candidato = nomes.pop(0)
                nomes.append(candidato)
                
                tipo_devido = CICLO_REUNIOES[status_pessoa[candidato]]
                na_semana = candidato in participacao_semanal[semana]
                bloqueio_dor = (r_tipo == "DOR" and candidato in ["Dani", "Rafael"])

                if tipo_devido == r_tipo and not na_semana and not bloqueio_dor:
                    selecionado = candidato
                    break
            
            if selecionado:
                escala_final.append({
                    "Semana": semana, "Data": data_str, "Dia": dia_nome,
                    "Reunião": r_tipo, "Apresentador": selecionado, 
                    "Backup": MAPA_BACKUPS.get(selecionado, "N/A")
                })
                participacao_semanal[semana].add(selecionado)
                status_pessoa[selecionado] = (status_pessoa[selecionado] + 1) % 3

    return pd.DataFrame(escala_final)

# --- UI ---
lista_nomes = carregar_dados()
if lista_nomes:
    df_escala = gerar_escala_completa(lista_nomes)
    st.title("🚀 MMD | Dashboard de Apresentações")

    # Filtro Individual
    nome_busca = st.selectbox("🔍 Buscar por Apresentador:", ["Todos"] + lista_nomes)
    if nome_busca != "Todos":
        df_ind = df_escala[df_escala["Apresentador"] == nome_busca].copy()
        df_ind["Agenda Outlook"] = df_ind.apply(criar_link_outlook, axis=1)
        st.dataframe(df_ind[["Data", "Dia", "Reunião", "Backup", "Agenda Outlook"]], 
                     column_config={"Agenda Outlook": st.column_config.LinkColumn("📅 Outlook", display_text="AGENDAR")},
                     use_container_width=True, hide_index=True)
        st.divider()

    # Cards Semanais (Corrigidos)
    st.subheader("🗓️ Visão Semanal")
    escolha_sem = st.select_slider("Selecione a Semana:", options=sorted(df_escala["Semana"].unique()), value=datetime.now().isocalendar()[1])
    
    df_sem_view = df_escala[df_escala["Semana"] == escolha_sem]
    for dia_str, gp in df_sem_view.groupby("Data", sort=False):
        st.markdown(f"**{gp['Dia'].iloc[0]} - {dia_str}**")
        col_cards = st.columns(len(gp))
        for i, (_, r) in enumerate(gp.iterrows()):
            with col_cards[i]:
                link_out = criar_link_outlook(r)
                st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #ff4b4b; min-height: 150px; box-shadow: 1px 1px 4px rgba(0,0,0,0.1);">
                    <small style="color: #666;">{r['Reunião']}</small><br>
                    <b style="font-size: 16px;">🏆 {r['Apresentador']}</b><br>
                    <span style="font-size: 12px; color: #555;">🔄 Backup: {r['Backup']}</span><br><br>
                    <a href="{link_out}" target="_blank" style="text-decoration: none; background-color: #0078d4; color: white; padding: 5px 10px; border-radius: 4px; font-size: 10px; font-weight: bold;">📅 AGENDAR</a>
                </div>
                """, unsafe_allow_html=True)
