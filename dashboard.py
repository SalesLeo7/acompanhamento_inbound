import streamlit as st
import pandas as pd
import os

## configuração da pagina
st.set_page_config(page_title="Acomapanhamento de Inbound", layout="wide")
st.title("Acomapanhamento de Inbound (RECDOK)")

## Carregando os dados
@st.cache_data
def carregar_dados():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, 'base_inventory', 'inventory_corrigido.csv')

    inbound = pd.read_csv(file_path, index_col=0, header=1)

    inbound = inbound.iloc[:, [0,1,2,3,4,5,18,29,30,31]]

    # 🔥 tratamento correto de data
    inbound['receipt_dstamp'] = pd.to_datetime(
        inbound['receipt_dstamp'],
        dayfirst=True,
        errors='coerce'
    )

    # 🔥 remove datas inválidas
    inbound = inbound[inbound['receipt_dstamp'].notna()]

    inbound['lead_time_dias'] = (
        pd.Timestamp.today() - inbound['receipt_dstamp']
    ).dt.days

    return inbound

inbound = carregar_dados()

## barra lateral
st.sidebar.header("Filtros")

owner = st.sidebar.multiselect(
    "Owner ID",
    options=inbound['owner_id'].dropna().unique(),
    default=inbound['owner_id'].dropna().unique()
)

site = st.sidebar.multiselect(
    "Site ID",
    options=inbound['site_id'].dropna().unique(),
    default=inbound['site_id'].dropna().unique()
)

# 🔥 proteção contra erro de data
min_date = inbound['receipt_dstamp'].min()
max_date = inbound['receipt_dstamp'].max()

if pd.isna(min_date) or pd.isna(max_date):
    st.error("Erro: coluna de datas inválida ou vazia.")
    st.stop()

data_inicio, data_fim = st.sidebar.date_input(
    "Período (Receipt Date)",
    value=(min_date, max_date)
)

# 🔥 filtro completo com data
inbound_filtrado = inbound[
    (inbound['owner_id'].isin(owner)) &
    (inbound['site_id'].isin(site)) &
    (inbound['receipt_dstamp'] >= pd.to_datetime(data_inicio)) &
    (inbound['receipt_dstamp'] <= pd.to_datetime(data_fim))
]

## cards de metricas
col1, col2, col3 = st.columns(3)

col1.metric("Total de Receipts", inbound_filtrado['receipt_id'].nunique())

col2.metric(
    "Lead Time Médio",
    f"{inbound_filtrado['lead_time_dias'].mean():.0f} dias"
    if not inbound_filtrado.empty else "0 dias"
)

col3.metric(
    "Maior Lead Time",
    f"{inbound_filtrado['lead_time_dias'].max()} dias"
    if not inbound_filtrado.empty else "0 dias"
)

st.divider()

## Gráfico de barras
st.subheader("Lead Time Médio por Owner")
lead_owner = inbound_filtrado.groupby('owner_id')['lead_time_dias'].mean().sort_values(ascending=False)
st.bar_chart(lead_owner)

## Gráfico de linha
st.subheader("Recebimentos ao Longo do Tempo")
recebimentos = inbound_filtrado.groupby('receipt_dstamp').size()
st.line_chart(recebimentos)

## Tabela
st.subheader("Dados Completos")
st.dataframe(inbound_filtrado, use_container_width=True)
