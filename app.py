import streamlit as st

# Mude para True para tirar o app do ar e False para voltar ao normal
MODO_MANUTENCAO = False 

if MODO_MANUTENCAO:
    st.title("🚧 Portal MMD 🚧")
    st.subheader("Sistema em Manutenção")
    st.info("Estamos atualizando a base de dados e inserindo os novos colaboradores. O portal estará de volta em breve com novidades!")
    st.image("https://cdn-icons-png.flaticon.com/512/3251/3251465.png", width=200) # Opcional: ícone de engrenagem/construção
    st.stop() # Esta função interrompe a execução do restante do código do app

# --- O RESTANTE DO SEU CÓDIGO DO PORTAL FICA AQUI ABAIXO ---

import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import streamlit.components.v1 as components
import io
import random

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Portal de Escalas", layout="wide")

# --- DICIONÁRIO DE TRADUÇÃO ---
I18N = {
    "PT": {
        "lang_code": "pt-BR",
        "titulo": "🚀 MMD | Portal de Escalas 2026",
        "login_tit": "Portal de Escalas MMD",
        "usuario": "Usuário",
        "senha": "Senha",
        "acessar": "Acessar Painel",
        "acessibilidade": "Ativar Acessibilidade",
        "roteiro_ter": "📝 Roteiro Terça: Práticas + Iniciativas",
        "roteiro_qui": "📝 Roteiro Quinta: Lead Time + SLA",
        "estrutura_tit": "👥 Estrutura de Times",
        "exp_mes": "📂 Exportar Mês",
        "exp_ano": "📅 Exportar Ano",
        "baixar": "Baixar",
        "buscar": "🔍 Buscar por Apresentador:",
        "todos": "Todos",
        "semana": "Semana:",
        "agendar": "📅 AGENDAR",
        "backup": "🔄 Backup",
        "backup2": "🛡️ Backup 2",
        "backup_oculto": "Backup Oculto",
        "stats": "📊 {nome}: {total} reuniões no ano (sendo {dor} reuniões DOR).",
        "reuniao": "Reunião",
        "flash_m": "Flash Manhã",
        "resp_m": "Responsável Manhã",
        "resp_t": "Responsável Tarde",
        "tipo_t": "Tipo Tarde/DOR",
        "mes_col": "Mês",
        "dias": ["Segunda-Feira", "Terça-Feira", "Quarta-Feira", "Quinta-Feira", "Sexta-Feira"],
        "meses": ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"],
        "pauta": {
            "lista": "📑 Lista de presença", "tk": "⏱ Timekeeper", "escala": "🗓 Escala", "behavior": "📈 Behavior",
            "plan": "🎯 Plano de ação", "prac": "✅ Práticas", "nps": "📊 NPS", "ini": "💡 Iniciativas",
            "track": "📉 Tracker", "work": "🛠 Work Plan", "issue": "⚠️ Issues", "she": "🛡 SHE",
            "lt": "🕒 Lead Time", "ftr": "✅ FTR", "cats": "📁 Cats+BH"
        }
    },
    "ES": {
        "lang_code": "es-ES",
        "titulo": "🚀 MMD | Portal de Escalas 2026",
        "login_tit": "Portal de Escalas MMD",
        "usuario": "Usuario",
        "senha": "Contraseña",
        "acessar": "Acceder al Panel",
        "acessibilidade": "Activar Accesibilidad",
        "roteiro_ter": "📝 Guion Martes: Prácticas + Iniciativas",
        "roteiro_qui": "📝 Guion Jueves: Lead Time + SLA",
        "estrutura_tit": "👥 Estructura de Equipos",
        "exp_mes": "📂 Exportar Mes",
        "exp_ano": "📅 Exportar Año",
        "baixar": "Descargar",
        "buscar": "🔍 Buscar por Presentador:",
        "todos": "Todos",
        "semana": "Semana:",
        "agendar": "📅 AGENDAR",
        "backup": "🔄 Backup",
        "backup2": "🛡️ Backup 2",
        "backup_oculto": "Backup Oculto",
        "stats": "📊 {nome}: {total} reuniones en el año ({dor} reuniones DOR).",
        "reuniao": "Reunión",
        "flash_m": "Flash Mañana",
        "resp_m": "Responsable Mañana",
        "resp_t": "Responsable Tarde",
        "tipo_t": "Tipo Tarde/DOR",
        "mes_col": "Mes",
        "dias": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
        "meses": ["Enero", "Febrero", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
        "pauta": {
            "lista": "📑 Lista de presencia", "tk": "⏱ Timekeeper", "escala": "🗓 Escala Horario", "behavior": "📈 Behavior",
            "plan": "🎯 Plan de accion", "prac": "✅ Practicas", "nps": "📊 NPS", "ini": "💡 Iniciativas",
            "track": "📉 Tracker", "work": "🛠 Work Plan", "issue": "⚠️ Issues", "she": "🛡 SHE",
            "lt": "🕒 Lead Time", "ftr": "✅ FTR", "cats": "📁 Cats+BH"
        }
    }
}

if "lang" not in st.session_state:
    st.session_state.lang = "PT"

t = I18N[st.session_state.lang]

# --- ACESSIBILIDADE ---
def injetar_leitor_acessibilidade(lang_code):
    components.html(f"""
        <script>
            const synth = window.speechSynthesis;
            let ultimoTexto = "";
            function falar(texto) {{
                if (!texto || texto === ultimoTexto) return;
                synth.cancel(); 
                const ut = new SpeechSynthesisUtterance(texto);
                ut.lang = '{lang_code}';
                ut.rate = 1.1;
                ultimoTexto = texto;
                synth.speak(ut);
                setTimeout(() => {{ ultimoTexto = ""; }}, 800);
            }}
            const docAlvo = window.parent.document;
            docAlvo.addEventListener('mouseover', (e) => {{
                const el = e.target;
                const textoParaLer = (el.innerText || el.textContent).trim();
                if (textoParaLer.length > 0 && !textoParaLer.includes("http")) {{
                    falar(textoParaLer);
                }}
            }}, true);
            docAlvo.addEventListener('mouseout', () => {{ synth.cancel(); }}, true);
        </script>
    """, height=0, width=0)

# --- ESTRUTURA DOS TIMES E GRUPOS ---
indireto_br = ["Debora", "Dani", "Dyana", "Luca", "Bruno", "Thiago"]
fert_br = ["Amanda", "Douglas", "Renan", "Anna"]
crm_br = ["Julia", "Bruna"]
direto_br = ["Livia", "Rafael"]

direto_latam = ["Ariel", "Enrique", "Sonia", "Jazmin", "Gisele"]
fert_latam = ["Florencia", "Jesus", "Bianca M.", "Soledad", "Mijal", "German", "Sebastian", "Andrea", "Honorato", "Nathan", "Rocio"]

time_brasil_completo = sorted(list(set(indireto_br + fert_br + crm_br + direto_br)))
time_latam_completo = sorted(list(set(direto_latam + fert_latam)))
time_geral_completo = sorted(list(set(time_brasil_completo + time_latam_completo)))

# --- MOTOR DE REGRAS ---
SHEET_ID = "1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Backups"
USER_ACCESS = "MMD-Board"
PASS_ACCESS = "@MMD123#"

MAPA_REFERENCIA = {
    "Abigail": "Dani", "Amanda": "Mijal", "Anna Laura": "Soledad", "Ariel": "Rafael", 
    "Bianca M.": "Ariel", "Bruna": "Anna Laura", "Bruno": "Bianca M.", "Dani": "Jesus", 
    "Debora": "Bruna", "Diana": "Julia", "Florencia": "Diana", "Gisele": "Thiago", 
    "Honorato": "Bruno", "Jazmin": "Abigail", "Jesus": "Luca", "Julia": "Honorato", 
    "Livia": "Amanda", "Luca": "Jazmin", "Mijal": "Livia", "Rafael": "Florencia", 
    "Renan": "Debora", "Soledad": "Gisele", "Thiago": "Renan"
}

def encontrar_backup_vivo(nome, nomes_ativos):
    proximo = MAPA_REFERENCIA.get(nome)
    tentativas = 0
    while proximo and proximo not in nomes_ativos and tentativas < len(MAPA_REFERENCIA):
        proximo = MAPA_REFERENCIA.get(proximo)
        tentativas += 1
    return proximo if proximo in nomes_ativos else "Sem Backup Ativo"

def check_login():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown(f"<h2 style='text-align: center;'>{t['login_tit']}</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            with st.form("login"):
                u = st.text_input(t["usuario"]).strip()
                p = st.text_input(t["senha"], type="password").strip()
                if st.form_submit_button(t["acessar"], use_container_width=True):
                    if u == USER_ACCESS and p == PASS_ACCESS:
                        st.session_state.logged_in = True
                        st.rerun()
                    else: st.error("Acesso negado / Acceso denegado")
        return False
    return True

def gerar_escala_balanceada(nomes_br, nomes_latam):
    random.seed(42)
    
    fila_br = nomes_br.copy()
    fila_latam = nomes_latam.copy()
    random.shuffle(fila_br)
    random.shuffle(fila_latam)
    
    todos_nomes = sorted(list(set(nomes_br + nomes_latam)))
    nomes_dor = [n for n in todos_nomes if n not in ["Dani", "Rafael"]]
    random.shuffle(nomes_dor)
    
    cont_total = {n: 0 for n in todos_nomes}
    cont_dor = {n: 0 for n in nomes_dor}
    
    dias_range = pd.date_range(datetime(2026, 1, 1), datetime(2026, 12, 31), freq='B')
    escala = []
    
    for dia in dias_range:
        data_s, sem, d_sem = dia.strftime("%d/%m/%Y"), dia.isocalendar()[1], dia.weekday()
        d_nome = t["dias"][d_sem]
        quem_ja_foi = [e['Apresentador'] for e in escala if e['Semana'] == sem]
        
        # --- FLASH MANHÃ (09:45) ---
        # 1. Brasil
        cand_br_m = [n for n in fila_br if n not in quem_ja_foi]
        if not cand_br_m: cand_br_m = fila_br
        ap_br_m = min(cand_br_m, key=lambda x: cont_total[x])
        cont_total[ap_br_m] += 1
        quem_ja_foi.append(ap_br_m)
        
        escala.append({
            "Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": "Flash Manhã (Brasil)", "Região": "Brasil",
            "Apresentador": ap_br_m, "Backup": encontrar_backup_vivo(ap_br_m, todos_nomes),
            "Backup2": encontrar_backup_vivo(encontrar_backup_vivo(ap_br_m, todos_nomes), todos_nomes),
            "BackupOculto": encontrar_backup_vivo(encontrar_backup_vivo(encontrar_backup_vivo(ap_br_m, todos_nomes), todos_nomes), todos_nomes),
            "Link": f"https://outlook.office.com/calendar/0/deeplink/compose?subject={urllib.parse.quote('Flash Manhã Brasil')}&startdt={dia.strftime('%Y-%m-%d')}T09:45:00"
        })

        # 2. LATAM
        cand_latam_m = [n for n in fila_latam if n not in quem_ja_foi]
        if not cand_latam_m: cand_latam_m = fila_latam
        ap_latam_m = min(cand_latam_m, key=lambda x: cont_total[x])
        cont_total[ap_latam_m] += 1
        quem_ja_foi.append(ap_latam_m)

        escala.append({
            "Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": "Flash Manhã (LATAM)", "Região": "LATAM",
            "Apresentador": ap_latam_m, "Backup": encontrar_backup_vivo(ap_latam_m, todos_nomes),
            "Backup2": encontrar_backup_vivo(encontrar_backup_vivo(ap_latam_m, todos_nomes), todos_nomes),
            "BackupOculto": encontrar_backup_vivo(encontrar_backup_vivo(encontrar_backup_vivo(ap_latam_m, todos_nomes), todos_nomes), todos_nomes),
            "Link": f"https://outlook.office.com/calendar/0/deeplink/compose?subject={urllib.parse.quote('Flash Manhã LATAM')}&startdt={dia.strftime('%Y-%m-%d')}T09:45:00"
        })

        # --- TARDE (15:00) ---
        if d_sem in [1, 3]: # Terça e Quinta: DOR Geral
            cand_dor = [n for n in nomes_dor if n not in quem_ja_foi]
            if not cand_dor: cand_dor = nomes_dor
            ap_dor = min(cand_dor, key=lambda x: cont_dor[x])
            cont_dor[ap_dor] += 1
            cont_total[ap_dor] += 1
            
            escala.append({
                "Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": "DOR", "Região": "Geral",
                "Apresentador": ap_dor, "Backup": encontrar_backup_vivo(ap_dor, todos_nomes),
                "Backup2": encontrar_backup_vivo(encontrar_backup_vivo(ap_dor, todos_nomes), todos_nomes),
                "BackupOculto": encontrar_backup_vivo(encontrar_backup_vivo(encontrar_backup_vivo(ap_dor, todos_nomes), todos_nomes), todos_nomes),
                "Link": f"https://outlook.office.com/calendar/0/deeplink/compose?subject={urllib.parse.quote('DOR Geral')}&startdt={dia.strftime('%Y-%m-%d')}T15:00:00"
            })
        else: # Segunda, Quarta e Sexta: Flash Tarde (Brasil + LATAM)
            # Brasil Tarde
            cand_br_t = [n for n in fila_br if n not in quem_ja_foi]
            if not cand_br_t: cand_br_t = fila_br
            ap_br_t = min(cand_br_t, key=lambda x: cont_total[x])
            cont_total[ap_br_t] += 1
            quem_ja_foi.append(ap_br_t)

            escala.append({
                "Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": "Flash Tarde (Brasil)", "Região": "Brasil",
                "Apresentador": ap_br_t, "Backup": encontrar_backup_vivo(ap_br_t, todos_nomes),
                "Backup2": encontrar_backup_vivo(encontrar_backup_vivo(ap_br_t, todos_nomes), todos_nomes),
                "BackupOculto": encontrar_backup_vivo(encontrar_backup_vivo(encontrar_backup_vivo(ap_br_t, todos_nomes), todos_nomes), todos_nomes),
                "Link": f"https://outlook.office.com/calendar/0/deeplink/compose?subject={urllib.parse.quote('Flash Tarde Brasil')}&startdt={dia.strftime('%Y-%m-%d')}T15:00:00"
            })

            # LATAM Tarde
            cand_latam_t = [n for n in fila_latam if n not in quem_ja_foi]
            if not cand_latam_t: cand_latam_t = fila_latam
            ap_latam_t = min(cand_latam_t, key=lambda x: cont_total[x])
            cont_total[ap_latam_t] += 1

            escala.append({
                "Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": "Flash Tarde (LATAM)", "Região": "LATAM",
                "Apresentador": ap_latam_t, "Backup": encontrar_backup_vivo(ap_latam_t, todos_nomes),
                "Backup2": encontrar_backup_vivo(encontrar_backup_vivo(ap_latam_t, todos_nomes), todos_nomes),
                "BackupOculto": encontrar_backup_vivo(encontrar_backup_vivo(encontrar_backup_vivo(ap_latam_t, todos_nomes), todos_nomes), todos_nomes),
                "Link": f"https://outlook.office.com/calendar/0/deeplink/compose?subject={urllib.parse.quote('Flash Tarde LATAM')}&startdt={dia.strftime('%Y-%m-%d')}T15:00:00"
            })
            
    return pd.DataFrame(escala)

def exportar_excel_limpo(df_total, mes_nome=None):
    output = io.BytesIO()
    df_c = df_total.copy()
    df_c['dt_obj'] = pd.to_datetime(df_c['Data'], format='%d/%m/%Y')
    df_c = df_c.sort_values('dt_obj')
    meses_map = {i+1: nome for i, nome in enumerate(t["meses"])}
    df_c['Mês'] = df_c['dt_obj'].dt.month.map(meses_map)
    
    if mes_nome: df_c = df_c[df_c['Mês'] == mes_nome]

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook, worksheet = writer.book, writer.book.add_worksheet('Escala')
        h_fmt = workbook.add_format({'bold': True, 'bg_color': '#ff4b4b', 'font_color': 'white', 'border': 1, 'align': 'center'})
        m_fmt = workbook.add_format({'bold': True, 'bg_color': '#A6A6A6', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        c_fmt = workbook.add_format({'border': 1, 'align': 'center'})
        
        cols = ['Mês', 'Data', 'Dia', 'Reunião', 'Região', 'Apresentador', 'Backup']
        for i, col in enumerate(cols): 
            worksheet.write(0, i, col, h_fmt)
            worksheet.set_column(i, i, 18)
            
        row_idx, mes_atual = 1, ""
        for _, row in df_c.iterrows():
            if row['Mês'] != mes_atual:
                mes_atual = row['Mês']
                worksheet.merge_range(row_idx, 0, row_idx, 6, mes_atual.upper(), m_fmt)
                row_idx += 1
            for j, c in enumerate(cols): worksheet.write(row_idx, j, str(row[c]) if c in row else "", c_fmt)
            row_idx += 1
    return output.getvalue()

def renderizar_card(row):
    cor_borda = "#0078d4" if row.get('Região') == "Brasil" else "#28a745" if row.get('Região') == "LATAM" else "#ff4b4b"
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid {cor_borda}; min-height: 220px; margin-bottom: 10px; color: #333;">
        <b style="font-size: 14px; color: #555;">{row['Reunião']}</b><br><br>
        <span style="font-size: 18px; font-weight: bold; color: #111;">🏆 {row['Apresentador']}</span><br><br>
        <span style="font-size: 13px; color: #444;">{t['backup']}: {row['Backup']}</span><br>
        <span title="{t['backup_oculto']}: {row['BackupOculto']}" style="font-size: 13px; color: #444; cursor: help;">{t['backup2']}: {row['Backup2']}</span>
        <div style="margin-top: 15px;"><a href="{row['Link']}" target="_blank" style="display: block; text-decoration: none; color: white; background-color: #0078d4; padding: 8px; border-radius: 5px; font-size: 11px; text-align: center; font-weight: bold;">{t['agendar']}</a></div>
    </div>
    """, unsafe_allow_html=True)

# --- EXECUÇÃO ---
if check_login():
    st.sidebar.title("🌐 Idioma / Lenguaje")
    lang_opt = st.sidebar.radio("Selecione:", ["🇧🇷 Português", "🇪🇸 Español"], index=0 if st.session_state.lang == "PT" else 1)
    new_lang = "PT" if "Português" in lang_opt else "ES"
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.sidebar.divider()
    if st.sidebar.toggle(t["acessibilidade"], value=False):
        injetar_leitor_acessibilidade(t["lang_code"])
    
    st.sidebar.divider()
    with st.sidebar.expander(t["roteiro_ter"], expanded=False):
        st.markdown(f"**Pauta:** {t['pauta']['prac']} + {t['pauta']['ini']} + {t['pauta']['track']} + {t['pauta']['work']}")
        st.markdown(f"- {t['pauta']['lista']}\n- {t['pauta']['tk']}\n- {t['pauta']['escala']}\n- {t['pauta']['behavior']}\n- {t['pauta']['plan']}\n- {t['pauta']['prac']}\n- {t['pauta']['nps']}\n- {t['pauta']['ini']}\n- {t['pauta']['track']}\n- {t['pauta']['work']}\n- {t['pauta']['plan']} ({t['pauta']['issue']})\n- 🛡 SHE\n- 🏆 Behavior")

    with st.sidebar.expander(t["roteiro_qui"], expanded=False):
        st.markdown(f"**Pauta:** {t['pauta']['lt']} + {t['pauta']['ftr']} + {t['pauta']['cats']} + {t['pauta']['work']}")
        st.markdown(f"- {t['pauta']['lista']}\n- {t['pauta']['tk']}\n- {t['pauta']['escala']}\n- {t['pauta']['behavior']}\n- {t['pauta']['plan']}\n- {t['pauta']['lt']}\n- {t['pauta']['ftr']}\n- {t['pauta']['cats']}\n- {t['pauta']['work']}\n- {t['pauta']['issue']}\n- {t['pauta']['plan']}\n- 🛡 SHE\n- 🏆 Behavior")

    with st.sidebar.expander(t["estrutura_tit"], expanded=False):
        st.markdown("""
        **Indireto Brasil:** Debora, Dani, Dyana, Luca, Bruno, Thiago, Tobias
        \n**Material Fert Brasil:** Amanda, Douglas, Renan, Anna
        \n**CRM:** Julia, Bruna 
        \n**Material Direto Brasil:** Livia, Rafael
        \n**Material Direto Latam:** Ariel, Enrique, Sonia, Jazmin, Gisele
        \n**Fert Latam:** Florencia, Jesus, Bianca, Soledad, Mijal, German, Sebastian, Estefanía, Andrea, Honorato, Nathan, Rocio, Faiha
        """)

    # 1. Carrega as informações das planilhas de forma segura dentro do Login
    try:
        URL_PAGINA1 = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Página1"
        URL_BACKUPS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Backups"
        
        df_backups = pd.read_csv(URL_BACKUPS)
        df_backups['Funcionario'] = df_backups['Funcionario'].astype(str).str.strip()
        df_backups['Backups'] = df_backups['Backups'].astype(str).str.strip()
        MAPA_REFERENCIA = dict(zip(df_backups['Funcionario'], df_backups['Backups']))
    except Exception as e:
        pass

    # 2. Gera a escala usando as listas completas de Brasil e LATAM
    df_total = gerar_escala_balanceada(time_brasil_completo, time_latam_completo)
    st.title(t["titulo"])

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        with st.expander(t["exp_mes"]):
            m_sel = st.selectbox(t["mes_col"] + ":", t["meses"])
            st.download_button(f"{t['baixar']} {m_sel}", exportar_excel_limpo(df_total, m_sel), f"Escala_{m_sel}.xlsx", use_container_width=True)
    with col_e2:
        with st.expander(t["exp_ano"]):
            st.download_button(t["baixar"] + f" {t['mes_col']} Completo", exportar_excel_limpo(df_total), "Escala_Anual.xlsx", use_container_width=True)

    st.divider()
    busca = st.selectbox(t["buscar"], [t["todos"]] + time_geral_completo)
    if busca != t["todos"]:
        df_b = df_total[df_total["Apresentador"] == busca].copy()
        st.info(t["stats"].format(nome=busca, total=len(df_b), dor=len(df_b[df_b["Reunião"] == "DOR"])))
        st.dataframe(df_b[["Data", "Dia", "Reunião", "Backup", "Backup2", "Link"]], column_config={"Link": st.column_config.LinkColumn(t["agendar"], display_text=t["agendar"], width="small")}, use_container_width=True, hide_index=True)

    st.divider()
    s_idx = st.select_slider(t["semana"], options=sorted(df_total["Semana"].unique()), value=datetime.now().isocalendar()[1])
    df_s = df_total[df_total["Semana"] == s_idx]
    
    for dt, gp in df_s.groupby("Data", sort=False):
        st.markdown(f"### **{gp['Dia'].iloc[0]} - {dt}**")
        
        # Agrupa por turno de reunião para renderizar lado a lado
        reunioes_manha = gp[gp['Reunião'].str.contains("Manhã")]
        reunioes_tarde = gp[gp['Reunião'].str.contains("Tarde|DOR")]
        
        # --- EXIBIÇÃO MANHÃ ---
        if not reunioes_manha.empty:
            st.caption("☀️ **Reuniões da Manhã (09:30)**")
            cols_m = st.columns(len(reunioes_manha))
            for i, (_, r) in enumerate(reunioes_manha.iterrows()):
                with cols_m[i]:
                    renderizar_card(r)

        # --- EXIBIÇÃO TARDE ---
        if not reunioes_tarde.empty:
            st.caption("🌤️ **Reuniões da Tarde (15:00)**")
            cols_t = st.columns(len(reunioes_tarde))
            for i, (_, r) in enumerate(reunioes_tarde.iterrows()):
                with cols_t[i]:
                    renderizar_card(r)
        
        st.write("")
