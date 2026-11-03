"""Cores do painel para os modos claro e escuro.

Valores da paleta de referência de visualização (categórica em ordem fixa,
sequencial azul, tinta e linhas de grade por modo). As quatro cores das redes
foram validadas nos dois modos com o validador de paletas (faixa de
luminosidade, croma, separação para daltonismo e contraste com o fundo):

- claro, fundo #fcfcfb: tudo passa; verde-água e amarelo ficam abaixo de 3:1
  de contraste, compensados por rótulos diretos e tabela no gráfico de matrículas;
- escuro, fundo #1a1a19: tudo passa, inclusive contraste >= 3:1.

O modo escuro não é uma inversão automática: cada cor tem o seu passo próprio
na mesma rampa, e a escala sequencial inverte a âncora (valores baixos se
aproximam do fundo escuro, valores altos ficam claros).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tema:
    nome: str
    #: Categóricas em ordem fixa: slots 1 a 4 (azul, laranja, verde-água, amarelo).
    serie: tuple[str, str, str, str]
    #: Rampa sequencial do menor para o maior valor (mapa).
    sequencial: tuple[str, ...]
    #: Linha de referência neutra (mediana, mínimo legal).
    neutro: str
    texto: str
    texto_secundario: str
    grade: str
    eixo: str
    superficie: str
    #: Texto escrito dentro de barras coloridas (usar grande e em negrito: o azul
    #: do modo claro tem 4,46:1 com preto, abaixo dos 4,5:1 de texto normal).
    rotulo_em_preenchimento: str

    @property
    def cores_rede(self) -> dict[str, str]:
        return dict(zip(("federal", "estadual", "municipal", "privada"), self.serie, strict=True))


CLARO = Tema(
    nome="claro",
    serie=("#2a78d6", "#eb6834", "#1baf7a", "#eda100"),
    sequencial=("#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"),
    neutro="#898781",
    texto="#0b0b0b",
    texto_secundario="#52514e",
    grade="#e1e0d9",
    eixo="#c3c2b7",
    superficie="#fcfcfb",
    rotulo_em_preenchimento="#0b0b0b",
)

ESCURO = Tema(
    nome="escuro",
    serie=("#3987e5", "#d95926", "#199e70", "#c98500"),
    # âncora invertida: o menor valor fica perto do fundo escuro
    sequencial=("#104281", "#184f95", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4", "#cde2fb"),
    neutro="#898781",
    texto="#f0efec",
    texto_secundario="#c3c2b7",
    grade="#2c2c2a",
    eixo="#383835",
    superficie="#1a1a19",
    rotulo_em_preenchimento="#0b0b0b",
)


def para(tipo: str | None) -> Tema:
    """Tema para o tipo informado pelo Streamlit (``"dark"``/``"light"``; padrão claro)."""
    return ESCURO if tipo == "dark" else CLARO
