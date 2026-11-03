import json

import duckdb

from pipeline import monitoramento as mon


def test_carga_estavel_sem_achados():
    anterior = {"raw.a": 100, "marts.b": 10}
    atual = {"raw.a": 104, "marts.b": 10}
    assert mon.comparar(atual, anterior) == []


def test_queda_acima_do_limite_e_erro():
    achados = mon.comparar({"raw.a": 90}, {"raw.a": 100})
    assert [(a.nivel, a.tabela) for a in achados] == [("erro", "raw.a")]
    assert achados[0].mensagem == "queda de 10,0%"


def test_crescimento_acima_do_limite_e_erro():
    achados = mon.comparar({"raw.a": 151}, {"raw.a": 100})
    assert achados[0].nivel == "erro"


def test_tabela_sumiu_ou_vazia_e_erro():
    achados = mon.comparar({"raw.b": 0}, {"raw.a": 5, "raw.b": 5})
    assert {(a.tabela, a.mensagem) for a in achados} == {
        ("raw.a", "tabela sumiu"),
        ("raw.b", "tabela ficou vazia"),
    }


def test_tabela_nova_e_aviso_e_controle_e_ignorado():
    achados = mon.comparar(
        {"raw.a": 1, "raw.nova": 3, "raw._cargas": 99}, {"raw.a": 1, "raw._cargas": 4}
    )
    assert [(a.nivel, a.tabela) for a in achados] == [("aviso", "raw.nova")]


def test_falhas_de_extracao_viram_aviso(tmp_path):
    banco = tmp_path / "b.duckdb"
    with duckdb.connect(str(banco)) as con:
        con.execute("create schema raw")
        con.execute(
            "create table raw._cargas (extrator varchar, iniciado_em timestamptz, "
            "finalizado_em timestamptz, sucesso boolean, linhas integer, erro varchar)"
        )
        con.execute(
            "insert into raw._cargas values "
            "('inep', now() - interval 2 day, now() - interval 2 day, true, 10, null), "
            "('inep', now(), now(), false, 0, 'timeout'), "
            "('ibge', now() - interval 1 day, now() - interval 1 day, false, 0, 'x'), "
            "('ibge', now(), now(), true, 5, null)"
        )
    achados = mon.falhas_de_extracao(banco)
    assert [(a.nivel, a.tabela) for a in achados] == [("aviso", "extrator inep")]


def _escrever(caminho, tabelas):
    caminho.write_text(json.dumps({"gerado_em": "2026-11-03T00:00:00+00:00", "tabelas": tabelas}))


def test_main_retorna_1_com_erro_e_grava_resumo_e_historico(tmp_path):
    atual, anterior = tmp_path / "a.json", tmp_path / "b.json"
    _escrever(atual, {"raw.a": 10})
    _escrever(anterior, {"raw.a": 100})
    resumo, historico = tmp_path / "resumo.md", tmp_path / "h" / "historico.jsonl"
    codigo = mon.main(
        [
            str(atual),
            "--anterior",
            str(anterior),
            "--resumo",
            str(resumo),
            "--historico",
            str(historico),
        ]
    )
    assert codigo == 1
    assert "Anomalias" in resumo.read_text()
    registro = json.loads(historico.read_text().splitlines()[0])
    assert registro["erros"] == 1


def test_main_sem_carga_anterior_passa(tmp_path):
    atual = tmp_path / "a.json"
    _escrever(atual, {"raw.a": 10})
    assert mon.main([str(atual), "--anterior", str(tmp_path / "nao_existe.json")]) == 0
