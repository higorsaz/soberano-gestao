import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
import calendar
import time

# --- 1. CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="SOBERANO | Gestão Rural", page_icon="🐂", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    div[data-testid="stMetric"] { background-color: #262730; border: 1px solid #41444C; padding: 15px; border-radius: 10px; color: white; }
    .dia-box { padding: 10px; border-radius: 8px; text-align: center; margin: 2px; font-weight: bold; border: 1px solid #555; font-size: 14px; background-color: #1E1E1E; }
    .feito { background-color: #1b5e20; color: white; border-color: #2e7d32; }
    .pendente { background-color: #b71c1c; color: white; border-color: #c62828; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BANCO DE DADOS E MIGRAÇÃO AUTOMÁTICA ---
FILES = {
    'gado': 'db_gado.csv',
    'pastos': 'db_pastos.csv',
    'check': 'db_checklist.csv',
    'users': 'db_equipe.csv',
    'market': 'db_mercado.csv',
    'diarias': 'db_diarias.csv'
}

def init_db():
    # Criação inicial se não existir
    if not os.path.exists(FILES['gado']):
        pd.DataFrame(columns=['ID', 'Brinco', 'Categoria', 'Peso_kg', 'Custo_Compra', 'Data_Entrada', 'Pasto', 'Status', 'Data_Saida', 'Motivo_Saida']).to_csv(FILES['gado'], index=False)
    if not os.path.exists(FILES['users']):
        pd.DataFrame(columns=['ID', 'Nome', 'Cargo', 'Funcao', 'Telefone', 'Status']).to_csv(FILES['users'], index=False)
        # Dono Padrão
        pd.DataFrame([{'ID': 1, 'Nome': 'Higor Azevedo', 'Cargo': 'Proprietário', 'Funcao': 'Gestão', 'Telefone': '', 'Status': 'Ativo'}]).to_csv(FILES['users'], index=False)
    
    # ... outros inits padrão ...
    if not os.path.exists(FILES['diarias']): pd.DataFrame(columns=['Data', 'Nome_Diarista', 'Servico', 'Valor_Diaria', 'Dias_Trab', 'Total_Pago', 'Obs']).to_csv(FILES['diarias'], index=False)
    if not os.path.exists(FILES['pastos']): pd.DataFrame([{'Nome': 'Pasto 01', 'Area_ha': 10.0, 'Capim': 'Braquiária'}]).to_csv(FILES['pastos'], index=False)
    if not os.path.exists(FILES['check']): pd.DataFrame(columns=['Data', 'Responsavel', 'Sal', 'Agua', 'Cerca', 'Obs']).to_csv(FILES['check'], index=False)
    if not os.path.exists(FILES['market']): pd.DataFrame([{'Data': datetime.now().strftime("%Y-%m-%d"), 'Arroba_Boi': 320.00, 'Bezerro': 3000.00, 'Milho': 60.00}]).to_csv(FILES['market'], index=False)

def check_migration():
    """Esta função conserta o erro KeyError: Cargo atualizando o arquivo antigo"""
    try:
        # 1. Conserta Tabela EQUIPE
        if os.path.exists(FILES['users']):
            df = pd.read_csv(FILES['users'])
            # Se faltar coluna Cargo ou Status, adiciona
            changed = False
            if 'Cargo' not in df.columns:
                df['Cargo'] = 'Operacional' # Valor padrão pra quem já existia
                changed = True
            if 'Status' not in df.columns:
                df['Status'] = 'Ativo'
                changed = True
            
            # Garante que o Dono tenha o cargo certo para login
            df.loc[df['Nome'] == 'Higor Azevedo', 'Cargo'] = 'Proprietário'
            
            if changed:
                df.to_csv(FILES['users'], index=False)
                
        # 2. Conserta Tabela GADO (Para Venda/Baixa)
        if os.path.exists(FILES['gado']):
            df = pd.read_csv(FILES['gado'])
            changed = False
            for col in ['Data_Saida', 'Motivo_Saida']:
                if col not in df.columns:
                    df[col] = ''
                    changed = True
            if changed:
                df.to_csv(FILES['gado'], index=False)
                
    except Exception as e:
        st.error(f"Erro na Migração: {e}")

def load(k): return pd.read_csv(FILES[k])
def save(df, k): df.to_csv(FILES[k], index=False)

# Roda inicialização e correção
init_db()
check_migration()

# --- 3. LOGIN ---
st.sidebar.title("🤠 SOBERANO")
perfil = st.sidebar.selectbox("Acesso", ["Proprietário", "Equipe"])
modo_admin = False

if perfil == "Proprietário":
    if st.sidebar.text_input("Senha Admin", type="password") == "123":
        modo_admin = True
        st.sidebar.success("✅ Logado")
        menu = st.sidebar.radio("MENU", ["📊 Dashboard", "🐂 Rebanho (Entradas)", "📉 Saídas / Baixas", "👥 RH & Diárias", "🌾 Pastos", "✅ Checklist"])
    else:
        menu = "Bloqueado"
else:
    # Carrega usuários e filtra com segurança
    df_u = load('users')
    # Filtra apenas quem NÃO é proprietário para a lista de funcionários
    lista_func = df_u[df_u['Cargo'] != 'Proprietário']['Nome'].tolist()
    
    if not lista_func: 
        lista_func = ["Visitante"]
        
    func = st.sidebar.selectbox("Seu Nome", lista_func)
    st.sidebar.info(f"Olá, {func}")
    menu = st.sidebar.radio("MENU", ["✅ Checklist", "🐂 Consulta Rebanho"])

st.sidebar.markdown("---")

# --- 4. SISTEMA ---

if menu == "Bloqueado":
    st.title("🔒 Acesso Restrito")

# === DASHBOARD ===
elif menu == "📊 Dashboard":
    st.title("📊 Visão Geral")
    
    # Mercado
    with st.expander("💰 Cotações (Editar)", expanded=False):
        last = load('market').iloc[-1]
        with st.form("mkt"):
            c1, c2, c3 = st.columns(3)
            boi = c1.number_input("@ Boi (R$)", value=float(last['Arroba_Boi']))
            bez = c2.number_input("Bezerro (R$)", value=float(last['Bezerro']))
            mil = c3.number_input("Milho (R$)", value=float(last.get('Milho', 60)))
            if st.form_submit_button("Atualizar"):
                save(pd.concat([load('market'), pd.DataFrame([{'Data': datetime.now().strftime("%Y-%m-%d"), 'Arroba_Boi': boi, 'Bezerro': bez, 'Milho': mil}])], ignore_index=True), 'market')
                st.rerun()

    df_g = load('gado')
    df_d = load('diarias')
    ativos = df_g[df_g['Status']=='Ativo']
    custo_rh = df_d['Total_Pago'].sum()
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Gado Ativo", len(ativos))
    
    peso_tot = ativos['Peso_kg'].sum()
    val_vivo = (peso_tot / 30) * boi
    k2.metric("Patrimônio Vivo", f"R$ {val_vivo:,.2f}")
    k3.metric("Gasto Diárias", f"R$ {custo_rh:,.2f}")
    
    custo_compra = ativos['Custo_Compra'].sum()
    lucro = val_vivo - custo_compra - custo_rh
    k4.metric("Lucro Proj.", f"R$ {lucro:,.2f}")

# === RH E DIÁRIAS ===
elif menu == "👥 RH & Diárias":
    st.title("👥 Departamento Pessoal")
    tab1, tab2 = st.tabs(["Funcionários Fixos", "Diaristas"])
    
    with tab1:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("### Cadastro")
            with st.form("rh"):
                df_u = load('users')
                # Filtra lista de edição
                edits = ["Novo Cadastro"] + df_u[df_u['Cargo']!='Proprietário']['Nome'].tolist()
                sel = st.selectbox("Editar:", edits)
                
                n_ini, c_ini, f_ini = "", "Peão", "Geral"
                if sel != "Novo Cadastro":
                    d = df_u[df_u['Nome']==sel].iloc[0]
                    n_ini, c_ini, f_ini = d['Nome'], d['Cargo'], d['Funcao']
                
                nome = st.text_input("Nome", value=n_ini)
                cargo = st.selectbox("Cargo", ["Gerente", "Capataz", "Peão", "Tratorista", "Cozinheira", "Outros"], index=0)
                funcao = st.text_input("Função", value=f_ini)
                
                if st.form_submit_button("Salvar"):
                    if sel != "Novo Cadastro": df_u = df_u[df_u['Nome']!=sel]
                    novo = {'ID': int(time.time()), 'Nome': nome, 'Cargo': cargo, 'Funcao': funcao, 'Telefone': '', 'Status': 'Ativo'}
                    save(pd.concat([df_u, pd.DataFrame([novo])], ignore_index=True), 'users')
                    st.rerun()
        with c2:
            st.dataframe(df_u[['Nome', 'Cargo', 'Funcao']])
            exc = st.selectbox("Demitir:", edits)
            if st.button("Confirmar Demissão") and exc != "Novo Cadastro":
                save(df_u[df_u['Nome']!=exc], 'users')
                st.rerun()

    with tab2:
        st.markdown("### Lançar Diária")
        with st.form("dia"):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Prestador")
            serv = c2.text_input("Serviço")
            c3, c4 = st.columns(2)
            val = c3.number_input("Valor Diária", value=100.0)
            dias = c4.number_input("Dias", value=1)
            if st.form_submit_button("Lançar"):
                reg = {'Data': datetime.now().strftime("%Y-%m-%d"), 'Nome_Diarista': nome, 'Servico': serv, 'Valor_Diaria': val, 'Dias_Trab': dias, 'Total_Pago': val*dias, 'Obs': ''}
                save(pd.concat([load('diarias'), pd.DataFrame([reg])], ignore_index=True), 'diarias')
                st.rerun()
        st.dataframe(load('diarias'))

# === REBANHO ===
elif menu == "🐂 Rebanho (Entradas)" or menu == "🐂 Consulta Rebanho":
    st.title("🐂 Rebanho")
    if modo_admin and "Entradas" in menu:
        with st.expander("➕ Novo Animal"):
            with st.form("gad"):
                c1, c2, c3 = st.columns(3)
                b = c1.text_input("Brinco")
                c = c2.selectbox("Categoria", ["Bezerro", "Bezerra", "Garrote", "Novilha", "Boi Magro", "Boi Gordo", "Vaca", "Touro"])
                p = c3.number_input("Peso", min_value=0.0)
                cust = st.number_input("Custo Compra", min_value=0.0)
                pas = st.selectbox("Pasto", load('pastos')['Nome'].unique())
                if st.form_submit_button("Salvar"):
                    n = {'ID': int(time.time()), 'Brinco': b, 'Categoria': c, 'Peso_kg': p, 'Custo_Compra': cust, 'Pasto': pas, 'Status': 'Ativo', 'Data_Entrada': datetime.now().strftime("%Y-%m-%d"), 'Data_Saida': '', 'Motivo_Saida': ''}
                    save(pd.concat([load('gado'), pd.DataFrame([n])], ignore_index=True), 'gado')
                    st.rerun()
    st.dataframe(load('gado')[load('gado')['Status']=='Ativo'])

# === SAÍDAS ===
elif menu == "📉 Saídas / Baixas":
    st.title("📉 Baixas")
    df = load('gado')
    ativos = df[df['Status']=='Ativo']
    with st.form("bx"):
        sel = st.multiselect("Animais", ativos.apply(lambda x: f"{x['Brinco']} ({x['ID']})", axis=1))
        mot = st.selectbox("Motivo", ["Venda", "Morte", "Consumo"])
        val = st.number_input("Valor Venda Total")
        if st.form_submit_button("Confirmar"):
            ids = [int(x.split("(")[1].replace(")","")) for x in sel]
            for i in ids:
                df.loc[df['ID']==i, 'Status'] = 'Inativo'
                df.loc[df['ID']==i, 'Motivo_Saida'] = mot
            save(df, 'gado')
            st.rerun()

# === PASTOS ===
elif menu == "🌾 Pastos":
    st.title("🌾 Pastos")
    with st.form("pst"):
        n = st.text_input("Nome")
        a = st.number_input("Area")
        if st.form_submit_button("Salvar"):
            save(pd.concat([load('pastos'), pd.DataFrame([{'Nome': n, 'Area_ha': a, 'Capim': '-'}])], ignore_index=True), 'pastos')
            st.rerun()
    st.dataframe(load('pastos'))

# === CHECKLIST ===
elif menu == "✅ Checklist":
    st.title("✅ Checklist")
    with st.form("chk"):
        sal = st.checkbox("Sal")
        agua = st.checkbox("Água")
        obs = st.text_area("Obs")
        if st.form_submit_button("Salvar"):
            save(pd.concat([load('check'), pd.DataFrame([{'Data': datetime.now().strftime("%Y-%m-%d"), 'Responsavel': 'User', 'Sal': sal, 'Agua': agua, 'Obs': obs}])], ignore_index=True), 'check')
            st.rerun()
    st.dataframe(load('check').tail(10))
