"""Testes do analisador léxico (apd/tokenizador.py).

Verificam a conversão de textos XML/HTML e de expressões balanceadas em fitas
de ``Token`` terminadas por ``MARCADOR_FIM`` ("$"), conferindo símbolos, lexemas,
contagem exata de linhas e colunas (inclusive com ``\\r\\n`` e tabulações) e o
levantamento de ``ErroLexico`` com posição precisa.
"""

import inspect
import unittest

from apd.automato import APD
from apd.modelos import MARCADOR_FIM, ErroLexico, Token, Transicao
from apd.tokenizador import tokenizar, tokenizar_expressao, tokenizar_xml


def simbolos(tokens: list[Token]) -> list[str]:
    """Extrai apenas a sequência de símbolos de Σ da fita de tokens."""
    return [t.simbolo for t in tokens]


def posicoes(tokens: list[Token]) -> list[tuple[str, int, int]]:
    """Extrai ``(simbolo, linha, coluna)`` de cada token da fita."""
    return [(t.simbolo, t.linha, t.coluna) for t in tokens]


class TestTokenizarXmlBasico(unittest.TestCase):
    """Casos estruturais de tags, texto e marcador de fim em XML."""

    def test_texto_vazio_gera_apenas_marcador_fim(self):
        self.assertEqual(tokenizar_xml(""), [Token(MARCADOR_FIM, "", 1, 1)])

    def test_abertura_e_fechamento_simples(self):
        fita = tokenizar_xml("<div></div>")
        self.assertEqual(simbolos(fita), ["<div>", "</div>", "$"])
        self.assertEqual(
            posicoes(fita),
            [("<div>", 1, 1), ("</div>", 1, 6), ("$", 1, 12)],
        )

    def test_exemplo_completo_com_lexemas_e_posicoes_da_especificacao(self):
        fita = tokenizar_xml("<div><p>Olá</p></div>")
        self.assertEqual(
            fita,
            [
                Token("<div>", "<div>", 1, 1),
                Token("<p>", "<p>", 1, 6),
                Token("#texto", "Olá", 1, 9),
                Token("</p>", "</p>", 1, 12),
                Token("</div>", "</div>", 1, 16),
                Token("$", "", 1, 22),
            ],
        )

    def test_exemplo_multilinha_com_posicoes_exatas(self):
        entrada = (
            "<html>\n"
            "  <body>\n"
            '    <p class="x">Olá mundo</p>\n'
            "  </body>\n"
            "</html>"
        )
        fita = tokenizar_xml(entrada)
        self.assertEqual(
            posicoes(fita),
            [
                ("<html>", 1, 1),
                ("<body>", 2, 3),
                ("<p>", 3, 5),
                ("#texto", 3, 18),
                ("</p>", 3, 27),
                ("</body>", 4, 3),
                ("</html>", 5, 1),
                ("$", 5, 8),
            ],
        )
        self.assertEqual(fita[2].lexema, '<p class="x">')
        self.assertEqual(fita[3].lexema, "Olá mundo")

    def test_quebras_crlf_e_cr_produzem_mesmas_posicoes_que_lf(self):
        entrada_lf = (
            "<html>\n"
            "  <body>\n"
            '    <p class="x">Olá mundo</p>\n'
            "  </body>\n"
            "</html>"
        )
        entrada_crlf = entrada_lf.replace("\n", "\r\n")
        entrada_cr = entrada_lf.replace("\n", "\r")
        self.assertEqual(posicoes(tokenizar_xml(entrada_crlf)), posicoes(tokenizar_xml(entrada_lf)))
        self.assertEqual(posicoes(tokenizar_xml(entrada_cr)), posicoes(tokenizar_xml(entrada_lf)))

    def test_tabulacao_conta_como_uma_coluna(self):
        fita = tokenizar_xml("\t<p>\tOi</p>")
        self.assertEqual(
            posicoes(fita),
            [("<p>", 1, 2), ("#texto", 1, 6), ("</p>", 1, 8), ("$", 1, 12)],
        )

    def test_marcador_fim_logo_apos_ultimo_caractere_e_apos_quebra_final(self):
        self.assertEqual(tokenizar_xml("abc")[-1], Token("$", "", 1, 4))
        self.assertEqual(tokenizar_xml("abc\n")[-1], Token("$", "", 2, 1))
        self.assertEqual(tokenizar_xml("abc\r\n")[-1], Token("$", "", 2, 1))

    def test_nome_da_tag_normalizado_para_minusculas_preservando_lexema(self):
        fita = tokenizar_xml('<DIV CLASS="x"></DIV>')
        self.assertEqual(fita[0], Token("<div>", '<DIV CLASS="x">', 1, 1))
        self.assertEqual(fita[1], Token("</div>", "</DIV>", 1, 16))

    def test_caracteres_validos_no_nome_da_tag(self):
        fita = tokenizar_xml("<ns:item-1_a.b></ns:item-1_a.b>")
        self.assertEqual(
            simbolos(fita),
            ["<ns:item-1_a.b>", "</ns:item-1_a.b>", "$"],
        )

    def test_fechamento_com_espacos_antes_de_maior(self):
        fita = tokenizar_xml("<div></div >")
        self.assertEqual(fita[1], Token("</div>", "</div >", 1, 6))

    def test_tags_auto_fechadas_geram_simbolo_com_barra(self):
        for bruto in ("<br/>", "<br />", "<BR/>", '<br class="x" />'):
            with self.subTest(bruto=bruto):
                fita = tokenizar_xml(bruto)
                self.assertEqual(fita[0].simbolo, "<br/>")
                self.assertEqual(fita[0].lexema, bruto)

    def test_tag_fora_do_subconjunto_nao_levanta_erro_lexico(self):
        fita = tokenizar_xml("<table></table>")
        self.assertEqual(simbolos(fita), ["<table>", "</table>", "$"])


class TestTokenizarXmlAtributosComentariosETexto(unittest.TestCase):
    """Atributos com aspas, comentários e regras de agrupamento de #texto."""

    def test_maior_dentro_de_aspas_duplas_e_simples_nao_fecha_tag(self):
        fita_duplas = tokenizar_xml('<div title="a>b">ok</div>')
        self.assertEqual(
            fita_duplas,
            [
                Token("<div>", '<div title="a>b">', 1, 1),
                Token("#texto", "ok", 1, 18),
                Token("</div>", "</div>", 1, 20),
                Token("$", "", 1, 26),
            ],
        )

        fita_simples = tokenizar_xml("<div title='a>b'>ok</div>")
        self.assertEqual(fita_simples[0], Token("<div>", "<div title='a>b'>", 1, 1))
        self.assertEqual(fita_simples[1], Token("#texto", "ok", 1, 18))

    def test_aspas_alternadas_e_barra_dentro_de_atributo_nao_viram_auto_fechada(self):
        fita = tokenizar_xml("""<div data-expr="a'b>c/" title='x"y>z/'>""")
        self.assertEqual(fita[0].simbolo, "<div>")
        self.assertEqual(simbolos(fita), ["<div>", "$"])

    def test_atributo_em_varias_linhas_atualiza_posicao_seguinte(self):
        entrada = '<div\n  id="1"\n  title="a\nb"><p>oi</p></div>'
        fita = tokenizar_xml(entrada)
        self.assertEqual(
            posicoes(fita),
            [
                ("<div>", 1, 1),
                ("<p>", 4, 4),
                ("#texto", 4, 7),
                ("</p>", 4, 9),
                ("</div>", 4, 13),
                ("$", 4, 19),
            ],
        )

    def test_comentario_ignorado_mantem_posicoes_exatas(self):
        fita = tokenizar_xml("<p><!-- oi --></p>")
        self.assertEqual(
            posicoes(fita),
            [("<p>", 1, 1), ("</p>", 1, 15), ("$", 1, 19)],
        )

    def test_comentario_com_quebras_de_linha_e_tags_internas(self):
        entrada = "<div><!-- linha 1\n  <p>tag ignorada</p>\n  fim --><p>real</p></div>"
        fita = tokenizar_xml(entrada)
        self.assertEqual(
            posicoes(fita),
            [
                ("<div>", 1, 1),
                ("<p>", 3, 10),
                ("#texto", 3, 13),
                ("</p>", 3, 17),
                ("</div>", 3, 21),
                ("$", 3, 27),
            ],
        )

    def test_comentario_vazio_imediato(self):
        fita = tokenizar_xml("<!----><p></p>")
        self.assertEqual(
            posicoes(fita),
            [("<p>", 1, 8), ("</p>", 1, 11), ("$", 1, 15)],
        )

    def test_apenas_espacos_entre_tags_nao_geram_texto(self):
        fita = tokenizar_xml("<div>   \n\t  <p> \n </p>\t</div>")
        self.assertEqual(simbolos(fita), ["<div>", "<p>", "</p>", "</div>", "$"])

    def test_texto_com_espacos_nas_pontas_guarda_lexema_limpo_e_primeira_posicao(self):
        fita = tokenizar_xml("<p>  Olá mundo \n</p>")
        self.assertEqual(fita[1], Token("#texto", "Olá mundo", 1, 6))
        self.assertEqual(fita[2], Token("</p>", "</p>", 2, 1))

    def test_texto_em_varias_linhas_gera_unico_token(self):
        fita = tokenizar_xml("<p>\n  primeira linha\n  segunda linha  \n</p>")
        self.assertEqual(simbolos(fita), ["<p>", "#texto", "</p>", "$"])
        self.assertEqual(
            fita[1],
            Token("#texto", "primeira linha\n  segunda linha", 2, 3),
        )

    def test_comentario_no_meio_do_texto_separa_em_dois_tokens(self):
        fita = tokenizar_xml("a <!-- c --> b")
        self.assertEqual(
            fita,
            [
                Token("#texto", "a", 1, 1),
                Token("#texto", "b", 1, 14),
                Token("$", "", 1, 15),
            ],
        )


class TestTokenizarXmlErrosLexicos(unittest.TestCase):
    """Os quatro erros léxicos do contrato, com mensagem e posição exatas."""

    def test_erro_tag_sem_maior_correspondente_no_inicio(self):
        with self.assertRaises(ErroLexico) as ctx:
            tokenizar_xml("<div")
        self.assertEqual(ctx.exception.mensagem, "'<' sem '>' correspondente")
        self.assertEqual((ctx.exception.linha, ctx.exception.coluna), (1, 1))

    def test_erro_tag_sem_maior_no_meio_da_entrada(self):
        with self.assertRaises(ErroLexico) as ctx:
            tokenizar_xml("<div><p>oi</div")
        self.assertEqual(ctx.exception.mensagem, "'<' sem '>' correspondente")
        self.assertEqual((ctx.exception.linha, ctx.exception.coluna), (1, 11))

    def test_erro_aspas_nao_fechadas_em_atributo_aponta_para_abertura_da_tag(self):
        with self.assertRaises(ErroLexico) as ctx:
            tokenizar_xml('<p><div class="aberta>texto</div></p>')
        self.assertEqual(ctx.exception.mensagem, "'<' sem '>' correspondente")
        self.assertEqual((ctx.exception.linha, ctx.exception.coluna), (1, 4))

    def test_erro_menor_isolado_no_fim(self):
        for entrada in ("<", "</"):
            with self.subTest(entrada=entrada):
                with self.assertRaises(ErroLexico) as ctx:
                    tokenizar_xml(entrada)
                self.assertEqual(ctx.exception.mensagem, "'<' sem '>' correspondente")
                self.assertEqual((ctx.exception.linha, ctx.exception.coluna), (1, 1))

    def test_erro_tag_sem_nome(self):
        casos = [
            ("<>", (1, 1)),
            ("</>", (1, 1)),
            ("< div>", (1, 1)),
            ("<div></></div>", (1, 6)),
        ]
        for entrada, esperado in casos:
            with self.subTest(entrada=entrada):
                with self.assertRaises(ErroLexico) as ctx:
                    tokenizar_xml(entrada)
                self.assertEqual(ctx.exception.mensagem, "tag sem nome")
                self.assertEqual((ctx.exception.linha, ctx.exception.coluna), esperado)

    def test_erro_caractere_invalido_no_nome_da_tag(self):
        casos = [
            ("<d!v>", "caractere inválido '!' no nome da tag", (1, 3)),
            ("<1p>", "caractere inválido '1' no nome da tag", (1, 2)),
            ("<!DOCTYPE html>", "caractere inválido '!' no nome da tag", (1, 2)),
            ("</d$v>", "caractere inválido '$' no nome da tag", (1, 4)),
        ]
        for entrada, mensagem, esperado in casos:
            with self.subTest(entrada=entrada):
                with self.assertRaises(ErroLexico) as ctx:
                    tokenizar_xml(entrada)
                self.assertEqual(ctx.exception.mensagem, mensagem)
                self.assertEqual((ctx.exception.linha, ctx.exception.coluna), esperado)

    def test_erro_comentario_nao_fechado(self):
        casos = [
            ("<!-- sem fim", (1, 1)),
            ("<!-->", (1, 1)),
            ("<!--->", (1, 1)),
            ("<p><!-- nao fecha", (1, 4)),
        ]
        for entrada, esperado in casos:
            with self.subTest(entrada=entrada):
                with self.assertRaises(ErroLexico) as ctx:
                    tokenizar_xml(entrada)
                self.assertEqual(ctx.exception.mensagem, "comentário não fechado")
                self.assertEqual((ctx.exception.linha, ctx.exception.coluna), esperado)

    def test_erros_em_linhas_posteriores_reportam_linha_e_coluna_certas(self):
        with self.assertRaises(ErroLexico) as ctx_tag:
            tokenizar_xml("<html>\n  <body>\n    <d!v>\n  </body>\n</html>")
        self.assertEqual(ctx_tag.exception.mensagem, "caractere inválido '!' no nome da tag")
        self.assertEqual((ctx_tag.exception.linha, ctx_tag.exception.coluna), (3, 7))

        with self.assertRaises(ErroLexico) as ctx_com:
            tokenizar_xml("<html>\n  <!-- comentario\n  sem fechar")
        self.assertEqual(ctx_com.exception.mensagem, "comentário não fechado")
        self.assertEqual((ctx_com.exception.linha, ctx_com.exception.coluna), (2, 3))


class TestTokenizarExpressao(unittest.TestCase):
    """Tokenização de delimitadores e operandos em expressões balanceadas."""

    def test_expressao_vazia_gera_apenas_marcador_fim(self):
        self.assertEqual(tokenizar_expressao(""), [Token("$", "", 1, 1)])

    def test_seis_delimitadores_com_colunas_consecutivas(self):
        fita = tokenizar_expressao("{[()]}")
        self.assertEqual(
            posicoes(fita),
            [
                ("{", 1, 1),
                ("[", 1, 2),
                ("(", 1, 3),
                (")", 1, 4),
                ("]", 1, 5),
                ("}", 1, 6),
                ("$", 1, 7),
            ],
        )

    def test_exemplo_expressao_completa_da_especificacao(self):
        fita = tokenizar_expressao("2*(3+[4-1])")
        self.assertEqual(
            fita,
            [
                Token("x", "2*", 1, 1),
                Token("(", "(", 1, 3),
                Token("x", "3+", 1, 4),
                Token("[", "[", 1, 6),
                Token("x", "4-1", 1, 7),
                Token("]", "]", 1, 10),
                Token(")", ")", 1, 11),
                Token("$", "", 1, 12),
            ],
        )

    def test_espacos_e_tabulacoes_separam_operandos(self):
        fita = tokenizar_expressao("( a\tb )")
        self.assertEqual(
            fita,
            [
                Token("(", "(", 1, 1),
                Token("x", "a", 1, 3),
                Token("x", "b", 1, 5),
                Token(")", ")", 1, 7),
                Token("$", "", 1, 8),
            ],
        )

    def test_quebra_de_linha_lf_e_crlf_em_expressao(self):
        fita_lf = tokenizar_expressao("(\n)")
        fita_crlf = tokenizar_expressao("(\r\n)")
        esperado = [
            Token("(", "(", 1, 1),
            Token(")", ")", 2, 1),
            Token("$", "", 2, 2),
        ]
        self.assertEqual(fita_lf, esperado)
        self.assertEqual(fita_crlf, esperado)

    def test_caracteres_especiais_viram_operando_sem_erro_lexico(self):
        fita = tokenizar_expressao("< @ ç $")
        self.assertEqual(
            fita,
            [
                Token("x", "<", 1, 1),
                Token("x", "@", 1, 3),
                Token("x", "ç", 1, 5),
                Token("x", "$", 1, 7),
                Token("$", "", 1, 8),
            ],
        )

    def test_operando_no_fim_sem_delimitador(self):
        fita = tokenizar_expressao("2+3*a")
        self.assertEqual(
            fita,
            [Token("x", "2+3*a", 1, 1), Token("$", "", 1, 6)],
        )


class TestDespachoEContrato(unittest.TestCase):
    """Função fachada ``tokenizar``, assinaturas públicas e integração com ``APD``."""

    def test_despacho_xml_e_expressao(self):
        xml = "<div><p>oi</p></div>"
        expr = "2*(3+4)"
        self.assertEqual(tokenizar(xml, "xml"), tokenizar_xml(xml))
        self.assertEqual(tokenizar(expr, "expressao"), tokenizar_expressao(expr))

    def test_tipo_invalido_levanta_value_error(self):
        for invalido in ("json", "XML", "", "html"):
            with self.subTest(tipo=invalido):
                with self.assertRaises(ValueError):
                    tokenizar("<div></div>", invalido)

    def test_assinaturas_exatas_do_contrato(self):
        self.assertEqual(
            list(inspect.signature(tokenizar_xml).parameters),
            ["texto"],
        )
        self.assertEqual(
            list(inspect.signature(tokenizar_expressao).parameters),
            ["texto"],
        )
        self.assertEqual(
            list(inspect.signature(tokenizar).parameters),
            ["texto", "tipo"],
        )

    def test_fita_gerada_executa_diretamente_no_apd(self):
        apd_expr = APD(
            nome="Parênteses",
            estados={"q0", "qf"},
            alfabeto_entrada={"(", ")", "x", "$"},
            alfabeto_pilha={"Z0", "PAR"},
            transicoes=[
                Transicao("q0", "(", "Z0", "q0", ("PAR", "Z0")),
                Transicao("q0", "(", "PAR", "q0", ("PAR", "PAR")),
                Transicao("q0", ")", "PAR", "q0", ()),
                Transicao("q0", "x", "Z0", "q0", ("Z0",)),
                Transicao("q0", "x", "PAR", "q0", ("PAR",)),
                Transicao("q0", "$", "Z0", "qf", ("Z0",)),
            ],
            estado_inicial="q0",
            simbolo_inicial_pilha="Z0",
            estados_finais={"qf"},
            tokenizador="expressao",
        )
        self.assertTrue(apd_expr.executar(tokenizar("(2 + (3 * 4))", "expressao")).aceita)
        self.assertFalse(apd_expr.executar(tokenizar("((2 + 3)", "expressao")).aceita)


if __name__ == "__main__":
    unittest.main()
