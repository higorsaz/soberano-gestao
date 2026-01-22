import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
import calendar
import time

# --- 1. VISUAL ---
st.set_page_config(page_title="SOBERANO | Gestão Rural", page_icon="🐂", layout="wide")
st.markdown("""<style>.stApp { background-color: #0E1117; color: #FAFAFA; } .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; } div[data-testid="stMetric"] { background-color: #262730; border: 1px solid #444; padding: 10px; border-radius: 5px; }</style>""", unsafe_allow_html=True)

# --- 2. DADOS ---
FILES = {'gado': 'db_gado.csv', 'users': 'db_equipe.csv', 'diarias': 'db_diarias.csv', 'pastos': 'db_pastos.csv', 'check': 'db_checklist.csv', 'market': 'db_mercado.csv'}

def init_db():
    # Inits simplificados (já existentes)
    if not os.path.exists(FILES['gado']): pd.DataFrame(columns=['ID', 'Brinco', 'Categoria', 'Peso_kg', 'Custo_Compra', 'Data_Entrada', 'Pasto', 'Status', 'Data_Saida', 'Motivo_Saida']).to_csv(FILES['gado'], index=False)
    if not os.path.exists(FILES['diarias']): pd.DataFrame(columns=['Data', 'Nome_Diarista', 'Servico', 'Valor_Diaria', 'Dias_Trab', 'Total_Pago', 'Obs']).to_csv(FILES['diarias'], index=False)
    if not os.path.exists(FILES['market']): pd.DataFrame([{'Data': datetime.now().strftime("%Y-%m-%d"), 'Arroba_Boi': 320.00, 'Bezerro': 3000.00, 'Milho': 60.00}]).to_csv(FILES['market'], index=False)
    # (Mantém os outros inits para não bugar)
    if not os.path.exists(FILES['users']): pd.DataFrame([{'ID':1, 'Nome':'Higor', 'Cargo':'Proprietário', 'Funcao':'Gestão', 'Status':'Ativo'}]).to_csv(FILES['users'], index=False)
    if not os.path.exists(FILES['pastos']): pd.DataFrame([{'Nome':'Pasto A', 'Area_ha':10, 'Capim':'-'}]).to_csv(FILES['pastos'], index=False)
    if not os.path.exists(FILES['check']): pd.DataFrame(columns=['Data','Responsavel','Sal','Agua','Obs']).to_csv(FILES['check'], index=False)

def check_migration():
    # Função de segurança para arquivos antigos
    try:
        if os.path.exists(FILES['users']):
            df = pd.read_csv(FILES['users'])
            if 'Cargo' not in df.columns: 
                df['Cargo'] = 'Operacional'; df.to_csv(FILES['users'], index=False)
    except: pass

def load(k): return pd.read_csv(FILES[k])
def save(df, k): df.to_csv(FILES[k], index=False)

init_db()
check_migration()

# --- 3. MENU ---
st.sidebar.title("🤠 SOBERANO")
perfil = st.sidebar.selectbox("Acesso", ["Proprietário", "Equipe"])
modo_admin = False

if perfil == "Proprietário":
    if st.sidebar.text_input("Senha", type="password") == "123":
        modo_admin = True
        menu = st.sidebar.radio("MENU", ["📊 Dashboard", "🐂 Rebanho (Entradas)", "📉 Baixas", "👥 RH & Diárias", "🌾 Pastos", "✅ Checklist"])
    else: menu = "Bloqueado"
else:
    menu = "Bloqueado" # Simplificando para focar no erro

# --- 4. TELAS ---
if menu == "Bloqueado": st.title("🔒 Bloqueado")

# === DASHBOARD CORRIGIDO ===
elif menu == "📊 Dashboard":
    st.title("📊 Visão Financeira")
    
    # --- Cotações ---
    with st.expander("💰 Cotações (Influencia no cálculo do valor)", expanded=False):
        last = load('market').iloc[-1]
        with st.form("mkt"):
            c1, c2 = st.columns(2)
            boi = c1.number_input("@ Boi Gordo (R$)", value=float(last['Arroba_Boi']))
            bez = c2.number_input("Bezerro/Cabeça (R$)", value=float(last['Bezerro']))
            if st.form_submit_button("Atualizar Referência"):
                save(pd.concat([load('market'), pd.DataFrame([{'Data': datetime.now().strftime("%Y-%m-%d"), 'Arroba_Boi': boi, 'Bezerro': bez, 'Milho': 60}])], ignore_index=True), 'market')
                st.rerun()

    # --- Cálculos ---
    df_g = load('gado')
    ativos = df_g[df_g['Status']=='Ativo']
    
    # 1. Valor de Venda (Lógica Inteligente: Bezerro é p/ cabeça, Boi é p/ peso)
    def calcular_valor(row):
        if row['Categoria'] in ['Bezerro', 'Bezerra']:
            return bez # Preço fixo por cabeça (cotação do bezerro)
        else:
            # Outros animais calculados por Arroba (Peso / 30 * Arroba)
            return (row['Peso_kg'] / 30) * boi

    if not ativos.empty:
        ativos['Valor_Atual'] = ativos.apply(calcular_valor, axis=1)
        
        receita_potencial = ativos['Valor_Atual'].sum()
        custo_aquisicao = ativos['Custo_Compra'].sum()
        margem_bruta = receita_potencial - custo_aquisicao
        
        custo_operacional = load('diarias')['Total_Pago'].sum()
        lucro_liquido = margem_bruta - custo_operacional
        
        # --- EXIBIÇÃO ---
        st.markdown("### 1. Desempenho do Gado (Compra vs Venda)")
        k1, k2, k3 = st.columns(3)
        k1.metric("Valor Atual (Estoque)", f"R$ {receita_potencial:,.2f}", help="Soma do valor de mercado de todos animais")
        k2.metric("Custo de Compra", f"R$ {custo_aquisicao:,.2f}", help="O quanto você pagou neles")
        k3.metric("Margem Bruta (Gado)", f"R$ {margem_bruta:,.2f}", delta="Valorização", help="Valor Atual - Custo Compra")
        
        st.markdown("---")
        
        st.markdown("### 2. Resultado Final (Considerando Despesas)")
        d1, d2 = st.columns(2)
        d1.metric("Despesas Operacionais (Diárias)", f"R$ {custo_operacional:,.2f}", delta="-Saída", delta_color="inverse")
        d2.metric("LUCRO LÍQUIDO REAL", f"R$ {lucro_liquido:,.2f}", delta_color="normal", help="Margem Bruta - Despesas")
        
    else:
        st.info("Sem animais ativos.")

# === OUTROS MÓDULOS (RESUMIDOS PARA CABER) ===
elif menu == "🐂 Rebanho (Entradas)":
    st.title("🐂 Rebanho")
    if modo_admin:
        with st.form("add"):
            c1, c2, c3 = st.columns(3)
            b = c1.text_input("Brinco")
            cat = c2.selectbox("Categoria", ["Bezerro", "Bezerra", "Garrote", "Novilha", "Boi Magro", "Boi Gordo", "Vaca", "Touro"])
            peso = c3.number_input("Peso (kg)", min_value=0.0)
            custo = st.number_input("Custo Compra (R$)", min_value=0.0)
            if st.form_submit_button("Salvar"):
                n = {'ID':int(time.time()), 'Brinco':b, 'Categoria':cat, 'Peso_kg':peso, 'Custo_Compra':custo, 'Pasto':'-', 'Status':'Ativo', 'Data_Entrada': datetime.now().strftime("%Y-%m-%d"), 'Data_Saida':'', 'Motivo_Saida':''}
                save(pd.concat([load('gado'), pd.DataFrame([n])], ignore_index=True), 'gado')
                st.rerun()
    st.dataframe(load('gado')[load('gado')['Status']=='Ativo'])

elif menu == "👥 RH & Diárias":
    st.title("👥 RH")
    t1, t2 = st.tabs(["Fixos", "Diaristas"])
    with t2:
        with st.form("d"):
            val = st.number_input("Valor Total Pago", min_value=0.0)
            if st.form_submit_button("Lançar Pagamento"):
                save(pd.concat([load('diarias'), pd.DataFrame([{'Total_Pago':val, 'Data':datetime.now().strftime("%Y-%m-%d"), 'Nome_Diarista':'Geral', 'Servico':'-', 'Valor_Diaria':val, 'Dias_Trab':1, 'Obs':'-'}])], ignore_index=True), 'diarias')
                st.rerun()
        st.dataframe(load('diarias'))

# (Mantém Baixas, Pastos e Checklist iguais ao anterior - código abreviado aqui)
elif menu == "📉 Baixas": st.title("Baixas"); st.info("Use o menu anterior para código completo se precisar")
elif menu == "🌾 Pastos": st.title("Pastos"); st.dataframe(load('pastos'))
elif menu == "✅ Checklist": st.title("Checklist"); st.dataframe(load('check'))
