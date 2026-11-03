"""Painel de educação e gastos públicos do Tocantins.

Rode com ``streamlit run app/painel.py``. Os dados vêm do banco publicado na
branch ``dados`` (ver ``app/dados.py`` para as variáveis de ambiente).
"""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

import dados
import indicadores as ind

st.set_page_config(page_title="Educação no Tocantins", page_icon="📊", layout="wide")

# Paleta: sequencial azul para magnitude; categóricas em ordem fixa.
AZUL_SEQUENCIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
SERIE_1, SERIE_2, SERIE_3, SERIE_4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
CINZA = "#b9b8b2"
CORES_REDE = {"federal": SERIE_1, "estadual": SERIE_2, "municipal": SERIE_3, "privada": SERIE_4}


def layout(fig: go.Figure, altura: int = 420) -> go.Figure:
    fig.update_layout(
        height=altura,
        margin={"l": 8, "r": 8, "t": 48, "b": 8},
        separators=",.",
        font={"family": "Inter, system-ui, sans-serif", "size": 13},
        hoverlabel={"font_size": 13},
        legend={
            "orientation": "h",
            "y": 1.02,
            "yanchor": "bottom",
            "x": 0,
            "title": None,
            "traceorder": "normal",
        },
    )
    fig.update_xaxes(showgrid=False, linewidth=1, linecolor="rgba(128,128,128,.35)")
    fig.update_yaxes(gridcolor="rgba(128,128,128,.18)", gridwidth=1, zeroline=False)
    return fig


@st.cache_resource(show_spinner="Baixando o banco de dados…")
def carregar() -> dict:
    banco = dados.caminho_banco()
    return {
        "municipios": dados.municipios(banco),
        "geojson": dados.geojson_municipios(banco),
        "ideb": dados.ideb(banco),
        "despesa": dados.despesa_municipal(banco),
        "investimento": dados.investimento_aluno(banco),
        "siope": dados.mde_siope(banco),
        "matriculas": dados.matriculas(banco),
        "estado": dados.resumo_estadual(banco),
        "cargas": dados.ultima_carga(banco),
    }


d = carregar()
municipios = d["municipios"]
nomes = municipios["nome_municipio"].tolist()


def indice(nome: str) -> int:
    """Posição do município na lista (0 se não existir no banco)."""
    return nomes.index(nome) if nome in nomes else 0


st.title("Educação e gastos públicos no Tocantins")
st.caption(
    "Indicadores educacionais (INEP) e despesa com educação (SICONFI/Tesouro Nacional) "
    "dos 139 municípios. Valores em reais correntes."
)

# --- filtros, numa linha acima dos gráficos -------------------------------------------
c1, c2, c3, c4 = st.columns([2.2, 1.4, 1.2, 1])
indicador = c1.selectbox("Indicador", list(ind.INDICADORES), index=0)
definicao = ind.INDICADORES[indicador]
etapa = rede = None
if definicao.fonte == "ideb":
    etapa = c2.selectbox("Etapa", list(ind.ETAPAS), format_func=ind.ETAPAS.get)
    rede = c3.selectbox("Rede", list(ind.REDES), format_func=ind.REDES.get)
serie = ind.serie(d, indicador, etapa=etapa, rede=rede)
anos = sorted(serie["ano"].unique(), reverse=True)
if not anos:
    st.warning("Não há dados para esta combinação de filtros.")
    st.stop()
ano = c4.selectbox("Ano", anos)
recorte = serie[serie["ano"] == ano]

# --- números do Estado (último ano disponível até o ano escolhido) -----------------------
estado = d["estado"]


def ultimo_valor(coluna: str) -> tuple[float | None, int | None]:
    base = estado[(estado["ano"] <= ano) & estado[coluna].notna()]
    if base.empty:
        return None, None
    linha = base.sort_values("ano").iloc[-1]
    return linha[coluna], int(linha["ano"])


k1, k2, k3, k4 = st.columns(4)
valor, ano_ref = ultimo_valor("despesa_educacao_estado")
k1.metric(f"Despesa estadual em Educação ({ano_ref or '—'})", ind.reais(valor, curto=True))
valor, ano_ref = ultimo_valor("investimento_por_aluno_estado")
k2.metric(f"Investimento por aluno – rede estadual ({ano_ref or '—'})", ind.reais(valor))
valor, ano_ref = ultimo_valor("municipios_com_dca")
k3.metric(
    f"Municípios com DCA declarado ({ano_ref or '—'})",
    f"{int(valor)} de 139" if valor is not None else "—",
)
k4.metric(
    f"{definicao.rotulo_curto} – mediana dos municípios ({ano})",
    definicao.formatar(recorte["valor"].median()) if len(recorte) else "—",
)

nota = ind.nota_contexto(definicao, ano)
if nota:
    st.info(nota, icon=":material/gavel:")

abas = st.tabs(
    ["Mapa", "Ranking", "Evolução", "Investimento × IDEB", "Matrículas", "Comparar", "Sobre"]
)

# --- mapa ---------------------------------------------------------------------------------
with abas[0]:
    fig = px.choropleth_map(
        recorte,
        geojson=d["geojson"],
        locations="cod_municipio",
        color="valor",
        color_continuous_scale=AZUL_SEQUENCIAL,
        hover_name="nome_municipio",
        hover_data={"cod_municipio": False, "valor": definicao.formato_hover},
        labels={"valor": definicao.rotulo_curto},
        map_style="white-bg",  # sem mapa de fundo: nenhum serviço externo de tiles
        center={"lat": -10.2, "lon": -48.3},
        zoom=5.6,
        opacity=0.95,
    )
    fig.update_traces(marker_line_width=0.6, marker_line_color="white")
    fig.update_layout(coloraxis_colorbar={"title": None, "thickness": 12})
    st.subheader(f"{indicador} em {ano}")
    st.plotly_chart(layout(fig, 760), use_container_width=True)
    sem_dado = len(municipios) - recorte["cod_municipio"].nunique()
    if sem_dado:
        st.caption(f"{sem_dado} municípios sem dado neste recorte aparecem em branco.")

# --- ranking ----------------------------------------------------------------------------
with abas[1]:
    destaque = st.selectbox("Destacar município", nomes, index=indice("Palmas"))
    ordenado = recorte.sort_values("valor", ascending=True)
    cores = [SERIE_2 if n == destaque else SERIE_1 for n in ordenado["nome_municipio"]]
    fig = go.Figure(
        go.Bar(
            x=ordenado["valor"],
            y=ordenado["nome_municipio"],
            orientation="h",
            marker_color=cores,
            hovertemplate="%{y}: %{x" + definicao.formato_plotly + "}<extra></extra>",
        )
    )
    posicao = ordenado["nome_municipio"].tolist()[::-1]
    if destaque in posicao:
        st.markdown(
            f"**{destaque}** está em **{posicao.index(destaque) + 1}º** de {len(posicao)} "
            f"municípios em {definicao.rotulo_curto.lower()} ({ano})."
        )
    if definicao.referencia is not None:
        abaixo = int((ordenado["valor"] < definicao.referencia).sum())
        fig.add_vline(
            x=definicao.referencia,
            line={"color": "#52514e", "width": 1.5},
            annotation_text=f"mínimo legal: {ind.numero(definicao.referencia, 0)}%",
            annotation_position="top",
        )
        st.markdown(
            f"**{abaixo}** de {len(ordenado)} municípios ficaram abaixo do mínimo de "
            f"{ind.numero(definicao.referencia, 0)}% em {ano}, segundo o que declararam ao SIOPE."
        )
    fig.update_layout(bargap=0.25, yaxis={"tickfont": {"size": 10}})
    st.plotly_chart(layout(fig, max(500, 14 * len(ordenado))), use_container_width=True)

# --- evolução ---------------------------------------------------------------------------
with abas[2]:
    escolhidos = st.multiselect(
        "Municípios",
        nomes,
        default=[n for n in ("Palmas", "Araguaína", "Gurupi") if n in nomes],
        max_selections=3,
    )
    cores_series = [SERIE_1, SERIE_2, SERIE_3]
    fig = go.Figure()
    for cor, nome in zip(cores_series, escolhidos, strict=False):
        s = serie[serie["nome_municipio"] == nome].sort_values("ano")
        fig.add_trace(
            go.Scatter(
                x=s["ano"],
                y=s["valor"],
                name=nome,
                mode="lines+markers",
                line={"color": cor, "width": 2},
                marker={"size": 8},
                hovertemplate=nome + " (%{x}): %{y" + definicao.formato_plotly + "}<extra></extra>",
            )
        )
    mediana = serie.groupby("ano")["valor"].median().reset_index()
    fig.add_trace(
        go.Scatter(
            x=mediana["ano"],
            y=mediana["valor"],
            name="Mediana dos municípios",
            mode="lines",
            line={"color": CINZA, "width": 2},
            hovertemplate="Mediana (%{x}): %{y" + definicao.formato_plotly + "}<extra></extra>",
        )
    )
    eixo_x = {"dtick": 2, "tick0": 2005} if definicao.fonte == "ideb" else {"dtick": 1}
    fig.update_layout(hovermode="x unified", xaxis=eixo_x)
    st.plotly_chart(layout(fig), use_container_width=True)

# --- investimento x IDEB ------------------------------------------------------------------
with abas[3]:
    inv = d["investimento"].dropna(subset=["ideb_anos_iniciais", "investimento_por_aluno"])
    anos_inv = sorted(inv["ano"].unique(), reverse=True)
    if anos_inv:
        ano_inv = st.selectbox("Ano (anos com IDEB e despesa)", anos_inv, key="ano_inv")
        base = inv[inv["ano"] == ano_inv]
        destaque_inv = st.selectbox(
            "Destacar município", nomes, index=indice("Palmas"), key="dest_inv"
        )
        fig = go.Figure()
        for nome_grupo, grupo, cor, tamanho in [
            ("Municípios", base[base["nome_municipio"] != destaque_inv], SERIE_1, 9),
            (destaque_inv, base[base["nome_municipio"] == destaque_inv], SERIE_2, 13),
        ]:
            fig.add_trace(
                go.Scatter(
                    x=grupo["investimento_por_aluno"],
                    y=grupo["ideb_anos_iniciais"],
                    mode="markers",
                    name=nome_grupo,
                    text=grupo["nome_municipio"],
                    marker={
                        "color": cor,
                        "size": tamanho,
                        "opacity": 0.85,
                        "line": {"width": 1.5, "color": "white"},
                    },
                    hovertemplate=(
                        "%{text}<br>R$ %{x:,.0f} por aluno<br>IDEB %{y:.1f}<extra></extra>"
                    ),
                )
            )
        # Spearman = Pearson sobre os postos (evita depender do scipy)
        correlacao = base["investimento_por_aluno"].rank().corr(base["ideb_anos_iniciais"].rank())
        fig.update_layout(
            xaxis_title="Investimento por aluno da rede municipal (R$)",
            yaxis_title="IDEB anos iniciais (rede municipal)",
        )
        st.plotly_chart(layout(fig, 520), use_container_width=True)
        st.caption(
            f"Correlação de Spearman em {ano_inv}: {ind.numero(correlacao, 2)} "
            f"({len(base)} municípios). Associação não implica causa: renda, porte e "
            "ruralidade não estão controlados. O investimento é a despesa liquidada na função "
            "Educação dividida pelas matrículas da rede municipal — não é o valor oficial de MDE."
        )

# --- matrículas ---------------------------------------------------------------------------
with abas[4]:
    mat = d["matriculas"]
    ano_mat = st.selectbox("Ano do Censo Escolar", sorted(mat["ano"].unique(), reverse=True))
    escolha_mat = st.selectbox("Município", ["Tocantins (todos)", *nomes])
    base = mat[mat["ano"] == ano_mat]
    if escolha_mat != "Tocantins (todos)":
        base = base[base["nome_municipio"] == escolha_mat]
    por_rede = base.groupby("rede", as_index=False)["matriculas_educacao_basica"].sum()
    ordem = [r for r in CORES_REDE if r in set(por_rede["rede"])]
    total = int(por_rede["matriculas_educacao_basica"].sum())
    fig = go.Figure()
    for r in ordem:
        valor = int(por_rede.loc[por_rede["rede"] == r, "matriculas_educacao_basica"].iloc[0])
        participacao = valor / total if total else 0
        fig.add_trace(
            go.Bar(
                x=[valor],
                y=[""],
                orientation="h",
                name=r.capitalize(),
                marker={"color": CORES_REDE[r], "line": {"width": 2, "color": "white"}},
                hovertemplate=(
                    f"{r.capitalize()}: {ind.numero(valor)} matrículas "
                    f"({ind.numero(100 * participacao, 1)}%)<extra></extra>"
                ),
                # rótulo direto só nos segmentos largos o bastante para lê-lo
                text=[f"{ind.numero(100 * participacao, 0)}%" if participacao >= 0.08 else ""],
                textposition="inside",
                insidetextanchor="middle",
                textfont={"color": "#0b0b0b", "size": 14},
            )
        )
    fig.update_layout(
        barmode="stack",
        yaxis={"visible": False},
        xaxis={"tickformat": ",d"},
    )
    st.subheader(f"Matrículas na educação básica por rede — {escolha_mat}, {ano_mat}")
    st.plotly_chart(layout(fig, 240), use_container_width=True)
    valores = dict(zip(por_rede["rede"], por_rede["matriculas_educacao_basica"], strict=True))
    tabela_redes = [
        {
            "Rede": r.capitalize(),
            "Matrículas": ind.numero(valores[r]),
            "Participação": f"{ind.numero(100 * valores[r] / total, 1)}%",
        }
        for r in ordem
    ] + [{"Rede": "Total", "Matrículas": ind.numero(total), "Participação": "100%"}]
    st.dataframe(tabela_redes, hide_index=True)

# --- comparar dois municípios ------------------------------------------------------------
with abas[5]:
    a, b = st.columns(2)
    m1 = a.selectbox("Município A", nomes, index=indice("Palmas"))
    m2 = b.selectbox("Município B", nomes, index=indice("Araguaína"))
    tabela = ind.comparativo(d, [m1, m2])
    st.dataframe(tabela, use_container_width=True)
    fig = go.Figure()
    for cor, nome in [(SERIE_1, m1), (SERIE_2, m2)]:
        s = serie[serie["nome_municipio"] == nome].sort_values("ano")
        fig.add_trace(
            go.Scatter(
                x=s["ano"],
                y=s["valor"],
                name=nome,
                mode="lines+markers",
                line={"color": cor, "width": 2},
                marker={"size": 8},
            )
        )
    fig.update_layout(title=f"{indicador}: {m1} × {m2}", hovermode="x unified")
    st.plotly_chart(layout(fig), use_container_width=True)

# --- sobre ------------------------------------------------------------------------------
with abas[6]:
    st.markdown(
        """
**Fontes** (detalhes em `docs/fontes.md`): INEP — IDEB por município e microdados do
Censo Escolar; Tesouro Nacional — SICONFI, DCA Anexo I-E (despesa por função);
FNDE — SIOPE (aplicação em MDE e investimento por aluno declarados pelos entes);
IBGE — Divisão Territorial, malha municipal e população (SIDRA).

**Mínimo de 25% em MDE em 2020 e 2021:** a Emenda Constitucional nº 119/2022 afastou a
responsabilização de quem não aplicou o mínimo nesses dois anos, por causa da pandemia,
desde que a diferença fosse compensada até 2023. Por isso o número de municípios abaixo de
25% salta em 2021 (43 de 139) e volta a cair em seguida.

**Duas medidas de investimento por aluno:** a *oficial do SIOPE* (FNDE) é a que o
próprio ente declara, com as regras de Manutenção e Desenvolvimento do Ensino (MDE);
a *aproximação* do projeto divide a despesa liquidada na função Educação (SICONFI) pelas
matrículas da rede municipal. As duas são exibidas para comparação.

**Como ler:** a despesa é a **liquidada** na função 12 – Educação, em reais correntes.
O investimento por aluno usa as matrículas da rede municipal no Censo Escolar do mesmo
ano. Municípios que não declararam o DCA no ano ficam sem valor.
"""
    )
    st.markdown("**Última carga de cada fonte**")
    st.dataframe(d["cargas"], hide_index=True)
