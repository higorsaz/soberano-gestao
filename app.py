import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
import calendar
import time

# --- 1. CONFIGURAÇÃO VISUAL PREMIUM (DARK MODE FORÇADO) ---
st.set_page_config(page_title="SOBERANO | Gestão Rural", page_icon="🐂", layout="wide")

# CSS Personalizado: Fundo Escuro, Botões Verdes, Texto Claro
st.markdown("""
    <style>
    /* Força Fundo Escuro Global */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Cards de Métricas (Fundo Cinza Escuro) */
    div[data-testid="stMetric"] {
        background-color: #262730;
        border: 1px solid #41444C;
        padding: 15px;
        border-radius: 10px;
        color: white;
    }
    
    /* Calendário: Caixinhas */
    .dia-box {
        padding: 10px; border-radius: 8px; text-align: center; margin: 2px;
        font-weight: bold; border: 1px solid #555;
        font-size: 14px; background-color: #1E1E1E;
    }
    .feito { background-color: #1b5e20; color: white; border-color: #2e7d32; }
    .pendente { background-color: #b71c1c; color: white; border-color: #c62828; }
    .hoje { border: 2px solid #FFD700 !important; }

    /* Inputs e Botões */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. BANCO DE DADOS ---
FILES = {
    'gado': 'db_gado.csv',
    'pastos': 'db_pastos.csv',
    'check': 'db_checklist.csv',
    'users': 'db_equipe.csv',
    'market': 'db_mercado.csv' # Novo: Armazena as cotações que você digitar
}

def init_db():
    if not os.path.exists(FILES['gado']):
        pd.DataFrame(columns=['ID', 'Brinco', 'Categoria', 'Peso_kg', 'Custo_Compra', 'Data_Entrada', 'Pasto', 'Status']).to_csv(FILES['gado'], index=False)
    if not os.path.exists(FILES['pastos']):
        pd.DataFrame([{'Nome': 'Pasto 01', 'Area_ha': 10.0, 'Capim': 'Braquiária'}]).to_csv(FILES['pastos'], index=False)
    if not os.path.exists(FILES['check']):
        pd.DataFrame(columns=['Data', 'Responsavel', 'Sal', 'Agua', 'Cerca', 'Obs']).to_csv(FILES['check'], index=False)
    if not os.path.exists(FILES['users']):
        pd.DataFrame([{'Nome': 'Higor Azevedo', 'Funcao': 'Dono'}, {'Nome': 'Peão 01', 'Funcao': 'Operacional'}]).to_csv(FILES['users'], index=False)
    if not os.path.exists(FILES['market']):
        # Valores padrão iniciais
        pd.DataFrame([{'Data': datetime.now().strftime("%Y-%m-%d"), 'Arroba_Boi': 320.00, 'Bezerro': 3000.00, 'Milho': 60.00}]).to_csv(FILES['market'], index=False)

def load(k): return pd.read_csv(FILES[k])
def save(df, k): df.to_csv(FILES[k], index=False)

init_db()

# --- 3. BARRA LATERAL ---
st.sidebar.title("🤠 SOBERANO")
st.sidebar.caption("Sistema de Gestão Pecuária")

perfil = st.sidebar.selectbox("Quem é você?", ["Proprietário", "Equipe"])
modo_admin = False

if perfil == "Proprietário":
    senha = st.sidebar.text_input("Senha", type="password")
    if senha == "123":
        modo_admin = True
        st.sidebar.success("✅ Logado")
        menu = st.sidebar.radio("Menu", ["📊 Dashboard & Mercado", "🐂 Rebanho", "🌾 Pastos", "✅ Checklist", "👥 Equipe"])
    else:
        menu = "Bloqueado"
else:
    func = st.sidebar.selectbox("Funcionário", load('users')[load('users')['Funcao']!='Dono']['Nome'].tolist())
    st.sidebar.info(f"Olá, {func}")
    menu = st.sidebar.radio("Menu", ["✅ Checklist", "🐂 Consulta"])

st.sidebar.markdown("---")

# --- 4. TELAS ---

if menu == "Bloqueado":
    st.title("🔒 Acesso Restrito")

# === DASHBOARD & MERCADO (O CORAÇÃO DO LUCRO) ===
elif menu == "📊 Dashboard & Mercado":
    st.title("📊 Painel Estratégico")
    
    # 1. ATUALIZAÇÃO DE MERCADO (MANUAL)
    with st.expander("💰 Atualizar Cotações do Dia (Sua Referência)", expanded=True):
        last_mkt = load('market').iloc[-1]
        with st.form("mercado_form"):
            c1, c2, c3 = st.columns(3)
            boi_hoje = c1.number_input("Arroba Boi Gordo (R$)", value=float(last_mkt['Arroba_Boi']))
            bez_hoje = c2.number_input("Preço Bezerro (R$)", value=float(last_mkt['Bezerro']))
            milho_hoje = c3.number_input("Saca Milho (R$)", value=float(last_mkt['Milho']))
            
            if st.form_submit_button("💾 Atualizar Indicadores"):
                novo_mkt = {'Data': datetime.now().strftime("%Y-%m-%d"), 'Arroba_Boi': boi_hoje, 'Bezerro': bez_hoje, 'Milho': milho_hoje}
                save(pd.concat([load('market'), pd.DataFrame([novo_mkt])], ignore_index=True), 'market')
                st.success("Mercado Atualizado!")
                st.rerun()

    # 2. CÁLCULO DE PATRIMÔNIO (CRUZAMENTO)
    st.markdown("### 💎 Seu Patrimônio Vivo")
    
    df_g = load('gado')
    ativos = df_g[df_g['Status']=='Ativo']
    
    if not ativos.empty:
        # Cálculos de Padaria
        peso_total_kg = ativos['Peso_kg'].sum()
        peso_total_arrobas = peso_total_kg / 30 # @ Bruta (aproximada) ou usar regra de rendimento 50% (/15 da carcaça)
        # Vamos usar regra de mercado: Peso Vivo / 30 = @? Não.
        # Regra de Bolso: (Peso Vivo * 0.50) / 15 = @ Liquida. 
        # Simplificando: Peso Vivo / 30 = @ Liquida (aprox).
        
        total_arrobas = peso_total_kg / 30
        valor_bruto_venda = total_arrobas * boi_hoje
        custo_estoque = ativos['Custo_Compra'].sum()
        lucro_potencial = valor_bruto_venda - custo_estoque
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Rebanho Atual", f"{len(ativos)} Cab")
        k2.metric("Valor de Venda (Est)", f"R$ {valor_bruto_venda:,.2f}", help=f"Baseado na @ de R$ {boi_hoje}")
        k3.metric("Custo de Compra", f"R$ {custo_estoque:,.2f}", delta="-Investido")
        k4.metric("Resultado Bruto", f"R$ {lucro_potencial:,.2f}", delta_color="normal")
        
    else:
        st.warning("Cadastre animais no menu 'Rebanho' para ver os cálculos.")

# === REBANHO (COM CUSTO) ===
elif menu == "🐂 Rebanho" or menu == "🐂 Consulta":
    st.title("🐂 Gestão do Rebanho")
    
    if modo_admin and menu == "🐂 Rebanho":
        with st.expander("➕ Compra / Nascimento"):
            with st.form("add"):
                c1, c2, c3 = st.columns(3)
                brinco = c1.text_input("Brinco")
                peso = c2.number_input("Peso (kg)", min_value=0.0)
                custo = c3.number_input("Custo de Compra (R$)", min_value=0.0)
                cat = c1.selectbox("Categoria", ["Bezerro", "Boi", "Vaca"])
                pasto = c2.selectbox("Pasto", load('pastos')['Nome'].unique())
                
                if st.form_submit_button("Salvar Animal"):
                    n = {
                        'ID': int(time.time()), 'Brinco': brinco, 'Categoria': cat, 
                        'Peso_kg': peso, 'Custo_Compra': custo, 'Pasto': pasto, 
                        'Status': 'Ativo', 'Data_Entrada': datetime.now().strftime("%Y-%m-%d")
                    }
                    save(pd.concat([load('gado'), pd.DataFrame([n])], ignore_index=True), 'gado')
                    st.rerun()
    
    st.dataframe(load('gado'), use_container_width=True)

# === CHECKLIST (CALENDÁRIO DARK) ===
elif menu == "✅ Checklist":
    st.title("✅ Controle Operacional")
    
    # Lançamento
    with st.expander("📝 Hoje", expanded=True):
        with st.form("check"):
            st.write(f"Data: {datetime.now().strftime('%d/%m/%Y')}")
            c1, c2 = st.columns(2)
            sal = c1.checkbox("Sal / Ração")
            agua = c2.checkbox("Água")
            obs = st.text_area("Obs")
            if st.form_submit_button("Salvar"):
                n = {'Data': datetime.now().strftime("%Y-%m-%d"), 'Responsavel': 'User', 'Sal': sal, 'Agua': agua, 'Cerca': True, 'Obs': obs}
                save(pd.concat([load('check'), pd.DataFrame([n])], ignore_index=True), 'check')
                st.rerun()

    # Calendário
    st.markdown("### Mapa Mensal")
    df_c = load('check')
    hoje = datetime.now()
    dias_mes = calendar.monthrange(hoje.year, hoje.month)[1]
    
    cols = st.columns(7)
    dias = ['S', 'T', 'Q', 'Q', 'S', 'S', 'D']
    for i, d in enumerate(dias): cols[i].markdown(f"**{d}**")
    
    idx = datetime(hoje.year, hoje.month, 1).weekday()
    for _ in range(idx): cols[_].write("")
    
    for d in range(1, dias_mes + 1):
        iso = f"{hoje.year}-{hoje.month:02d}-{d:02d}"
        feito = not df_c[df_c['Data']==iso].empty
        cor = "feito" if feito else "pendente"
        icone = "✅" if feito else ""
        cols[idx].markdown(f'<div class="dia-box {cor}">{d}<br>{icone}</div>', unsafe_allow_html=True)
        idx += 1
        if idx > 6: idx = 0

# === PASTOS & EQUIPE (SIMPLIFICADO) ===
elif menu == "🌾 Pastos":
    st.title("🌾 Pastos")
    with st.form("p"):
        nome = st.text_input("Nome")
        area = st.number_input("Ha")
        if st.form_submit_button("Salvar"):
            save(pd.concat([load('pastos'), pd.DataFrame([{'Nome': nome, 'Area_ha': area, 'Capim': '-'}])], ignore_index=True), 'pastos')
            st.rerun()
    st.dataframe(load('pastos'))

elif menu == "👥 Equipe":
    st.title("👥 Equipe")
    with st.form("e"):
        nome = st.text_input("Nome")
        if st.form_submit_button("Add"):
            save(pd.concat([load('users'), pd.DataFrame([{'Nome': nome, 'Funcao': 'Operacional'}])], ignore_index=True), 'users')
            st.rerun()
    st.dataframe(load('users'))
