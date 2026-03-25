import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Gestão de Escalas", layout="wide")

# Dados de conexão e Backups atualizados
SHEET_ID = "1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

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

# Definição da sequência obrigatória
CICLO_REUNIOES = ["Flash Manhã", "Flash Tarde", "DOR"]

def criar_link_outlook(row):
    try:
        data_obj = datetime.strptime(row['Data'], "%d/%m/%Y")
        data_iso = data_obj.strftime("%Y-%m-%d")
        # Horários padrão
        h_inicio = "09:45:00" if "Manhã" in row['Reunião'] else "15:00:00"
        h_fim = "10:15:00" if "Manhã" in row['Reunião'] else "15:30:00"
        
        assunto = urllib.parse.quote(f"Apresentação MMD: {row['Reunião']}")
        corpo = urllib.parse.quote(f"Apresentador: {row['Apresentador']}\nBackup: {row['Backup']}")
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

def gerar_escala_inteligente(nomes):
    dias_uteis = pd.date_range(start="2026-01-01", end="2026-12-31", freq='B')
    escala_final = []
    
    # Rastreia o progresso individual no ciclo (0=Manhã, 1=Tarde, 2=DOR)
    status_pessoa = {nome: 0 for nome in nomes}
    participacao_semanal = {}

    for dia in dias_uteis:
        semana = dia.isocalendar()[1]
        dia_nome = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][dia.weekday()]
        data_str = dia.strftime("%d/%m/%Y")
        
        if semana not in participacao_semanal:
            participacao_semanal[semana] = set()

        # Define quais reuniões ocorrem no dia
        reunioes_do_dia = ["Flash Manhã"]
        if dia.weekday() in [1, 3]: # Terça e Quinta
            reunioes_do_dia.append("DOR")
        else: # Segunda, Quarta e Sexta
            reunioes_do_dia.append("Flash Tarde")

        for r_tipo in reunioes_do_dia:
            # Busca alguém que precise fazer ESSE tipo de reunião e não tenha participado na semana
            selecionado = None
            # Tenta encontrar o próximo da fila que se encaixe no perfil
            for _ in range(len(nomes)):
                # Pegamos o primeiro nome da lista e movemos para o final (Round Robin)
                candidato = nomes.pop(0)
                nomes.append(candidato)
                
                tipo_necessario = CICLO_REUNIOES[status_pessoa[candidato]]
                ja_fez_na_semana = candidato in participacao_semanal[semana]
                
                if tipo_necessario == r_tipo and not ja_fez_na_semana:
                    selecionado = candidato
                    break
            
            if selecionado:
                backup_nome = MAPA_BACKUPS.get(selecionado, "N/A")
                escala_final.append({
                    "Semana": semana, "Data": data_str, "Dia": dia_nome,
                    "Reunião": r_tipo, "Apresentador": selecionado, "Backup": backup_nome
                })
                participacao_semanal[semana].add(selecionado)
                status_pessoa[selecionado] = (status_pessoa[selecionado] + 1) % 3

    return pd.DataFrame(escala_final)

# --- EXECUÇÃO ---
lista_nomes = carregar_dados()
if lista_nomes:
    df_escala = gerar_escala_inteligente(lista_nomes)
    
    st.title("🚀 MMD | Dashboard de Apresentações")

    # Filtro de Busca
    nome_busca = st.selectbox("🔍 Buscar por Apresentador:", ["Todos"] + lista_nomes)
    
    if nome_busca != "Todos":
        st.subheader(f"📅 Agenda Individual: {nome_busca}")
        df_filtrado = df_escala[df_escala["Apresentador"] == nome_busca].copy()
        
        # Inserção do Botão Outlook
        df_filtrado["Agenda Outlook"] = df_filtrado.apply(criar_link_outlook, axis=1)
        
        st.dataframe(
            df_filtrado[["Data", "Dia", "Reunião", "Backup", "Agenda Outlook"]],
            column_config={
                "Agenda Outlook": st.column_config.LinkColumn("📅 Outlook", display_text="AGENDAR")
            },
            use_container_width=True, hide_index=True
        )
        st.divider()

    # Visualização de Cards Semanais
    st.subheader("🗓️ Visão Semanal")
    sem_atual = datetime.now().isocalendar()[1]
    escolha_sem = st.select_slider("Selecione a Semana:", options=sorted(df_escala["Semana"].unique()), value=sem_atual)
    
    df_sem_view = df_escala[df_escala["Semana"] == escolha_sem]
    
    for dia_str, gp in df_sem_view.groupby("Data", sort=False):
        st.markdown(f"**{gp['Dia'].iloc[0]} - {dia_str}**")
        col_cards = st.columns(len(gp))
        for i, (_, r) in enumerate(gp.iterrows()):
            with col_cards[i]:
                link_out = criar_link_outlook(r)
                st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #ff4b4b; box-shadow: 1px 1px 4px rgba(0,0,0,0.1);">
                    <small style="color: #666;">{r['Reunião']}</small><br>
                    <b style="font-size: 16px;">🏆 {r['Apresentador']}</b><br>
                    <span style="font-size: 12px; color: #555;">🔄 Backup: {r['Backup']}</span><br><br>
                    <a href="{link_out}" target="_blank" style="text-decoration: none; background-color: #0078d4; color: white; padding: 4px 8px; border-radius: 4px; font-size: 10px; font-weight: bold;">📅 AGENDAR</a>
                </div>
                """, unsafe_allow_html=True)
