import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
import colorsys

# Função para escurecer uma cor RGB em 50%
def darken_color(hex_color, factor=0.5):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    h, s, v = colorsys.rgb_to_hsv(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
    v = max(0, v * factor)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))

# --- Configuração da Página ---
st.set_page_config(layout="wide")

# --- CSS Customizado para Estilização ---
st.markdown(
    """
    <style>
    .header {
        background-color: #008000;
        color: white;
        padding: 20px;
        text-align: center;
        font-size: 28px;
        font-weight: bold;
        border-radius: 10px;
        margin-bottom: 25px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Cabeçalho ---
st.markdown('<div class="header">PAINEL EXECUTIVO - MAPA</div>', unsafe_allow_html=True)

# --- Carregamento dos Dados ---
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_excel('projetos.xlsx')
        colunas_data = [
            'Data de recebimento (SEI)', 'Data de Início do projeto',
            'Previsão de entrega MVP', 'Previsão de término', 'Data de fim do projeto'
        ]
        for col in colunas_data:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
        return df
    except FileNotFoundError:
        st.error("Arquivo 'projetos.xlsx' não encontrado. Por favor, coloque o arquivo no mesmo diretório deste script.")
        return pd.DataFrame()

df = carregar_dados()

if not df.empty:
    # --- Filtros de Controle ---
    st.subheader("Filtros de Controle")
    col1, col2, col3, col col4, col5 = st.columns(5)
    
    with col1:
        secretarias_unicas = sorted(df['Secretaria'].dropna().unique())
        secretaria_filtro = st.multiselect("SECRETARIA", options=secretarias_unicas, placeholder="Selecione a(s) Secretaria(s)")
    
    with col2:
        tipos_unicos = sorted(df['Tipo'].dropna().unique())
        tipo_filtro = st.multiselect("TIPO", options=tipos_unicos, placeholder="Selecione o(s) Tipo(s)")
    
    with col3:
        subtipos_unicos = sorted(df['Subtipo'].dropna().unique())
        subtipo_filtro = st.multiselect("SUBTIPO", options=subtipos_unicos, placeholder="Selecione o(s) Subtipo(s)")
    
    with col4:
        projetos_unicos = sorted(df['nome'].dropna().unique())
        projeto_filtro = st.multiselect("PROJETOS", options=projetos_unicos, placeholder="Selecione o(s) Projeto(s)")
    
    with col5:
        situacoes_unicas = sorted(df['Status do Projeto'].dropna().unique())
        situacao_filtro = st.multiselect("SITUAÇÃO DO PROJETO", options=situacoes_unicas, placeholder="Selecione a(s) Situação(s)")

    # --- Lógica de Filtragem ---
    df_filtrado = df.copy()
    if secretaria_filtro:
        df_filtrado = df_filtrado[df_filtrado['Secretaria'].isin(secretaria_filtro)]
    if tipo_filtro:
        df_filtrado = df_filtrado[df_filtrado['Tipo'].isin(tipo_filtro)]
    if subtipo_filtro:
        df_filtrado = df_filtrado[df_filtrado['Subtipo'].isin(subtipo_filtro)]
    if projeto_filtro:
        df_filtrado = df_filtrado[df_filtrado['nome'].isin(projeto_filtro)]
    if situacao_filtro:
        df_filtrado = df_filtrado[df_filtrado['Status do Projeto'].isin(situacao_filtro)]

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Box de KPIs (Indicadores) ---
    st.subheader("Resumo dos Projetos")
    total_projetos = len(df_filtrado)
    projetos_andamento = len(df_filtrado[df_filtrado['Status do Projeto'] == 'Em andamento'])
    projetos_concluidos = len(df_filtrado[df_filtrado['Status do Projeto'] == 'Concluído'])
    projetos_paralisados = len(df_filtrado[df_filtrado['Status do Projeto'] == 'Paralisado / Despriorizado'])
    projetos_internos = len(df_filtrado[df_filtrado['Tipo'] == 'INTERNO'])
    projetos_externos = len(df_filtrado[df_filtrado['Tipo'] == 'EXTERNO'])

    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
    kpi1.metric(label="PROJETOS", value=total_projetos)
    kpi2.metric(label="EM ANDAMENTO", value=projetos_andamento)
    kpi3.metric(label="CONCLUÍDOS", value=projetos_concluidos)
    kpi4.metric(label="PARALISADOS", value=projetos_paralisados)
    kpi5.metric(label="INTERNOS", value=projetos_internos)
    kpi6.metric(label="EXTERNOS", value=projetos_externos)

    st.markdown("---")

    # --- Gráfico de Gantt (Cronograma) ---
    st.subheader("Cronograma dos Projetos (Gráfico de Gantt)")

    # Prepara o dataframe para o gráfico, removendo projetos sem datas essenciais
    df_grafico = df_filtrado.dropna(subset=['Data de Início do projeto', 'Previsão de término']).copy()

    # Calcula a duração do MVP com base no percentual de Andamento MVP
    df_grafico['Andamento MVP'] = pd.to_numeric(df_grafico['Andamento MVP'], errors='coerce').fillna(0)
    df_grafico['MVP End'] = df_grafico.apply(
        lambda row: row['Data de Início do projeto'] + timedelta(days=(
            (row['Previsão de término'] - row['Data de Início do projeto']).days * row['Andamento MVP'] / 100
        )) if row['Andamento MVP'] > 0 else row['Data de Início do projeto'],
        axis=1
    )
    # Formata o texto do Andamento MVP para exibição
    df_grafico['Andamento MVP Text'] = df_grafico['Andamento MVP'].apply(lambda x: f"{x:.0f}%" if x > 0 else "")

    if not df_grafico.empty:
        # Ordena os projetos pela data de início para melhor visualização
        df_grafico = df_grafico.sort_values(by='Data de Início do projeto')

        # Cria o gráfico de Gantt com plotly
        fig = go.Figure()

        # Adiciona a barra principal (duração total do projeto)
        for idx, row in df_grafico.iterrows():
            # Cor base para a barra principal
            base_color = px.colors.qualitative.Plotly[idx % len(px.colors.qualitative.Plotly)]
            # Cor mais escura (50%) para a barra de MVP
            mvp_color = darken_color(base_color, factor=0.5)

            # Barra principal (duração total do projeto)
            fig.add_trace(
                go.Bar(
                    x=[(row['Previsão de término'] - row['Data de Início do projeto']).days],
                    y=[row['nome']],
                    base=row['Data de Início do projeto'],
                    orientation='h',
                    marker=dict(
                        color=base_color,
                        opacity=1.0
                    ),
                    name=row['nome'],
                    text=row['nome'],
                    textposition='outside',
                    showlegend=False
                )
            )
            # Adiciona a barra de MVP (mais escura)
            if row['Andamento MVP'] > 0:
                fig.add_trace(
                    go.Bar(
                        x=[(row['MVP End'] - row['Data de Início do projeto']).days],
                        y=[row['nome']],
                        base=row['Data de Início do projeto'],
                        orientation='h',
                        marker=dict(
                            color=mvp_color,
                            opacity=1.0
                        ),
                        name=f"{row['nome']} MVP",
                        text=row['Andamento MVP Text'],
                        textposition='inside',
                        showlegend=False
                    )
                )

        # Atualizações de layout para melhor visualização
        fig.update_layout(
            title_text='Duração dos Projetos',
            xaxis_title='Linha do Tempo',
            yaxis_title=None,
            showlegend=False,
            xaxis=dict(
                tickformat="%m/%Y",
                showgrid=True,
                gridcolor='LightGray'
            ),
            yaxis=dict(
                autorange="reversed"
            ),
            height=max(400, len(df_grafico) * 60),
            barmode='overlay'  # Permite sobreposição das barras
        )

        # Ajusta a fonte do texto
        fig.update_traces(textfont_size=14)

        # Exibe o gráfico no Streamlit
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Não há dados de data suficientes para exibir o cronograma para os filtros selecionados.")

    st.markdown("---")

    # --- Tabela de Dados Detalhados ---
    st.subheader("Detalhes dos Projetos Filtrados")
    df_para_exibir = df_filtrado.copy()
    colunas_data_formatar = [
        'Data de recebimento (SEI)', 'Data de Início do projeto',
        'Previsão de entrega MVP', 'Previsão de término', 'Data de fim do projeto'
    ]
    for col in colunas_data_formatar:
        if col in df_para_exibir.columns:
            df_para_exibir[col] = pd.to_datetime(df_para_exibir[col]).dt.strftime('%d/%m/%Y')
    st.dataframe(df_para_exibir, use_container_width=True)
