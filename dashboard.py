import streamlit as st
import pandas as pd
import os

## Configuração da página
st.set_page_config(page_title="Acompanhamento de Inbound", layout="wide")
st.title("Acompanhamento de Inbound (RECDOK)")

## Carregando os dados
@st.cache_data
def carregar_dados():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, 'base_inventory', 'inventory_corrigido.csv')

    # Leitura do CSV:
    # - header=1 → usa a 2ª linha como cabeçalho (nomes de código como receipt_id, owner_id etc.)
    # - index_col=0 → usa a 1ª coluna (key,tag_id) como índice
    inbound = pd.read_csv(file_path, index_col=0, header=1)

    # ✅ CORREÇÃO PRINCIPAL: seleção por NOME de coluna, não por posição.
    # O iloc[:, [0,1,2,3,4,5,18,29,30,31]] estava errado porque com index_col=0
    # a coluna receipt_id fica na posição 28, não 29 — deslocando tudo.
    colunas_necessarias = [
        'client_id',
        'owner_id',
        'sku_id',
        'site_id',
        'location_id',
        'description',
        'qty_on_hand',
        'receipt_id',
        'line_id',
        'receipt_dstamp',
    ]

    # Verifica se todas as colunas existem antes de selecionar
    colunas_faltando = [c for c in colunas_necessarias if c not in inbound.columns]
    if colunas_faltando:
        raise ValueError(
            f"Colunas não encontradas no arquivo: {colunas_faltando}. "
            f"Colunas disponíveis: {inbound.columns.tolist()}"
        )

    inbound = inbound[colunas_necessarias]

    # Padroniza nomes (strip de espaços extras, lowercase)
    inbound.columns = inbound.columns.str.strip().str.lower()

    # Trata datas
    inbound['receipt_dstamp'] = pd.to_datetime(
        inbound['receipt_dstamp'],
        format='%d/%m/%Y',
        errors='coerce'
    )

    # Remove linhas sem data válida
    inbound = inbound[inbound['receipt_dstamp'].notna()]

    if inbound.empty:
        raise ValueError("Nenhuma linha com data válida encontrada no arquivo.")

    # Lead time em dias (da data de recebimento até hoje)
    inbound['lead_time_dias'] = (
        pd.Timestamp.today() - inbound['receipt_dstamp']
    ).dt.days

    return inbound


# Tratamento de erro FORA do @st.cache_data
# (st.error e st.stop não funcionam corretamente dentro de funções cacheadas)
inbound = None
try:
    inbound = carregar_dados()
except ValueError as e:
    st.error(f"Erro ao carregar os dados: {e}")
except FileNotFoundError:
    st.error("Arquivo 'inventory_corrigido.csv' não encontrado na pasta 'base_inventory'.")
except Exception as e:
    st.error(f"Erro inesperado: {e}")

# st.stop() chamado UMA VEZ, fora do except,
# para não ser capturado acidentalmente pelo bloco de exceção
if inbound is None:
    st.stop()

## SIDEBAR — Filtros
st.sidebar.header("Filtros")

owner = st.sidebar.multiselect(
    "Owner ID",
    options=sorted(inbound['owner_id'].dropna().unique()),
    default=sorted(inbound['owner_id'].dropna().unique())
)

site = st.sidebar.multiselect(
    "Site ID",
    options=sorted(inbound['site_id'].dropna().unique()),
    default=sorted(inbound['site_id'].dropna().unique())
)

# Datas seguras
min_date = inbound['receipt_dstamp'].min()
max_date = inbound['receipt_dstamp'].max()

if pd.isna(min_date) or pd.isna(max_date):
    st.error("Erro: coluna de datas inválida.")
    st.stop()

data_range = st.sidebar.date_input(
    "Período (Receipt Date)",
    value=(min_date, max_date)
)

# Garante tupla com início e fim
if isinstance(data_range, tuple) and len(data_range) == 2:
    data_inicio, data_fim = data_range
else:
    data_inicio = data_fim = data_range if not isinstance(data_range, tuple) else data_range[0]

## FILTRO dos dados
inbound_filtrado = inbound.copy()

if owner:
    inbound_filtrado = inbound_filtrado[inbound_filtrado['owner_id'].isin(owner)]

if site:
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

## GRÁFICO 1 — Lead Time Médio por Owner
st.subheader("Lead Time Médio por Owner")

lead_owner = (
    inbound_filtrado
    .groupby('owner_id')['lead_time_dias']
    .mean()
    .sort_values(ascending=False)
)

st.bar_chart(lead_owner.head(10))

## GRÁFICO 2 — Recebimentos ao Longo do Tempo
st.subheader("Recebimentos ao Longo do Tempo")

recebimentos = (
    inbound_filtrado
    .groupby('receipt_dstamp')
    .size()
    .sort_index()
)

st.line_chart(recebimentos)

## TABELA — Dados Completos
st.subheader("Dados Completos")
st.dataframe(inbound_filtrado, use_container_width=True)
