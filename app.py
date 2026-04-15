import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import streamlit.components.v1 as components
import io
import random

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Portal Integrado", layout="wide")

# --- DICIONÁRIO DE TORRES (REGRA DE NEGÓCIO) ---
TORRES = {
    "Indireto Brasil": ["Debora", "Dani", "Abigail", "Luca", "Bruno", "Thiago", "Anna"],
    "Material Fert Brasil": ["Amanda", "Sabrina", "Douglas"],
    "CRM": ["Julia", "Bruna", "Renan"],
    "Material Direto Brasil": ["Livia", "Rafael"],
    "Material Direto Latam": ["Ariel", "Cristian", "Enrique", "Sonia", "Gisele"],
    "Fert Latam": ["Jazmin", "Florencia", "Jesus", "Bianca", "Soledad", "Mijal", "Silvana", "Andrea", "Honorato", "Faiha"]
}

# Inverter para busca rápida: { "Thiago": "Indireto Brasil" }
PESSOA_PARA_TORRE = {pessoa: torre for torre, pessoas in TORRES.items() for pessoa in pessoas}

# --- DICIONÁRIO DE TRADUÇÃO ---
I18N = {
    "PT": {
        "lang_code": "pt-BR",
        "titulo": "🚀 MMD | Portal de Gestão 2026",
        "aba_escala": "📅 Escalas",
        "aba_ferias": "🌴 Planejamento de Férias",
        "login_tit": "Portal de Escalas MMD",
        "usuario": "Usuário", "senha": "Senha", "acessar": "Acessar Painel",
        "acessibilidade": "Ativar Acessibilidade",
        "roteiro_ter": "📝 Roteiro Terça: Práticas + Iniciativas",
        "roteiro_qui": "📝 Roteiro Quinta: Lead Time + SLA",
        "estrutura_tit": "👥 Estrutura de Times",
        "exp_mes": "📂 Exportar Mês", "exp_ano": "📅 Exportar Ano",
        "baixar": "Baixar", "buscar": "🔍 Buscar por Apresentador:",
        "todos": "Todos", "semana": "Semana:", "agendar": "📅 AGENDAR",
        "backup": "🔄 Backup", "backup2": "🛡️ Backup 2", "backup_oculto": "Backup Oculto",
        "stats": "📊 {nome}: {total} reuniões no ano (sendo {dor} reuniões DOR).",
        "flash_m": "Flash Manhã", "resp_m": "Responsável Manhã", "resp_t": "Responsável Tarde", "tipo_t": "Tipo Tarde/DOR",
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
        "titulo": "🚀 MMD | Portal de Gestión 2026",
        "aba_escala": "📅 Escalas",
        "aba_ferias": "🌴 Plan de Vacaciones",
        "login_tit": "Portal de Escalas MMD",
        "usuario": "Usuario", "senha": "Contraseña", "acessar": "Acceder al Panel",
        "acessibilidade": "Activar Accesibilidad",
        "roteiro_ter": "📝 Guion Martes: Prácticas + Iniciativas",
        "roteiro_qui": "📝 Guion Jueves: Lead Time + SLA",
        "estrutura_tit": "👥 Estructura de Equipos",
        "exp_mes": "📂 Exportar Mes", "exp_ano": "📅 Exportar Año",
        "baixar": "Descargar", "buscar": "🔍 Buscar por Presentador:",
        "todos": "Todos", "semana": "Semana:", "agendar": "📅 AGENDAR",
        "backup": "🔄 Backup", "backup2": "🛡️ Backup 2", "backup_oculto": "Backup Oculto",
        "stats": "📊 {nome}: {total} reuniones en el año ({dor} reuniones DOR).",
        "flash_m": "Flash Mañana", "resp_m": "Responsable Mañana", "resp_t": "Responsable Tarde", "tipo_t": "Tipo Tarde/DOR",
        "mes_col": "Mes",
        "dias": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
        "meses": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julho", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
        "pauta": {
            "lista": "📑 Lista de presencia", "tk": "⏱ Timekeeper", "escala": "🗓 Escala Horario", "behavior": "📈 Behavior",
            "plan": "🎯 Plan de accion", "prac": "✅ Practicas", "nps": "📊 NPS", "ini": "💡 Iniciativas",
            "track": "📉 Tracker", "work": "🛠 Work Plan", "issue": "⚠️ Issues", "she": "🛡 SHE",
            "lt": "🕒 Lead Time", "ftr": "✅ FTR", "cats": "📁 Cats+BH"
        }
    }
}

if "lang" not in st.session_state: st.session_state.lang = "PT"
if "db_ferias" not in st.session_state: st.session_state.db_ferias = [] # Simulação do banco de dados

t = I18N[st.session_state.lang]

# --- FUNÇÕES DE ACESSIBILIDADE E LOGIN (MANTIDAS) ---
def injetar_leitor_acessibilidade(lang_code):
    components.html(f"""<script>
        const synth = window.speechSynthesis; let ultimoTexto = "";
        function falar(texto) {{ if (!texto || texto === ultimoTexto) return; synth.cancel(); 
        const ut = new SpeechSynthesisUtterance(texto); ut.lang = '{lang_code}'; ut.rate = 1.1;
        ultimoTexto = texto; synth.speak(ut); setTimeout(() => {{ ultimoTexto = ""; }}, 800); }}
        const docAlvo = window.parent.document;
        docAlvo.addEventListener('mouseover', (e) => {{ const el = e.target; const txt = (el.innerText || el.textContent).trim();
        if (txt.length > 0 && !txt.includes("http")) {{ falar(txt); }} }}, true);
    </script>""", height=0, width=0)

def check_login():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown(f"<h2 style='text-align: center;'>{t['login_tit']}</h2>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1,1,1]); 
        with c2:
            with st.form("login"):
                u, p = st.text_input(t["usuario"]), st.text_input(t["senha"], type="password")
                if st.form_submit_button(t["acessar"], use_container_width=True):
                    if u == "MMD-Board" and p == "@MMD123#": st.session_state.logged_in = True; st.rerun()
                    else: st.error("Erro")
        return False
    return True

# --- MOTOR DE ESCALAS (MANTIDO) ---
MAPA_REFERENCIA = {
    "Abigail": "Dani", "Amanda": "Mijal", "Anna Laura": "Soledad", "Ariel": "Rafael", 
    "Bianca M.": "Ariel", "Bruna": "Anna Laura", "Bruno": "Bianca M.", "Dani": "Jesus", 
    "Debora": "Bruna", "Diana": "Julia", "Florencia": "Diana", "Gisele": "Thiago", 
    "Honorato": "Bruno", "Jazmin": "Abigail", "Jesus": "Luca", "Julia": "Honorato", 
    "Livia": "Amanda", "Luca": "Jazmin", "Mijal": "Livia", "Rafael": "Florencia", 
    "Renan": "Debora", "Soledad": "Gisele", "Thiago": "Renan"
}

def encontrar_backup_vivo(nome, ativos):
    prox = MAPA_REFERENCIA.get(nome)
    tent = 0
    while prox and prox not in ativos and tent < len(MAPA_REFERENCIA):
        prox = MAPA_REFERENCIA.get(prox); tent += 1
    return prox if prox in ativos else "Sem Backup Ativo"

def gerar_escala_balanceada(nomes):
    random.seed(42); fb = nomes.copy(); random.shuffle(fb)
    n_dor = [n for n in nomes if n not in ["Dani", "Rafael"]]; random.shuffle(n_dor)
    c_tot, c_dor = {n: 0 for n in nomes}, {n: 0 for n in n_dor}
    dias = pd.date_range(datetime(2026, 1, 1), datetime(2026, 12, 31), freq='B')
    esc = []
    for d in dias:
        dt, sem, d_sem = d.strftime("%d/%m/%Y"), d.isocalendar()[1], d.weekday()
        ja_foi = [e['Apresentador'] for e in esc if e['Semana'] == sem]
        ap_m = min([n for n in fb if n not in ja_foi], key=lambda x: c_tot[x]); c_tot[ap_m] += 1
        ja_foi.append(ap_m)
        esc.append({"Semana": sem, "Data": dt, "Dia": t["dias"][d_sem], "Reunião": t["flash_m"], "Apresentador": ap_m, "Backup": encontrar_backup_vivo(ap_m, nomes), "Backup2": encontrar_backup_vivo(encontrar_backup_vivo(ap_m, nomes), nomes), "BackupOculto": "", "Link": "#"})
        tipo_t = "DOR" if d_sem in [1, 3] else "Flash Tarde"
        cand_t = [n for n in (n_dor if tipo_t == "DOR" else fb) if n not in ja_foi]
        ap_t = min(cand_t, key=lambda x: c_dor[x] if tipo_t == "DOR" else c_tot[x])
        if tipo_t == "DOR": c_dor[ap_t] += 1
        c_tot[ap_t] += 1
        esc.append({"Semana": sem, "Data": dt, "Dia": t["dias"][d_sem], "Reunião": tipo_t, "Apresentador": ap_t, "Backup": encontrar_backup_vivo(ap_t, nomes), "Backup2": encontrar_backup_vivo(encontrar_backup_vivo(ap_t, nomes), nomes), "BackupOculto": "", "Link": "#"})
    return pd.DataFrame(esc)

# --- FUNÇÃO DE EXPORTAÇÃO CORRIGIDA ---
def exportar_excel_limpo(df_total, mes_nome=None):
    output = io.BytesIO()
    df_c = df_total.copy()
    df_c['dt_obj'] = pd.to_datetime(df_c['Data'], format='%d/%m/%Y')
    df_c = df_c.sort_values('dt_obj')
    meses_map = {i+1: nome for i, nome in enumerate(t["meses"])}
    df_c['Mês'] = df_c['dt_obj'].dt.month.map(meses_map)
    m = df_c[df_c['Reunião'] == t['flash_m']][['Mês', 'Data', 'Dia', 'Apresentador', 'Backup']].rename(columns={'Apresentador':t['resp_m'], 'Backup':t['backup'] + ' M'})
    t_df = df_c[df_c['Reunião'].isin(['Flash Tarde', 'DOR'])][['Data', 'Apresentador', 'Backup', 'Reunião']].rename(columns={'Apresentador':t['resp_t'], 'Backup':t['backup'] + ' T', 'Reunião':t['tipo_t']})
    df_f = pd.merge(m, t_df, on='Data', how='outer').fillna("").sort_values('Data')
    if mes_nome: df_f = df_f[df_f['Mês'] == mes_nome]
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook, worksheet = writer.book, writer.book.add_worksheet('Escala')
        h_fmt = workbook.add_format({'bold': True, 'bg_color': '#ff4b4b', 'font_color': 'white', 'border': 1, 'align': 'center'})
        m_fmt = workbook.add_format({'bold': True, 'bg_color': '#A6A6A6', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        c_fmt = workbook.add_format({'border': 1, 'align': 'center'})
        cols = ['Data', 'Dia', t['resp_m'], t['backup'] + ' M', t['tipo_t'], t['resp_t'], t['backup'] + ' T']
        for i, col in enumerate(cols): worksheet.write(0, i, col, h_fmt); worksheet.set_column(i, i, 18)
        row_idx, mes_at = 1, ""
        for _, row in df_f.iterrows():
            if row['Mês'] != mes_at:
                mes_at = row['Mês']; worksheet.merge_range(row_idx, 0, row_idx, 6, mes_at.upper(), m_fmt); row_idx += 1
            for j, c in enumerate(cols): worksheet.write(row_idx, j, row[c] if c in row else "", c_fmt)
            row_idx += 1
    return output.getvalue()

# --- EXECUÇÃO DO PORTAL ---
if check_login():
    # Sidebar
    st.sidebar.title("🌐 Idioma / Lenguaje")
    lang_opt = st.sidebar.radio("Selecione:", ["🇧🇷 Português", "🇪🇸 Español"], index=0 if st.session_state.lang == "PT" else 1)
    if ("Português" in lang_opt and st.session_state.lang == "ES") or ("Español" in lang_opt and st.session_state.lang == "PT"):
        st.session_state.lang = "PT" if "Português" in lang_opt else "ES"; st.rerun()

    st.sidebar.divider()
    if st.sidebar.toggle(t["acessibilidade"], value=False): injetar_leitor_acessibilidade(t["lang_code"])
    
    st.sidebar.divider()
    with st.sidebar.expander(t["roteiro_ter"], expanded=False):
        st.write(f"- {t['pauta']['lista']}\n- {t['pauta']['tk']}\n- {t['pauta']['escala']}\n- {t['pauta']['behavior']}\n- {t['pauta']['plan']}\n- {t['pauta']['prac']}")
    with st.sidebar.expander(t["roteiro_qui"], expanded=False):
        st.write(f"- {t['pauta']['lista']}\n- {t['pauta']['lt']}\n- {t['pauta']['ftr']}\n- {t['pauta']['cats']}")
    with st.sidebar.expander(t["estrutura_tit"], expanded=False):
        for torre, p in TORRES.items(): st.markdown(f"**{torre}:** {', '.join(p)}")

    # Abas Principais
    tab_escala, tab_ferias = st.tabs([t["aba_escala"], t["aba_ferias"]])

    # --- ABA 1: ESCALAS ---
    with tab_escala:
        try:
            df_csv = pd.read_csv(f"https://docs.google.com/spreadsheets/d/1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU/gviz/tq?tqx=out:csv")
            nomes = sorted([n for n in df_csv['Funcionario'].dropna().unique() if n not in ["Faiha", "Sonia", "Enrique", "Bianca S."]])
        except: nomes = sorted(list(PESSOA_PARA_TORRE.keys()))

        df_total = gerar_escala_balanceada(nomes)
        st.title(t["titulo"])
        
        c1, c2 = st.columns(2)
        with c1:
            with st.expander(t["exp_mes"]):
                m = st.selectbox(t["mes_col"], t["meses"]); st.download_button(f"{t['baixar']} {m}", exportar_excel_limpo(df_total, m), f"Escala_{m}.xlsx")
        with c2:
            with st.expander(t["exp_ano"]):
                st.download_button(f"{t['baixar']} Ano", exportar_excel_limpo(df_total), "Escala_2026.xlsx")

        st.divider()
        busca = st.selectbox(t["buscar"], [t["todos"]] + nomes)
        if busca != t["todos"]:
            df_b = df_total[df_total["Apresentador"] == busca]
            st.info(t["stats"].format(nome=busca, total=len(df_b), dor=len(df_b[df_b["Reunião"]=="DOR"])))
            st.dataframe(df_b[["Data", "Dia", "Reunião", "Backup", "Backup2"]], hide_index=True, use_container_width=True)

        st.divider()
        sem = st.select_slider(t["semana"], options=sorted(df_total["Semana"].unique()), value=datetime.now().isocalendar()[1])
        df_s = df_total[df_total["Semana"] == sem]
        for dt, gp in df_s.groupby("Data", sort=False):
            st.markdown(f"**{gp['Dia'].iloc[0]} - {dt}**")
            cols = st.columns(len(gp))
            for i, (_, r) in enumerate(gp.iterrows()):
                with cols[i]:
                    st.markdown(f"""<div style="background:#f0f2f6;padding:15px;border-radius:10px;border-left:5px solid #ff4b4b;color:#333;">
                    <b>{r['Reunião']}</b><br><br><span style="font-size:18px;font-weight:bold;">🏆 {r['Apresentador']}</span><br>
                    <small>{t['backup']}: {r['Backup']}</small></div>""", unsafe_allow_html=True)

    # --- ABA 2: FÉRIAS (O NOVO MÓDULO) ---
    with tab_ferias:
        st.title("🌴 Planejamento de Férias Inteligente")
        st.info("Regra: Pessoas da mesma torre não podem sair de férias no mesmo período.")
        
        col_form, col_visu = st.columns([1, 3])
        
        with col_form:
            st.subheader("Marcar Período")
            nome_f = st.selectbox("Seu Nome:", nomes)
            data_ini = st.date_input("Início:", value=datetime.now())
            data_fim = st.date_input("Término:", value=datetime.now() + timedelta(days=10))
            
            if st.button("💾 Salvar Férias", use_container_width=True):
                minha_torre = PESSOA_PARA_TORRE.get(nome_f)
                conflito = False
                quem_conflita = ""
                
                # Checar Regra de Torres
                for registro in st.session_state.db_ferias:
                    # Se é da mesma torre e não é a mesma pessoa
                    if PESSOA_PARA_TORRE.get(registro['nome']) == minha_torre and registro['nome'] != nome_f:
                        # Checar sobreposição de datas
                        if not (data_fim < registro['ini'] or data_ini > registro['fim']):
                            conflito = True
                            quem_conflita = registro['nome']
                            break
                
                if conflito:
                    st.error(f"❌ Bloqueado! {quem_conflita} da torre '{minha_torre}' já possui férias nesse período.")
                else:
                    st.session_state.db_ferias.append({'nome': nome_f, 'ini': data_ini, 'fim': data_fim, 'torre': minha_torre})
                    st.success("✅ Férias registradas com sucesso!")
                    st.rerun()

        with col_visu:
            mes_ref = st.selectbox("Visualizar Mês:", t["meses"], index=datetime.now().month -1)
            ano_ref = 2026
            num_mes = t["meses"].index(mes_ref) + 1
            
            # Criar grade visual simples
            st.write(f"### Disponibilidade: {mes_ref} / {ano_ref}")
            
            # Lógica de cores para os dias do mês
            dias_do_mes = pd.date_range(start=f"{ano_ref}-{num_mes:02d}-01", end=pd.Timestamp(ano_ref, num_mes, 1) + pd.offsets.MonthEnd(0))
            
            # Mostrar os dias em formato de grade (7 colunas)
            cols_grid = st.columns(7)
            for i, dia in enumerate(dias_do_mes):
                dia_dt = dia.date()
                ocupado = False
                ocupante = ""
                for r in st.session_state.db_ferias:
                    if r['ini'] <= dia_dt <= r['fim']:
                        ocupado = True
                        ocupante = r['nome']
                        break
                
                cor = "#ff4b4b" if ocupado else "#28a745"
                txt_cor = "white"
                with cols_grid[i % 7]:
                    st.markdown(f"""<div style="background:{cor}; color:{txt_cor}; padding:5px; border-radius:5px; text-align:center; margin-bottom:5px; font-size:12px;">
                    {dia.day}<br><b>{ocupante if ocupante else 'Livre'}</b></div>""", unsafe_allow_html=True)
        
        st.divider()
        st.subheader("Lista de Férias Marcadas")
        if st.session_state.db_ferias:
            df_f_view = pd.DataFrame(st.session_state.db_ferias)
            st.table(df_f_view)
        else:
            st.write("Nenhuma férias registrada ainda.")
