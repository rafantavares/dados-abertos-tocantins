"""Cliente HTTP com timeout, retry exponencial e cache em disco.

- **Retry**: erros de rede e status 429/5xx são repetidos com espera
  exponencial; demais status falham na hora.
- **Cache**: um arquivo já baixado (identificado pela URL) não é baixado de
  novo, a menos que ``forcar=True``. Isso torna os extratores idempotentes e
  baratos de rodar várias vezes.
- **TLS**: alguns servidores do governo (ex.: ``download.inep.gov.br``) não
  enviam o certificado intermediário. Nesse caso completamos a cadeia buscando
  o emissor indicado no campo AIA do certificado — a verificação continua ativa.
"""

from __future__ import annotations

import hashlib
import logging
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path

import httpx

log = logging.getLogger(__name__)

USER_AGENT = (
    "dados-abertos-tocantins/0.1 (+https://github.com/rafantavares/dados-abertos-tocantins)"
)
STATUS_RETENTAVEIS = {429, 500, 502, 503, 504}

#: Contextos TLS com cadeia completada, por host.
_CONTEXTOS: dict[str, ssl.SSLContext] = {}


class ErroDownload(RuntimeError):
    """Falha definitiva ao baixar uma URL."""


def contexto_com_intermediario(host: str) -> ssl.SSLContext:
    """Cria um contexto TLS que confia também no emissor intermediário do ``host``."""
    from cryptography import x509
    from cryptography.hazmat.primitives.serialization import Encoding
    from cryptography.x509.oid import AuthorityInformationAccessOID, ExtensionOID

    pem = ssl.get_server_certificate((host, 443), timeout=30)
    cert = x509.load_pem_x509_certificate(pem.encode())
    aia = cert.extensions.get_extension_for_oid(ExtensionOID.AUTHORITY_INFORMATION_ACCESS)
    contexto = ssl.create_default_context()
    for desc in aia.value:
        if desc.access_method != AuthorityInformationAccessOID.CA_ISSUERS:
            continue
        with urllib.request.urlopen(desc.access_location.value, timeout=30) as resp:
            dados = resp.read()
        try:
            emissor = x509.load_der_x509_certificate(dados)
        except ValueError:
            emissor = x509.load_pem_x509_certificate(dados)
        contexto.load_verify_locations(cadata=emissor.public_bytes(Encoding.PEM).decode())
    return contexto


def _erro_certificado(erro: Exception) -> bool:
    atual: BaseException | None = erro
    while atual is not None:
        if isinstance(atual, ssl.SSLCertVerificationError):
            return True
        atual = atual.__cause__ or atual.__context__
    return False


def _novo_cliente(timeout: float, verify: ssl.SSLContext | bool = True) -> httpx.Client:
    return httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
        verify=verify,
    )


def baixar(
    url: str,
    *,
    tentativas: int = 4,
    timeout: float = 120.0,
    espera_base: float = 2.0,
    cliente: httpx.Client | None = None,
) -> bytes:
    """Baixa ``url`` com retry exponencial para erros de rede e status 429/5xx."""
    host = urllib.parse.urlsplit(url).hostname or ""
    proprio = cliente is None
    if cliente is None:
        cliente = _novo_cliente(timeout, _CONTEXTOS.get(host, True))
    try:
        for tentativa in range(1, tentativas + 1):
            try:
                resp = cliente.get(url)
                if resp.status_code in STATUS_RETENTAVEIS:
                    raise httpx.HTTPStatusError(
                        f"status {resp.status_code}", request=resp.request, response=resp
                    )
                resp.raise_for_status()
                return resp.content
            except httpx.ConnectError as erro:
                if proprio and host not in _CONTEXTOS and _erro_certificado(erro):
                    log.warning("%s não enviou a cadeia TLS completa; buscando emissor (AIA)", host)
                    _CONTEXTOS[host] = contexto_com_intermediario(host)
                    cliente.close()
                    cliente = _novo_cliente(timeout, _CONTEXTOS[host])
                    continue
                _esperar_ou_falhar(url, erro, tentativa, tentativas, espera_base)
            except (httpx.TransportError, httpx.HTTPStatusError) as erro:
                if (
                    isinstance(erro, httpx.HTTPStatusError)
                    and erro.response.status_code not in STATUS_RETENTAVEIS
                ):
                    raise ErroDownload(f"{url}: {erro}") from erro
                _esperar_ou_falhar(url, erro, tentativa, tentativas, espera_base)
    finally:
        if proprio:
            cliente.close()
    raise ErroDownload(f"{url}: tentativas esgotadas")


def _esperar_ou_falhar(
    url: str, erro: Exception, tentativa: int, tentativas: int, espera_base: float
) -> None:
    if tentativa >= tentativas:
        raise ErroDownload(f"{url}: {erro}") from erro
    espera = espera_base * 2 ** (tentativa - 1)
    log.warning("tentativa %d falhou (%s); nova tentativa em %.0fs", tentativa, erro, espera)
    time.sleep(espera)


def baixar_com_cache(url: str, pasta_cache: Path, *, forcar: bool = False, **kwargs) -> bytes:
    """Como :func:`baixar`, mas reaproveita o arquivo salvo em ``pasta_cache``."""
    pasta_cache.mkdir(parents=True, exist_ok=True)
    arquivo = pasta_cache / hashlib.sha256(url.encode()).hexdigest()[:24]
    if arquivo.exists() and not forcar:
        log.info("cache: %s", url)
        return arquivo.read_bytes()
    conteudo = baixar(url, **kwargs)
    temporario = arquivo.with_suffix(".tmp")
    temporario.write_bytes(conteudo)
    temporario.replace(arquivo)
    return conteudo
