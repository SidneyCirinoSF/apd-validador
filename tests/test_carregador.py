"""Testes do carregador: JSON (a 7-tupla M = (Q, Σ, Γ, δ, q0, Z0, F) serializada) → APD.

Os JSON de teste são criados em pastas temporárias, para não depender dos
arquivos reais de ``automatos/`` (que só são usados no último teste, se existirem).
"""

import codecs
import copy
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from apd.automato import APD
from apd.carregador import carregar_apd, listar_automatos
from apd.modelos import DefinicaoInvalidaError, Transicao

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
PASTA_AUTOMATOS = RAIZ_PROJETO / "automatos"

_DEFINICAO_MINIMA = {
    "nome": "mínimo",
    "estados": ["q0", "q1", "qf"],
    "alfabeto_entrada": ["a", "b", "$"],
    "alfabeto_pilha": ["Z0", "A"],
    "estado_inicial": "q0",
    "simbolo_inicial_pilha": "Z0",
    "estados_finais": ["qf"],
    "transicoes": [
        {"origem": "q0", "le": "a", "topo": "Z0", "destino": "q1", "empilha": ["A", "Z0"]},
        {"origem": "q1", "le": None, "topo": "A", "destino": "q0", "empilha": ["A"]},
        {"origem": "q0", "le": "b", "topo": "A", "destino": "q0", "empilha": []},
        {"origem": "q0", "le": "$", "topo": "Z0", "destino": "qf", "empilha": ["Z0"]},
    ],
}


def definicao_minima() -> dict:
    """Cópia nova de um JSON válido (aceita a^n b^n com n ≤ 1, com uma ε-transição)."""
    return copy.deepcopy(_DEFINICAO_MINIMA)


class TestCarregarApd(unittest.TestCase):
    """``carregar_apd``: conversão para o APD e erros transformados em DefinicaoInvalidaError."""

    def setUp(self) -> None:
        self._temporaria = tempfile.TemporaryDirectory()
        self.pasta = Path(self._temporaria.name)

    def tearDown(self) -> None:
        self._temporaria.cleanup()

    def escrever(self, dados: object, nome: str = "teste.json") -> Path:
        """Grava ``dados`` como JSON (UTF-8) na pasta temporária."""
        caminho = self.pasta / nome
        caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
        return caminho

    def assert_invalido(self, caminho: Path, *trechos: str) -> DefinicaoInvalidaError:
        """Confere que o carregamento falha citando o arquivo e cada trecho dado."""
        with self.assertRaises(DefinicaoInvalidaError) as contexto:
            carregar_apd(caminho)
        mensagem = str(contexto.exception)
        self.assertIn(caminho.name, mensagem)
        for trecho in trechos:
            self.assertIn(trecho, mensagem)
        return contexto.exception

    # Casos mínimos da issue #2 -------------------------------------------------

    def test_json_valido_minimo(self) -> None:
        apd = carregar_apd(self.escrever(definicao_minima()))

        self.assertIsInstance(apd, APD)
        self.assertEqual(apd.nome, "mínimo")
        self.assertEqual(apd.estados, {"q0", "q1", "qf"})
        self.assertEqual(apd.alfabeto_entrada, {"a", "b", "$"})
        self.assertEqual(apd.alfabeto_pilha, {"Z0", "A"})
        self.assertEqual(apd.estado_inicial, "q0")
        self.assertEqual(apd.simbolo_inicial_pilha, "Z0")
        self.assertEqual(apd.estados_finais, {"qf"})

        transicoes = apd.tabela_transicoes()
        self.assertEqual(len(transicoes), 4)
        # "le": null vira None (ε) e "empilha" vira tupla.
        self.assertEqual(transicoes[1], Transicao("q1", None, "A", "q0", ("A",)))
        self.assertEqual(apd.transicao("q1", None, "A"), transicoes[1])
        for transicao in transicoes:
            self.assertIsInstance(transicao.empilha, tuple)
        self.assertEqual(transicoes[2].empilha, ())

    def test_arquivo_inexistente(self) -> None:
        self.assert_invalido(self.pasta / "nao_existe.json", "não encontrado")

    def test_json_malformado(self) -> None:
        caminho = self.pasta / "quebrado.json"
        caminho.write_text('{ "nome": ', encoding="utf-8")
        erro = self.assert_invalido(caminho, "JSON malformado")
        self.assertIsInstance(erro.__cause__, json.JSONDecodeError)

    def test_campo_obrigatorio_ausente(self) -> None:
        dados = definicao_minima()
        del dados["transicoes"]
        self.assert_invalido(self.escrever(dados), "transicoes")

    def test_json_nao_deterministico(self) -> None:
        dados = definicao_minima()
        # Mesma chave (q0, a, Z0) que a primeira transição.
        dados["transicoes"].append(
            {"origem": "q0", "le": "a", "topo": "Z0", "destino": "qf", "empilha": ["Z0"]}
        )
        erro = self.assert_invalido(
            self.escrever(dados, "nao_det.json"), "Não determinismo"
        )
        # O erro formal vindo do APD é reembrulhado, preservando a causa.
        self.assertIsInstance(erro.__cause__, DefinicaoInvalidaError)

    # Opcionais ---------------------------------------------------------------

    def test_descricao_e_tokenizador_padrao(self) -> None:
        apd = carregar_apd(self.escrever(definicao_minima()))
        self.assertEqual(apd.descricao, "")
        self.assertEqual(apd.tokenizador, "xml")
        self.assertEqual(apd.rotulos_pilha, {})

    def test_opcionais_carregados(self) -> None:
        dados = definicao_minima()
        dados["descricao"] = "Teste de opcionais."
        dados["tokenizador"] = "expressao"
        dados["rotulos_pilha"] = {"Z0": "fundo da pilha", "A": "a"}
        apd = carregar_apd(self.escrever(dados))
        self.assertEqual(apd.descricao, "Teste de opcionais.")
        self.assertEqual(apd.tokenizador, "expressao")
        self.assertEqual(apd.rotulos_pilha, {"Z0": "fundo da pilha", "A": "a"})

    # Erros de forma ------------------------------------------------------------

    def test_tokenizador_invalido(self) -> None:
        dados = definicao_minima()
        dados["tokenizador"] = "html"
        self.assert_invalido(self.escrever(dados), "tokenizador", "html")

    def test_empilha_nao_e_lista(self) -> None:
        dados = definicao_minima()
        dados["transicoes"][2]["empilha"] = "A"
        self.assert_invalido(self.escrever(dados), "transicoes[2]", "empilha", "lista")

    def test_transicao_sem_chave(self) -> None:
        dados = definicao_minima()
        del dados["transicoes"][3]["destino"]
        self.assert_invalido(self.escrever(dados), "transicoes[3]", "destino")

    def test_le_com_tipo_errado(self) -> None:
        dados = definicao_minima()
        dados["transicoes"][0]["le"] = 7
        self.assert_invalido(self.escrever(dados), "transicoes[0]", "le")

    def test_conjunto_que_nao_e_lista_de_strings(self) -> None:
        dados = definicao_minima()
        dados["estados"] = ["q0", 1, "qf"]
        self.assert_invalido(self.escrever(dados), "estados")

    def test_rotulos_pilha_com_tipo_errado(self) -> None:
        dados = definicao_minima()
        dados["rotulos_pilha"] = {"A": 1}
        self.assert_invalido(self.escrever(dados), "rotulos_pilha")

    def test_rotulos_pilha_com_simbolo_fora_de_gama(self) -> None:
        dados = definicao_minima()
        dados["rotulos_pilha"] = {"Z0": "fundo", "B": "b"}  # B ∉ Γ
        self.assert_invalido(self.escrever(dados), "rotulos_pilha", "'B'", "Γ")

    def test_tokenizador_null_mostra_null(self) -> None:
        dados = definicao_minima()
        dados["tokenizador"] = None
        erro = self.assert_invalido(self.escrever(dados), "tokenizador", "null")
        self.assertNotIn("None", str(erro))

    def test_raiz_que_nao_e_objeto(self) -> None:
        self.assert_invalido(self.escrever([1, 2, 3]), "objeto")

    def test_simbolo_fora_do_alfabeto_cita_arquivo(self) -> None:
        dados = definicao_minima()
        dados["transicoes"][0]["le"] = "c"  # c ∉ Σ: erro formal detectado pelo APD
        self.assert_invalido(self.escrever(dados, "fora_de_sigma.json"))

    # Leitura do arquivo ----------------------------------------------------------

    def test_arquivo_com_bom_carrega_normalmente(self) -> None:
        caminho = self.pasta / "com_bom.json"
        texto = json.dumps(definicao_minima(), ensure_ascii=False)
        caminho.write_bytes(codecs.BOM_UTF8 + texto.encode("utf-8"))
        apd = carregar_apd(caminho)
        self.assertEqual(apd.nome, "mínimo")
        self.assertEqual(len(apd.tabela_transicoes()), 4)

    def test_chave_duplicada(self) -> None:
        caminho = self.pasta / "duplicada.json"
        texto = json.dumps(definicao_minima(), ensure_ascii=False)
        # Repete "le" na primeira transição: {..., "le": "a", "le": null, ...}
        texto = texto.replace('"le": "a"', '"le": "a", "le": null', 1)
        caminho.write_text(texto, encoding="utf-8")
        self.assert_invalido(caminho, "'le'", "repetida")

    def test_inteiro_gigante(self) -> None:
        caminho = self.pasta / "inteiro_gigante.json"
        caminho.write_text('{"nome": ' + "9" * 5000 + "}", encoding="utf-8")
        erro = self.assert_invalido(caminho)
        self.assertIsInstance(erro.__cause__, ValueError)

    def test_aninhamento_profundo(self) -> None:
        caminho = self.pasta / "profundo.json"
        caminho.write_text("[" * 100_000 + "]" * 100_000, encoding="utf-8")
        erro = self.assert_invalido(caminho, "aninhado")
        self.assertIsInstance(erro.__cause__, RecursionError)

    def test_arquivo_que_nao_e_utf8(self) -> None:
        caminho = self.pasta / "latin1.json"
        # "í" em Latin-1 é o byte 0xED, que não forma UTF-8 válido aqui.
        caminho.write_bytes('{"nome": "mínimo"}'.encode("latin-1"))
        erro = self.assert_invalido(caminho, "UTF-8")
        self.assertIsInstance(erro.__cause__, UnicodeDecodeError)

    def test_caminho_que_e_diretorio(self) -> None:
        diretorio = self.pasta / "sou_pasta.json"
        diretorio.mkdir()
        erro = self.assert_invalido(diretorio, "não pôde ser lido")
        self.assertIsInstance(erro.__cause__, OSError)


class TestListarAutomatos(unittest.TestCase):
    """``listar_automatos``: só os .json, em ordem alfabética."""

    def test_lista_so_json_ordenados(self) -> None:
        with tempfile.TemporaryDirectory() as nome_pasta:
            pasta = Path(nome_pasta)
            for nome in ("b.json", "a.json", "notas.txt", "c.json.bak"):
                (pasta / nome).write_text("{}", encoding="utf-8")
            self.assertEqual(
                listar_automatos(pasta), [pasta / "a.json", pasta / "b.json"]
            )

    def test_pasta_inexistente(self) -> None:
        with tempfile.TemporaryDirectory() as nome_pasta:
            self.assertEqual(listar_automatos(Path(nome_pasta) / "nao_existe"), [])
        self.assertEqual(listar_automatos("pasta_que_nao_existe_em_lugar_algum"), [])

    def test_fallback_para_raiz_do_projeto(self) -> None:
        # Pasta com .json dentro de tests/, criada só durante o teste.
        pasta_real = Path(
            tempfile.mkdtemp(prefix="_tmp_listar_", dir=RAIZ_PROJETO / "tests")
        )
        self.addCleanup(shutil.rmtree, pasta_real, ignore_errors=True)
        for nome in ("b.json", "a.json"):
            (pasta_real / nome).write_text("{}", encoding="utf-8")
        relativa = Path("tests") / pasta_real.name

        # Diretório atual numa pasta temporária, onde a pasta relativa não existe.
        with tempfile.TemporaryDirectory() as outra_pasta:
            diretorio_original = os.getcwd()
            os.chdir(outra_pasta)
            try:
                self.assertFalse(relativa.is_dir())
                encontrados = listar_automatos(relativa)
            finally:
                os.chdir(diretorio_original)

        self.assertEqual([caminho.name for caminho in encontrados], ["a.json", "b.json"])
        for caminho in encontrados:
            self.assertTrue(caminho.is_file())


@unittest.skipUnless((PASTA_AUTOMATOS / "xml_tags.json").exists(), "aguardando #3")
class TestAutomatosReais(unittest.TestCase):
    """Carrega os dois JSON reais gerados no #3."""

    def test_carrega_xml_e_expressoes(self) -> None:
        xml = carregar_apd(PASTA_AUTOMATOS / "xml_tags.json")
        expressoes = carregar_apd(PASTA_AUTOMATOS / "expressoes.json")
        self.assertEqual(len(xml.tabela_transicoes()), 56)
        self.assertEqual(len(expressoes.tabela_transicoes()), 20)
        self.assertEqual(xml.tokenizador, "xml")
        self.assertEqual(expressoes.tokenizador, "expressao")


if __name__ == "__main__":
    unittest.main()
