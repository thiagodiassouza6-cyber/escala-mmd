import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="MMD | Dashboard", layout="wide")

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

# Sequência obrigatória definida
SEQUENCIA_REUNIOES = ["Flash Manhã", "Flash Tarde", "DOR"]

def criar_link_outlook(data_str, reuniao, apresentador):
    try:
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        data_iso = data_obj.strftime("%Y-%m-%d")
        hora_start = "09:45:00" if "Manhã" in reuniao else "15:00:00"
        hora_end = "10:15:00" if "Manhã" in reuniao else "15:30:00"
        assunto = urllib.parse.quote(f"🔔 Apresentação MMD: {reuniao}")
        corpo = urllib.parse.quote(f"Apresentador: {apresentador} | Backup: {MAPA_BACKUPS.get(apresentador, 'N/A')}")
        return f"https://outlook.office.com/calendar/0/deeplink/compose?subject={assunto}&body={corpo}&startdt={data_iso}T{hora_start}&enddt={data_iso}T{hora_end}"
    except:
        return "#"

@st.cache_data(ttl=60)
def carregar_nomes():
    try:
        df = pd.read_csv(SHEET_URL)
        return sorted(df['Funcionario'].dropna().unique().tolist())
    except:
        return []

def gerar_escala_sequencial(nomes):
    ano = 2026
    dias = pd.date_range(datetime(ano, 1, 1), datetime(ano, 12, 31), freq='B')
    
    escala = []
    # Controle de qual reunião cada pessoa deve fazer em seguida (0, 1 ou 2)
    proxima_reuniao_index = {nome: 0 for nome in nomes}
    participacao_semanal = {}
    
    # Ponteiro para circular entre os nomes
    idx_nome = 0

    for dia in dias:
        semana = dia.isocalendar()[1]
        dia_semana = dia.weekday()
        if semana not in participacao_semanal:
            participacao_semanal[semana] = set()

        # Reuniões disponíveis no dia
        reunioes_dia = ["Flash Manhã"]
        if dia_semana in [1, 3]: reunioes_dia.append("DOR")
        else: reunioes_dia.append("Flash Tarde")

        for r_tipo in reunioes_dia:
            tentativas = 0
            while tentativas < len(nomes):
                nome_candidato = nomes[idx_nome % len(nomes)]
                tipo_devido = SEQUENCIA_REUNIOES[proxima_reuniao_index[nome_candidato]]
                
                # Regras: Deve ser o tipo certo de reunião E não pode ter apresentado na semana
                pode_apresentar = (tipo_devido == r_tipo) and (nome_candidato not in participacao_semanal[semana])
                
                # Trava extra para nomes específicos no DOR
                if r_tipo == "DOR" and nome_candidato in ["Dani", "Rafael"]:
                    pode_apresentar = False

                if pode_apresentar:
                    escala.append({
                        "Semana": semana, "Data": dia.strftime("%d/%m/%Y"),
                        "Dia": ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][dia_semana],
                        "Reunião": r_tipo, "Apresentador": nome_candidato,
                        "Backup": MAPA_BACKUPS.get(nome_candidato, "N/A")
                    })
                    participacao_semanal[semana].add(nome_candidato)
                    # Avança a sequência dessa pessoa
                    proxima_reuniao_index[nome_candidato] = (proxima_reuniao_index[nome_candidato] + 1) % 3
                    idx_nome += 1
                    break
                else:
                    idx_nome += 1
                    tentativas += 1
                    
    return pd.DataFrame(escala)

# --- INTERFACE ---
nomes_lista = carregar_nomes()
if nomes_lista:
    df_total = gerar_escala_sequencial(nomes_lista)

    st.title("🚀 MMD | Dashboard de Apresentações")
    
    # Filtro Individual
    filtro_nome = st.selectbox("🔍 Buscar por Apresentador:", ["Todos"] + nomes_lista)
    
    if filtro_nome != "Todos":
        st.subheader(f"📅 Escala Individual: {filtro_nome}")
        df_pessoal = df_total[df_total["Apresentador"] == filtro_nome].copy()
        
        # Gerar coluna de link Outlook
        df_pessoal["Agenda Outlook"] = df_pessoal.apply(lambda x: criar_link_outlook(x['Data'], x['Reunião'], x['Apresentador']), axis=1)
        
        # Exibição da Tabela com Backup na 4ª coluna e Botão na 5ª
        st.dataframe(
            df_pessoal[["Data", "Dia", "Reunião", "Backup", "Agenda Outlook"]],
            column_config={
                "Agenda Outlook": st.column_config.LinkColumn("📅 Agendar", display_text="Adicionar ao Outlook")
            },
            use_container_width=True, hide_index=True
        )
        st.divider()

    # Cards Semanais
    st.subheader("🗓️ Cronograma Semanal")
    semana_sel = st.select_slider("Arraste para ver a escala:", options=sorted(df_total["Semana"].unique()), value=datetime.now().isocalendar()[1])
    
    df_semana = df_total[df_total["Semana"] == semana_sel]
    for data_label, group in df_semana.groupby("Data", sort=False):
        st.markdown(f"**{group['Dia'].iloc[0]} - {data_label}**")
        cols = st.columns(len(group))
        for i, (_, row) in enumerate(group.iterrows()):
            with cols[i]:
                link = criar_link_outlook(row['Data'], row['Reunião'], row['Apresentador'])
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; min-height: 160px;">
                    <b style="color: #31333F;">{row['Reunião']}</b><br>
                    <span style="font-size: 18px; font-weight: bold;">🏆 {row['Apresentador']}</span><br>
                    <span style="font-size: 13px; color: #666;">🔄 Backup: {row['Backup']}</span><br><br>
                    <a href="{link}" target="_blank" style="text-decoration: none; color: white; background-color: #0078d4; padding: 5px 10px; border-radius: 5px; font-size: 11px; font-weight: bold;">📅 AGENDAR</a>
                </div>
                """, unsafe_allow_html=True)
