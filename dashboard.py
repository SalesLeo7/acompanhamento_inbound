import streamlit as st
import pandas as pd
import os

## configuração da pagina
st.set_page_config(page_title="Acompanhamento de Inbound", layout="wide")
st.title("Acompanhamento de Inbound (RECDOK)")

## Carregando os dados
@st.cache_data
def carregar_dados():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, 'base_inventory', 'inventory2.csv')

    # 🔥 leitura mais segura
    inbound = pd.read_csv(file_path, index_col=0, header=1)

    inbound = inbound.iloc[:, [0, 1, 2, 3, 4, 5, 18, 29, 30, 31]]

    # 🔥 padroniza nomes de colunas
    inbound.columns = inbound.columns.str.strip().str.lower()

    # 🔍 DEBUG (pode comentar depois)
    # st.write("Colunas:", inbound.columns.tolist())

    # 🔥 tenta identificar nomes automaticamente
    possible_receipt = [col for col in inbound.columns if 'receipt' in col and 'id' in col]
    possible_owner = [col for col in inbound.columns if 'owner' in col]
    possible_site = [col for col in inbound.columns if 'site' in col]
    possible_date = [col for col in inbound.columns if 'date' in col or 'dstamp' in col]

    if not possible_receipt:
        st.error("Coluna de receipt_id não encontrada.")
        st.stop()

    # usa o primeiro encontrado
    receipt_col = possible_receipt[0]
    owner_col = possible_owner[0] if possible_owner else None
    site_col = possible_site[0] if possible_site else None
    date_col = possible_date[0] if possible_date else None

    # 🔥 renomeia para padrão
    inbound = inbound.rename(columns={
        receipt_col: 'receipt_id',
        owner_col: 'owner_id' if owner_col else None,
        site_col: 'site_id' if site_col else None,
        date_col: 'receipt_dstamp' if date_col else None
    })

    # 🔥 trata datas
    inbound['receipt_dstamp'] = pd.to_datetime(
        inbound['receipt_dstamp'],
        format='%d/%m/%Y',
        errors='coerce'
    )

    inbound = inbound[inbound['receipt_dstamp'].notna()]

    # 🔥 lead time
    inbound['lead_time_dias'] = (
        pd.Timestamp.today() - inbound['receipt_dstamp']
    ).dt.days

    return inbound


inbound = carregar_dados()

## SIDEBAR
st.sidebar.header("Filtros")

owner = st.sidebar.multiselect(
    "Owner ID",
    options=sorted(inbound['owner_id'].dropna().unique()) if 'owner_id' in inbound else [],
    default=sorted(inbound['owner_id'].dropna().unique()) if 'owner_id' in inbound else []
)

site = st.sidebar.multiselect(
    "Site ID",
    options=sorted(inbound['site_id'].dropna().unique()) if 'site_id' in inbound else [],
    default=sorted(inbound['site_id'].dropna().unique()) if 'site_id' in inbound else []
)

# datas seguras
min_date = inbound['receipt_dstamp'].min()
max_date = inbound['receipt_dstamp'].max()

if pd.isna(min_date) or pd.isna(max_date):
    st.error("Erro: coluna de datas inválida.")
    st.stop()

data_range = st.sidebar.date_input(
    "Período (Receipt Date)",
    value=(min_date, max_date)
)

# garante tupla
if isinstance(data_range, tuple):
    data_inicio, data_fim = data_range
else:
    data_inicio = data_fim = data_range

## FILTRO
inbound_filtrado = inbound.copy()

if 'owner_id' in inbound and owner:
    inbound_filtrado = inbound_filtrado[inbound_filtrado['owner_id'].isin(owner)]

if 'site_id' in inbound and site:
    inbound_filtrado = inbound_filtrado[inbound_filtrado['site_id'].isin(site)]

inbound_filtrado = inbound_filtrado[
    (inbound_filtrado['receipt_dstamp'] >= pd.to_datetime(data_inicio)) &
    (inbound_filtrado['receipt_dstamp'] <= pd.to_datetime(data_fim))
]

## MÉTRICAS
col1, col2, col3 = st.columns(3)

col1.metric(
    "Total de Receipts",
    inbound_filtrado['receipt_id'].nunique()
)

media = inbound_filtrado['lead_time_dias'].mean()
col2.metric(
    "Lead Time Médio",
    f"{media:.0f} dias" if pd.notna(media) else "0 dias"
)

maximo = inbound_filtrado['lead_time_dias'].max()
col3.metric(
    "Maior Lead Time",
    f"{int(maximo)} dias" if pd.notna(maximo) else "0 dias"
)

st.divider()

## GRÁFICO 1
st.subheader("Lead Time Médio por Owner")

if 'owner_id' in inbound_filtrado:
    lead_owner = (
        inbound_filtrado
        .groupby('owner_id')['lead_time_dias']
        .mean()
        .sort_values(ascending=False)
    )

    st.bar_chart(lead_owner.head(10))

## GRÁFICO 2
st.subheader("Recebimentos ao Longo do Tempo")

recebimentos = (
    inbound_filtrado
    .groupby('receipt_dstamp')
    .size()
    .sort_index()
)

st.line_chart(recebimentos)

## TABELA
st.subheader("Dados Completos")
st.dataframe(inbound_filtrado, use_container_width=True)
