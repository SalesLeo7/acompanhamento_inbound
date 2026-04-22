import streamlit as st
import pandas as pd

## configuração da pagina

st.set_page_config(page_title="Acomapanhamento de Inbound", layout="wide")
st.title("Acomapanhamento de Inbound (RECDOK)")

## Carregando os dados
import os

@st.cache_data
def carregar_dados():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, 'base_inventory', 'inventory_corrigido.csv')

    inbound = pd.read_csv(file_path, index_col=0, header=1)
    inbound = inbound.iloc[:, [0,1,2,3,4,5,18,29,30,31]]
    inbound['receipt_dstamp'] = pd.to_datetime(inbound['receipt_dstamp'], dayfirst=True, errors='coerce')
    inbound['lead_time_dias'] = (pd.Timestamp.today() - inbound['receipt_dstamp']).dt.days
    return inbound

inbound = carregar_dados()

## barra lateral

st.sidebar.header("Filtros")

owner = st.sidebar.multiselect(
    "Owner ID",
    options=inbound['owner_id'].unique(),
    default=inbound['owner_id'].unique()
)

site = st.sidebar.multiselect(
    "Site ID",
    options=inbound['site_id'].unique(),
    default=inbound['site_id'].unique()
)

# filtro de data
data_inicio, data_fim = st.sidebar.date_input(
    "Período (Receipt Date)",
    value=(
        inbound['receipt_dstamp'].min(),
        inbound['receipt_dstamp'].max()
    )
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
col2.metric("Lead Time Médio", f"{inbound_filtrado['lead_time_dias'].mean():.0f} dias")
col3.metric("Maior Lead Time", f"{inbound_filtrado['lead_time_dias'].max()} dias")

st.divider()

## Gráfico de barras - Lead time médio por Owner
st.subheader("Lead Time Médio por Owner")
lead_owner = inbound_filtrado.groupby('owner_id')['lead_time_dias'].mean().sort_values(ascending=False)
st.bar_chart(lead_owner)

## Gráfico de linha - Recebimentos ao longo do tempo
st.subheader("Recebimentos ao Longo do Tempo")
recebimentos = inbound_filtrado.groupby('receipt_dstamp').size()
st.line_chart(recebimentos)

## Tabela completa
st.subheader("Dados Completos")
st.dataframe(inbound_filtrado, use_container_width=True)