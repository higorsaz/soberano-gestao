import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
import calendar
import time

# --- 1. CONFIGURAÇÕES VISUAIS ---
st.set_page_config(page_title="SOBERANO | Gestão Rural", page_icon="🐂", layout="wide")

# CSS para o Calendário e Visual Mobile
st.markdown("""
    <style>
    .dia-box {
        padding: 10px; border-radius: 8px; text-align: center; margin: 2px;
        font-weight: bold; border: 1px solid #ddd;
        font-size: 14px;
    }
    .feito { background-color: #2e7d32; color: white; border-color: #1b5e20; }
    .pendente { background-color: #c62828; color: white; border-color: #b71c1c; }
    .hoje { border: 3px solid #FFD700 !important; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e9ecef; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BANCO DE DADOS (PERSISTÊNCIA SIMPLES EM CSV) ---
# Na nuvem grátis, os CSVs resetam quando o app reinicia (deploy novo).
# Para uso profissional definitivo, ideal conectar com Google Sheets ou Banco SQL.
# Mas para esta versão inicial, manteremos CSV local.

FILES = {
    'gado': 'db_gado.csv',
    'pastos': 'db_pastos.csv',
    'check': 'db_checklist.csv',
    'users': 'db_equipe.csv'
}

def init_db():
    if not os.path.exists(FILES['gado']):
        pd.DataFrame(columns=['ID', 'Brinco', 'Categoria', 'Peso', 'Pasto', 'Status', 'Data_Entrada']).to_csv(FILES['gado'], index=False)
    
    if not os.path.exists(FILES['pastos']):
        pd.DataFrame([
            {'Nome': 'Pasto 01', 'Area_ha': 10.0, 'Capim': 'Braquiária'},
            {'Nome': 'Pasto 02', 'Area_ha': 20.0, 'Capim': 'Mombaça'}
        ]).to_csv(FILES['pastos'], index=False)
        
    if not os.path.exists(FILES['check']):
        pd.DataFrame(columns=['Data', 'Responsavel', 'Sal', 'Agua', 'Cerca', 'Obs']).to_csv(FILES['check'], index=False)
        
    if not os.path.exists(FILES['users']):
        pd.DataFrame([
            {'Nome': 'Higor Azevedo', 'Funcao': 'Dono'},
            {'Nome': 'Funcionário 01', 'Funcao': 'Operacional'}
        ]).to_csv(FILES['users'], index=False)

def load(k): return pd.read_csv(FILES[k])
def save(df, k): df.to_csv(FILES[k], index=False)

init_db()

# --- 3. BARRA LATERAL (LOGIN & MENU) ---
st.sidebar.title("🤠 SOBERANO")
st.sidebar.caption("Sistema de Gestão Pecuária")

# Login Simples
perfil = st.sidebar.selectbox("Quem é você?", ["Proprietário", "Equipe"])

modo_admin = False
usuario_ativo = "Visitante"

if perfil == "Proprietário":
    senha = st.sidebar.text_input("Senha de Acesso", type="password")
    if senha == "123": # SENHA DO DONO
        modo_admin = True
        usuario_ativo = "Higor Azevedo"
        st.sidebar.success("✅ Logado como Dono")
        menu_opcoes = ["📊 Dashboard", "🐂 Rebanho", "🌾 Pastos", "✅ Checklist", "👥 Equipe", "⚙️ Config"]
    else:
        st.sidebar.warning("🔒 Digite a senha...")
        menu_opcoes = []
else:
    # Login Equipe
    df_users = load('users')
    lista = df_users[df_users['Funcao'] != 'Dono']['Nome'].tolist()
    if not lista: lista = ["Funcionário Padrão"]
    usuario_ativo = st.sidebar.selectbox("Selecione seu nome:", lista)
    st.sidebar.info(f"Bom trabalho, {usuario_ativo}!")
    menu_opcoes = ["✅ Checklist", "🐂 Consulta Rebanho"]

if menu_opcoes:
    menu = st.sidebar.radio("Navegue por aqui:", menu_opcoes)
else:
    menu = "Bloqueado"

st.sidebar.markdown("---")
st.sidebar.markdown("© 2024 Soberano")

# --- 4. TELAS DO SISTEMA ---

if menu == "Bloqueado":
    st.title("🔒 Acesso Restrito")
    st.write("Identifique-se na barra lateral para acessar o sistema.")

# === DASHBOARD ===
elif menu == "📊 Dashboard":
    st.title("📊 Painel de Comando")
    
    # KPIs Rápidos
    df_g = load('gado')
    df_p = load('pastos')
    ativos = df_g[df_g['Status']=='Ativo']
    area_total = df_p['Area_ha'].sum()
    lotacao = len(ativos) / area_total if area_total > 0 else 0
    
    # Linha 1: Métricas
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cabeças Ativas", len(ativos), delta="Animais no pasto")
    c2.metric("Área Total", f"{area_total} ha", delta="Cadastrada")
    c3.metric("Lotação Global", f"{lotacao:.2f} UA/ha", delta_color="normal")
    c4.metric("Peso Médio", f"{ativos['Peso'].mean():.0f} kg" if not ativos.empty else "0 kg")

    st.markdown("---")

    # Linha 2: Gráficos
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.subheader("Distribuição por Categoria")
        if not ativos.empty:
            fig1 = px.pie(ativos, names='Categoria', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Sem dados de gado.")
            
    with col_g2:
        st.subheader("Peso Total por Pasto (@)")
        if not ativos.empty:
            df_peso_pasto = ativos.groupby('Pasto')['Peso'].sum().reset_index()
            # Converte kg para arroba (aprox / 30 ou /15 dependendo da conta, usando kg bruto aqui)
            fig2 = px.bar(df_peso_pasto, x='Pasto', y='Peso', color='Pasto', text_auto=True)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sem dados.")

# === CHECKLIST (CALENDÁRIO) ===
elif menu == "✅ Checklist":
    st.title("✅ Controle Operacional")
    
    tab1, tab2 = st.tabs(["📝 Lançamento Hoje", "📅 Histórico Mensal"])
    
    with tab1:
        with st.form("check_dia"):
            st.subheader(f"Data: {datetime.now().strftime('%d/%m/%Y')}")
            c1, c2, c3 = st.columns(3)
            sal = c1.toggle("Sal Mineral OK?")
            agua = c2.toggle("Água Limpa?")
            cerca = c3.toggle("Cerca Intacta?")
            obs = st.text_area("Observações / Ocorrências")
            
            if st.form_submit_button("✅ Confirmar Rotina", use_container_width=True):
                novo = {
                    'Data': datetime.now().strftime("%Y-%m-%d"),
                    'Responsavel': usuario_ativo,
                    'Sal': 'Sim' if sal else 'Não',
                    'Agua': 'Sim' if agua else 'Não',
                    'Cerca': 'Sim' if cerca else 'Não',
                    'Obs': obs
                }
                save(pd.concat([load('check'), pd.DataFrame([novo])], ignore_index=True), 'check')
                st.success("Checklist Salvo!")
                time.sleep(1)
                st.rerun()

    with tab2:
        st.markdown("### Mapa de Execução")
        df_c = load('check')
        hoje = datetime.now()
        dias_mes = calendar.monthrange(hoje.year, hoje.month)[1]
        
        # Grid do Calendário
        cols = st.columns(7)
        dias_semana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        for i, d in enumerate(dias_semana): cols[i].markdown(f"**{d}**")
        
        idx = datetime(hoje.year, hoje.month, 1).weekday()
        for _ in range(idx): cols[_].write("")
        
        for d in range(1, dias_mes + 1):
            data_iso = f"{hoje.year}-{hoje.month:02d}-{d:02d}"
            feito = not df_c[df_c['Data'] == data_iso].empty
            cor = "feito" if feito else "pendente"
            icone = "✅" if feito else "🔻"
            
            # Caixa do dia
            cols[idx].markdown(f"""<div class="dia-box {cor}">{d}<br>{icone}</div>""", unsafe_allow_html=True)
            
            idx += 1
            if idx > 6: idx = 0

# === REBANHO ===
elif menu == "🐂 Rebanho" or menu == "🐂 Consulta Rebanho":
    st.title("🐂 Gestão do Rebanho")
    
    if modo_admin and menu == "🐂 Rebanho":
        with st.expander("➕ Novo Animal"):
            with st.form("add_boi"):
                c1, c2 = st.columns(2)
                brinco = c1.text_input("Brinco")
                peso = c2.number_input("Peso (kg)")
                cat = c1.selectbox("Categoria", ["Bezerro", "Garrote", "Boi", "Vaca"])
                pasto = c2.selectbox("Pasto", load('pastos')['Nome'].unique())
                if st.form_submit_button("Salvar"):
                    n = {'ID': int(time.time()), 'Brinco': brinco, 'Categoria': cat, 'Peso': peso, 'Pasto': pasto, 'Status': 'Ativo'}
                    save(pd.concat([load('gado'), pd.DataFrame([n])], ignore_index=True), 'gado')
                    st.rerun()
    
    st.dataframe(load('gado'), use_container_width=True)

# === PASTOS ===
elif menu == "🌾 Pastos":
    st.title("🌾 Mapa de Pastos")
    with st.form("pasto"):
        nome = st.text_input("Nome")
        area = st.number_input("Área (ha)")
        capim = st.text_input("Capim")
        if st.form_submit_button("Salvar"):
            df = load('pastos')
            df = df[df['Nome'] != nome]
            n = {'Nome': nome, 'Area_ha': area, 'Capim': capim}
            save(pd.concat([df, pd.DataFrame([n])], ignore_index=True), 'pastos')
            st.rerun()
    st.dataframe(load('pastos'), use_container_width=True)

# === EQUIPE ===
elif menu == "👥 Equipe":
    st.title("👥 Time de Campo")
    with st.form("team"):
        nome = st.text_input("Nome")
        if st.form_submit_button("Adicionar"):
            save(pd.concat([load('users'), pd.DataFrame([{'Nome': nome, 'Funcao': 'Operacional'}])], ignore_index=True), 'users')
            st.rerun()
    st.dataframe(load('users'), use_container_width=True)

# === CONFIG ===
elif menu == "⚙️ Config":
    st.title("⚙️ Sistema")
    st.info("Versão Cloud V1.0 - Rodando no Streamlit Cloud")
