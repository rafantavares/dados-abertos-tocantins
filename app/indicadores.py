"""Definição dos indicadores do painel e formatação em português (pt-BR).

Separado da interface para poder ser testado sem o Streamlit.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

ETAPAS = {
    "anos_iniciais": "Anos iniciais (1º ao 5º)",
    "anos_finais": "Anos finais (6º ao 9º)",
    "ensino_medio": "Ensino médio",
}
REDES = {"publica": "Pública (todas)", "municipal": "Municipal", "estadual": "Estadual"}


def ausente(valor) -> bool:
    """Verdadeiro para None, NaN e pd.NA."""
    try:
        return bool(pd.isna(valor))
    except (TypeError, ValueError):
        return False


def numero(valor: float | None, casas: int = 0) -> str:
    """Formata no padrão brasileiro: 1.234.567,89."""
    if ausente(valor):
        return "—"
    valor = float(valor)
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def reais(valor: float | None, curto: bool = False) -> str:
    if ausente(valor):
        return "—"
    valor = float(valor)
    if curto:
        for limite, sufixo in ((1e9, "bi"), (1e6, "mi"), (1e3, "mil")):
            if abs(valor) >= limite:
                return f"R$ {numero(valor / limite, 1)} {sufixo}"
    return f"R$ {numero(valor, 2)}"


@dataclass(frozen=True)
class Indicador:
    fonte: str
    coluna: str
    rotulo_curto: str
    formato_plotly: str
    formato_hover: str
    formatar: Callable[[float | None], str]
    #: Valor de referência legal, desenhado como linha no ranking (ex.: 25% de MDE).
    referencia: float | None = None
    #: Coluna com o valor corrigido pelo IPCA (só para indicadores em reais).
    coluna_real: str | None = None


INDICADORES: dict[str, Indicador] = {
    "IDEB": Indicador("ideb", "ideb", "IDEB", ":.1f", ":.1f", lambda v: numero(v, 1)),
    "Investimento por aluno (rede municipal)": Indicador(
        "investimento",
        "investimento_por_aluno",
        "Investimento por aluno",
        ":,.0f",
        ":,.0f",
        reais,
        coluna_real="investimento_por_aluno_real",
    ),
    "Aplicação em MDE – oficial SIOPE (% das receitas de impostos; mínimo 25%)": Indicador(
        "siope",
        "percentual_mde",
        "Aplicação em MDE (%)",
        ":.1f",
        ":.1f",
        lambda v: f"{numero(v, 1)}%",
        referencia=25.0,
    ),
    "Investimento por aluno da educação básica – oficial SIOPE": Indicador(
        "siope",
        "investimento_por_aluno_educacao_basica",
        "Investimento por aluno (SIOPE)",
        ":,.0f",
        ":,.0f",
        reais,
        coluna_real="investimento_por_aluno_educacao_basica_real",
    ),
    "Despesa em Educação por habitante": Indicador(
        "despesa",
        "despesa_educacao_per_capita",
        "Despesa por habitante",
        ":,.0f",
        ":,.0f",
        reais,
        coluna_real="despesa_educacao_per_capita_real",
    ),
    "Parcela da despesa total destinada à Educação (%)": Indicador(
        "despesa",
        "percentual_educacao",
        "Parcela da despesa (%)",
        ":.1f",
        ":.1f",
        lambda v: f"{numero(v, 1)}%",
    ),
}


def corrigivel(definicao: Indicador, base: pd.DataFrame) -> bool:
    """Verdadeiro se o indicador tem versão corrigida pelo IPCA neste banco."""
    return definicao.coluna_real is not None and definicao.coluna_real in base.columns


def serie(
    d: dict[str, pd.DataFrame],
    nome: str,
    etapa: str | None = None,
    rede: str | None = None,
    valores_reais: bool = False,
) -> pd.DataFrame:
    """Série (cod_municipio, nome_municipio, ano, valor) do indicador escolhido.

    Com ``valores_reais``, usa a coluna corrigida pelo IPCA quando ela existe
    (bancos antigos não a têm; aí o valor corrente é mantido).
    """
    definicao = INDICADORES[nome]
    base = d[definicao.fonte]
    if definicao.fonte == "ideb":
        base = base[(base["etapa"] == etapa) & (base["rede"] == rede)]
    coluna = (
        definicao.coluna_real if valores_reais and corrigivel(definicao, base) else definicao.coluna
    )
    resultado = base[["cod_municipio", "nome_municipio", "ano", coluna]].rename(
        columns={coluna: "valor"}
    )
    resultado = resultado.dropna(subset=["valor"])
    resultado["valor"] = resultado["valor"].astype(float)
    return resultado.reset_index(drop=True)


def comparativo(d: dict[str, pd.DataFrame], nomes: list[str]) -> pd.DataFrame:
    """Tabela lado a lado com o valor mais recente de cada indicador."""
    linhas = {}
    pop = d["municipios"].set_index("nome_municipio")["populacao_censo_2022"]
    linhas["População (Censo 2022)"] = {n: numero(pop.get(n)) for n in nomes}
    for etapa, rotulo in ETAPAS.items():
        s = serie(d, "IDEB", etapa=etapa, rede="publica")
        linhas[f"IDEB {rotulo} – rede pública"] = _mais_recente(s, nomes, lambda v: numero(v, 1))
    for nome, definicao in INDICADORES.items():
        if definicao.fonte != "ideb" and definicao.fonte in d:
            linhas[nome] = _mais_recente(serie(d, nome), nomes, definicao.formatar)
    return pd.DataFrame(linhas).T[nomes]


def _mais_recente(s: pd.DataFrame, nomes: list[str], formatar) -> dict[str, str]:
    saida = {}
    for n in nomes:
        linhas = s[s["nome_municipio"] == n].sort_values("ano")
        if linhas.empty:
            saida[n] = "—"
        else:
            ultimo = linhas.iloc[-1]
            saida[n] = f"{formatar(ultimo['valor'])} ({int(ultimo['ano'])})"
    return saida


#: Anos em que a EC 119/2022 afastou a responsabilização pelo mínimo de 25% em MDE.
ANOS_EC_119 = (2020, 2021)
NOTA_EC_119 = (
    "**Contexto legal ({ano}):** a Emenda Constitucional nº 119/2022 afastou a "
    "responsabilização de estados, municípios e agentes públicos que, por causa da "
    "pandemia de covid-19, não aplicaram o mínimo de 25% em MDE em 2020 e 2021. A "
    "diferença deveria ser compensada até o exercício de 2023. Os percentuais abaixo "
    "de 25% neste ano não indicam, por si só, irregularidade."
)


def nota_contexto(definicao: Indicador, ano: int) -> str | None:
    """Nota explicativa a exibir junto do indicador naquele ano, se houver."""
    if definicao.coluna == "percentual_mde" and int(ano) in ANOS_EC_119:
        return NOTA_EC_119.format(ano=ano)
    return None
