import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
import calendar
import time

# --- 1. CONFIGURAÇÃO VISUAL PREMIUM (DARK MODE) ---
st.set_page_config(page_title="SOBERANO | Gestão Rural", page_icon="🐂", layout="wide")

st.markdown("""
    <style>
    /* Estilo Global Dark */
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    
    /* Cards */
    div[data-testid="stMetric"] { background-color: #262730; border: 1px solid #41444C; padding: 15px; border-radius: 10px; color: white; }
    
    /* Calendário */
    .dia-box { padding: 10px; border-radius: 8px; text-align: center; margin: 2px; font-weight: bold; border: 1px solid #555; font-size: 14px; background-color: #1E1E1E; }
    .feito { background-color: #1b5e20; color: white; border-color: #2e7d32; }
    .pendente { background-color: #b71c1c; color: white; border-color: #c62828; }
    
    /* Botões */
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    
    /* Tabelas */
    .stDataFrame { border: 1px solid #444; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BANCO DE DADOS ---
FILES = {
    'gado': 'db_gado.csv',
    'pastos': 'db_pastos.csv',
    'check': 'db_checklist.csv',
    'users': 'db_equipe.csv',
    'market': 'db_mercado.csv',
    'diarias': 'db_diarias.csv'
}

def init_db():
    # GADO
    if not os.path.exists(FILES['gado']):
        pd.DataFrame(columns=['ID', 'Brinco', 'Categoria', 'Peso_kg', 'Custo_Compra', 'Data_Entrada', 'Pasto', 'Status', 'Data_Saida', 'Motivo_Saida']).to_csv(FILES['gado'], index=False)
    
    # FUNCIONÁRIOS (FIXOS)
    if not os.path.exists(FILES['users']):
        pd.DataFrame(columns=['ID', 'Nome', 'Cargo', 'Funcao', 'Telefone', 'Status']).to_csv(FILES['users'], index=False)
        # Cria dono padrão
        pd.DataFrame([{'ID': 1, 'Nome': 'Higor Azevedo', 'Cargo': 'Proprietário', 'Funcao': 'Gestão', 'Telefone': '', 'Status': 'Ativo'}]).to_csv(FILES['users'], index=False)
    
    # DIÁRIAS (TEMPORÁRIOS)
    if not os.path.exists(FILES['diarias']):
        pd.DataFrame(columns=['Data', 'Nome_Diarista', 'Servico', 'Valor_Diaria', 'Dias_Trab', 'Total_Pago', 'Obs']).to_csv(FILES['diarias'], index=False)
    
    # PASTOS
    if not os.path.exists(FILES['pastos']):
        pd.DataFrame([{'Nome': 'Pasto 01', 'Area_ha': 10.0, 'Capim': 'Braquiária'}]).to_csv(FILES['pastos'], index=False)
    
    # CHECKLIST
    if not os.path.exists(FILES['check']):
        pd.DataFrame(columns=['Data', 'Responsavel', 'Sal', 'Agua', 'Cerca', 'Obs']).to_csv(FILES['check'], index=False)
    
    # MERCADO
    if not os.path.exists(FILES['market']):
        pd.DataFrame([{'Data': datetime.now().strftime("%Y-%m-%d"), 'Arroba_Boi': 320.00, 'Bezerro': 3000.00, 'Milho': 60.00}]).to_csv(FILES['market'], index=False)

def load(k): return pd.read_csv(FILES[k])
def save(df, k): df.to_csv(FILES[k], index=False)

init_db()

# --- 3. LOGIN & MENU ---
st.sidebar.title("🤠 SOBERANO")
st.sidebar.caption("Gestão Rural Integrada")

perfil = st.sidebar.selectbox("Acesso", ["Proprietário", "Equipe"])
modo_admin = False

if perfil == "Proprietário":
    senha = st.sidebar.text_input("Senha Admin", type="password")
    if senha == "123":
        modo_admin = True
        st.sidebar.success("✅ Logado")
        menu = st.sidebar.radio("MENU PRINCIPAL", [
            "📊 Dashboard", 
            "🐂 Rebanho (Entradas)", 
            "📉 Saídas / Baixas", 
            "👥 RH & Diárias",
            "🌾 Pastos", 
            "✅ Checklist"
        ])
    else:
        menu = "Bloqueado"
else:
    # Login de Funcionário
    df_u = load('users')
    lista = df_u[df_u['Cargo'] != 'Proprietário']['Nome'].tolist()
    nome_func = st.sidebar.selectbox("Seu Nome", lista if lista else ["Visitante"])
    st.sidebar.info(f"Olá, {nome_func}")
    menu = st.sidebar.radio("MENU", ["✅ Checklist", "🐂 Consulta Rebanho"])

st.sidebar.markdown("---")

# --- 4. TELAS DO SISTEMA ---

if menu == "Bloqueado":
    st.title("🔒 Acesso Restrito")
    st.warning("Por favor, insira a senha de proprietário.")

# === DASHBOARD ===
elif menu == "📊 Dashboard":
    st.title("📊 Visão Geral da Fazenda")
    
    # Atualização Rápida de Mercado
    with st.expander("💰 Cotações do Dia (Editar)", expanded=False):
        last = load('market').iloc[-1]
        with st.form("mkt"):
            c1, c2, c3 = st.columns(3)
            boi = c1.number_input("@ Boi Gordo (R$)", value=float(last['Arroba_Boi']))
            bez = c2.number_input("Bezerro (R$)", value=float(last['Bezerro']))
            mil = c3.number_input("Milho/Saca (R$)", value=float(last.get('Milho', 60.0)))
            if st.form_submit_button("Atualizar"):
                save(pd.concat([load('market'), pd.DataFrame([{'Data': datetime.now().strftime("%Y-%m-%d"), 'Arroba_Boi': boi, 'Bezerro': bez, 'Milho': mil}])], ignore_index=True), 'market')
                st.rerun()

    # Indicadores
    df_g = load('gado')
    df_d = load('diarias')
    ativos = df_g[df_g['Status']=='Ativo']
    custo_rh = df_d['Total_Pago'].sum()
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Rebanho Ativo", len(ativos))
    
    # Patrimônio Estimado
    peso_tot = ativos['Peso_kg'].sum()
    valor_vivo = (peso_tot / 30) * boi
    k2.metric("Patrimônio Vivo", f"R$ {valor_vivo:,.2f}")
    
    # Custo Diárias
    k3.metric("Gasto Diárias", f"R$ {custo_rh:,.2f}", delta="-Saída")
    
    # Lucro Bruto (Venda Estimada - Custo Gado - Custo Diárias)
    custo_gado = ativos['Custo_Compra'].sum()
    lucro = valor_vivo - custo_gado - custo_rh
    k4.metric("Resultado Proj.", f"R$ {lucro:,.2f}", delta_color="normal")
    
    st.markdown("---")
    
    # Gráficos
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Rebanho por Categoria")
        if not ativos.empty:
            fig = px.pie(ativos, names='Categoria', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
            
    with g2:
        st.subheader("Custos Recentes (Diárias)")
        if not df_d.empty:
            st.dataframe(df_d.tail(5)[['Data', 'Nome_Diarista', 'Total_Pago']], use_container_width=True)

# === RH & DIÁRIAS (COMPLETO) ===
elif menu == "👥 RH & Diárias":
    st.title("👥 Departamento Pessoal")
    
    tab1, tab2 = st.tabs(["👔 Funcionários Fixos", "🛠️ Diaristas & Serviços"])
    
    # TAB 1: FIXOS
    with tab1:
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.markdown("### 📝 Cadastro/Edição")
            with st.form("rh_fixo"):
                df_u = load('users')
                # Filtra só funcionários para edição (exclui dono da lista de edição fácil para segurança)
                lista_edit = ["Novo Cadastro"] + df_u[df_u['Cargo']!='Proprietário']['Nome'].tolist()
                selecao = st.selectbox("Editar:", lista_edit)
                
                nome_ini = ""
                cargo_ini = "Peão"
                func_ini = "Geral"
                
                if selecao != "Novo Cadastro":
                    dado = df_u[df_u['Nome'] == selecao].iloc[0]
                    nome_ini = dado['Nome']
                    cargo_ini = dado['Cargo']
                    func_ini = dado['Funcao']
                
                nome = st.text_input("Nome", value=nome_ini)
                cargo = st.selectbox("Cargo", ["Gerente", "Capataz", "Peão", "Tratorista", "Cozinheira", "Outros"], index=0)
                funcao = st.text_input("Função Detalhada", value=func_ini)
                
                if st.form_submit_button("💾 Salvar Ficha"):
                    # Se for edição, remove antigo primeiro
                    if selecao != "Novo Cadastro":
                        df_u = df_u[df_u['Nome'] != selecao]
                    
                    novo = {'ID': int(time.time()), 'Nome': nome, 'Cargo': cargo, 'Funcao': funcao, 'Telefone': '', 'Status': 'Ativo'}
                    save(pd.concat([df_u, pd.DataFrame([novo])], ignore_index=True), 'users')
                    st.success("Salvo!")
                    time.sleep(1)
                    st.rerun()
                    
        with c2:
            st.markdown("### 📋 Quadro Atual")
            st.dataframe(df_u[['Nome', 'Cargo', 'Funcao']], use_container_width=True)
            
            with st.expander("🗑️ Excluir Funcionário"):
                apagar = st.selectbox("Quem demitir?", lista_edit)
                if st.button("Confirmar Demissão"):
                    if apagar != "Novo Cadastro":
                        save(df_u[df_u['Nome']!=apagar], 'users')
                        st.rerun()

    # TAB 2: DIARISTAS
    with tab2:
        st.markdown("### 💰 Lançamento de Diária")
        with st.form("diaria"):
            c1, c2, c3 = st.columns(3)
            nome_d = c1.text_input("Prestador", placeholder="Ex: João da Foice")
            servico = c2.text_input("Serviço", placeholder="Ex: Roçada Piquet 1")
            data_d = c3.date_input("Data", datetime.now())
            
            c4, c5, c6 = st.columns(3)
            val = c4.number_input("Valor Diária (R$)", value=100.0)
            dias = c5.number_input("Dias", value=1, min_value=1)
            total = val * dias
            c6.metric("Total", f"R$ {total:,.2f}")
            
            obs = st.text_area("Observações do Serviço")
            
            if st.form_submit_button("✅ Lançar Pagamento"):
                reg = {'Data': data_d.strftime("%Y-%m-%d"), 'Nome_Diarista': nome_d, 'Servico': servico, 'Valor_Diaria': val, 'Dias_Trab': dias, 'Total_Pago': total, 'Obs': obs}
                save(pd.concat([load('diarias'), pd.DataFrame([reg])], ignore_index=True), 'diarias')
                st.success("Lançado!")
                st.rerun()
        
        st.write("Histórico:")
        st.dataframe(load('diarias'))

# === REBANHO (ENTRADAS) ===
elif menu == "🐂 Rebanho (Entradas)" or menu == "🐂 Consulta Rebanho":
    st.title("🐂 Entrada de Animais")
    
    if modo_admin and "Entradas" in menu:
        with st.expander("➕ Novo Cadastro", expanded=True):
            with st.form("cad_gado"):
                c1, c2, c3 = st.columns(3)
                brinco = c1.text_input("Brinco")
                cat = c2.selectbox("Categoria", ["Bezerro", "Bezerra", "Garrote", "Novilha", "Boi Magro", "Boi Gordo", "Vaca", "Vaca Parida", "Vaca Prenha", "Vaca Vazia", "Touro"])
                peso = c3.number_input("Peso (kg)", min_value=0.0)
                
                c4, c5 = st.columns(2)
                custo = c4.number_input("Custo Compra (R$)", min_value=0.0)
                pasto = c5.selectbox("Pasto", load('pastos')['Nome'].unique())
                
                if st.form_submit_button("Salvar"):
                    n = {'ID': int(time.time()), 'Brinco': brinco, 'Categoria': cat, 'Peso_kg': peso, 'Custo_Compra': custo, 'Pasto': pasto, 'Status': 'Ativo', 'Data_Entrada': datetime.now().strftime("%Y-%m-%d"), 'Data_Saida': '', 'Motivo_Saida': ''}
                    save(pd.concat([load('gado'), pd.DataFrame([n])], ignore_index=True), 'gado')
                    st.success("Salvo!")
                    st.rerun()
    
    st.markdown("### 📋 Estoque no Pasto")
    df = load('gado')
    st.dataframe(df[df['Status']=='Ativo'], use_container_width=True)
    
    if modo_admin:
        with st.expander("🗑️ Excluir Registro (Erro de Digitação)"):
            ativos = df[df['Status']=='Ativo']
            lista = ativos.apply(lambda x: f"{x['Brinco']} - {x['Categoria']} (ID:{x['ID']})", axis=1).tolist()
            escolha = st.selectbox("Apagar qual?", ["Selecione..."] + lista)
            if st.button("Apagar Definitivamente"):
                if escolha != "Selecione...":
                    id_del = int(escolha.split("ID:")[1].replace(")",""))
                    save(df[df['ID']!=id_del], 'gado')
                    st.rerun()

# === SAÍDAS / BAIXAS ===
elif menu == "📉 Saídas / Baixas":
    st.title("📉 Registrar Saída (Venda/Morte)")
    
    df = load('gado')
    ativos = df[df['Status']=='Ativo']
    
    with st.form("baixa"):
        st.write("Selecione os animais que saíram da fazenda:")
        lista = ativos.apply(lambda x: f"{x['Brinco']} - {x['Categoria']} (ID:{x['ID']})", axis=1).tolist()
        sels = st.multiselect("Animais", lista)
        
        c1, c2, c3 = st.columns(3)
        motivo = c1.selectbox("Motivo", ["Venda", "Morte", "Abate Consumo", "Roubo"])
        data = c2.date_input("Data", datetime.now())
        valor = c3.number_input("Valor Total da Venda (Se houver)", min_value=0.0)
        
        if st.form_submit_button("Confirmar Baixa"):
            if sels:
                ids = [int(x.split("ID:")[1].replace(")","")) for x in sels]
                for i in ids:
                    df.loc[df['ID']==i, 'Status'] = 'Inativo'
                    df.loc[df['ID']==i, 'Motivo_Saida'] = motivo
                    df.loc[df['ID']==i, 'Data_Saida'] = data.strftime("%Y-%m-%d")
                save(df, 'gado')
                st.success("Baixa Realizada!")
                time.sleep(1)
                st.rerun()

# === PASTOS ===
elif menu == "🌾 Pastos":
    st.title("🌾 Gestão de Pastos")
    c1, c2 = st.columns(2)
    with c1:
        with st.form("p"):
            n = st.text_input("Nome")
            a = st.number_input("Ha")
            if st.form_submit_button("Criar"):
                save(pd.concat([load('pastos'), pd.DataFrame([{'Nome': n, 'Area_ha': a, 'Capim': '-'}])], ignore_index=True), 'pastos')
                st.rerun()
    with c2:
        df_p = load('pastos')
        delt = st.selectbox("Excluir Pasto", ["Selecione..."]+df_p['Nome'].tolist())
        if st.button("Apagar Pasto"):
            if delt != "Selecione...":
                save(df_p[df_p['Nome']!=delt], 'pastos')
                st.rerun()
    st.dataframe(load('pastos'))

# === CHECKLIST ===
elif menu == "✅ Checklist":
    st.title("✅ Rotina Operacional")
    with st.expander("📝 Hoje", expanded=True):
        with st.form("check"):
            st.write(f"Data: {datetime.now().strftime('%d/%m/%Y')}")
            c1, c2 = st.columns(2)
            sal = c1.checkbox("Sal / Cocho")
            agua = c2.checkbox("Água / Bebedouro")
            obs = st.text_area("Ocorrências")
            if st.form_submit_button("Salvar"):
                save(pd.concat([load('check'), pd.DataFrame([{'Data': datetime.now().strftime("%Y-%m-%d"), 'Responsavel': 'User', 'Sal': sal, 'Agua': agua, 'Obs': obs}])], ignore_index=True), 'check')
                st.rerun()
    
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
