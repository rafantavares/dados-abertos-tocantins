import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

import tema


def _luminancia(hexa: str) -> float:
    canais = [int(hexa[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lineares = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in canais]
    return 0.2126 * lineares[0] + 0.7152 * lineares[1] + 0.0722 * lineares[2]


def _contraste(a: str, b: str) -> float:
    claro, escuro = sorted((_luminancia(a), _luminancia(b)), reverse=True)
    return (claro + 0.05) / (escuro + 0.05)


def test_para_escolhe_tema_e_padrao_claro():
    assert tema.para("dark") is tema.ESCURO
    assert tema.para("light") is tema.CLARO
    assert tema.para(None) is tema.CLARO


def test_rampa_sequencial_inverte_a_ancora_no_escuro():
    claro = [_luminancia(c) for c in tema.CLARO.sequencial]
    escuro = [_luminancia(c) for c in tema.ESCURO.sequencial]
    assert claro == sorted(claro, reverse=True)  # maior valor = mais escuro sobre fundo claro
    assert escuro == sorted(escuro)  # maior valor = mais claro sobre fundo escuro


def test_cores_das_redes_seguem_a_ordem_fixa():
    for t in (tema.CLARO, tema.ESCURO):
        assert list(t.cores_rede) == ["federal", "estadual", "municipal", "privada"]
        assert list(t.cores_rede.values()) == list(t.serie)


def test_series_do_escuro_tem_contraste_minimo_com_o_fundo():
    for cor in tema.ESCURO.serie:
        assert _contraste(cor, tema.ESCURO.superficie) >= 3


def test_rotulo_dentro_das_barras_e_legivel():
    # O painel escreve esses rótulos com 19 px em negrito ("texto grande" na WCAG,
    # mínimo 3:1). Com texto normal (4,5:1) o azul do modo claro não passaria:
    # 4,46:1 com preto e 4,42:1 com branco.
    for t in (tema.CLARO, tema.ESCURO):
        for cor in t.serie:
            assert _contraste(t.rotulo_em_preenchimento, cor) >= 3
