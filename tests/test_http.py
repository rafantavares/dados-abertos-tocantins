import httpx
import pytest

from pipeline import http


def _cliente(respostas):
    """Cliente httpx falso que devolve as respostas em sequência."""
    fila = list(respostas)
    chamadas = []

    def handler(request):
        chamadas.append(str(request.url))
        item = fila.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    return httpx.Client(transport=httpx.MockTransport(handler)), chamadas


def test_baixar_sucesso():
    cliente, chamadas = _cliente([httpx.Response(200, content=b"ok")])
    assert http.baixar("https://x/a", cliente=cliente) == b"ok"
    assert len(chamadas) == 1


def test_baixar_repete_em_5xx_e_erro_de_rede():
    cliente, chamadas = _cliente(
        [
            httpx.Response(503),
            httpx.ReadTimeout("lento"),
            httpx.Response(200, content=b"ok"),
        ]
    )
    assert http.baixar("https://x/a", cliente=cliente, espera_base=0) == b"ok"
    assert len(chamadas) == 3


def test_baixar_nao_repete_404():
    cliente, chamadas = _cliente([httpx.Response(404)])
    with pytest.raises(http.ErroDownload):
        http.baixar("https://x/a", cliente=cliente, espera_base=0)
    assert len(chamadas) == 1


def test_baixar_desiste_apos_tentativas():
    cliente, chamadas = _cliente([httpx.Response(500)] * 3)
    with pytest.raises(http.ErroDownload):
        http.baixar("https://x/a", cliente=cliente, tentativas=3, espera_base=0)
    assert len(chamadas) == 3


def test_baixar_com_cache_e_idempotente(monkeypatch, tmp_path):
    chamadas = []

    def falso(url, **kwargs):
        chamadas.append(url)
        return b"conteudo"

    monkeypatch.setattr(http, "baixar", falso)
    assert http.baixar_com_cache("https://x/a", tmp_path) == b"conteudo"
    assert http.baixar_com_cache("https://x/a", tmp_path) == b"conteudo"
    assert chamadas == ["https://x/a"]
    http.baixar_com_cache("https://x/a", tmp_path, forcar=True)
    assert len(chamadas) == 2
