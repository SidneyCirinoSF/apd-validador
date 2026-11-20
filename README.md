# APD Validador

Simulador de **Autômato com Pilha Determinístico (APD)** para validar estruturas
aninhadas, feito em Python puro (somente biblioteca padrão) para a AV2 de
**Linguagens Formais e Autômatos**, Desafio 4: *Validador de Sintaxe com Autômato com Pilha*.

O programa lê um texto, transforma esse texto em uma fita de símbolos e executa um APD
M = (Q, Σ, Γ, δ, q0, Z0, F) sobre ela, mostrando **a pilha a cada símbolo consumido**
(empilha, desempilha ou mantém) e, quando a entrada é rejeitada, **o motivo exato da falha**.

> **Status: em desenvolvimento.** O núcleo já está na `main`: contratos de dados
> (`apd/modelos.py`), classe APD (`apd/automato.py`) e carregador (`apd/carregador.py`),
> com testes. O tokenizador, os JSON dos autômatos, o diagnóstico, a CLI e a GUI ainda
> não existem, então os comandos `python -m apd` abaixo **ainda não funcionam**; eles
> passam a funcionar à medida que as tarefas de [docs/TAREFAS.md](docs/TAREFAS.md) forem
> concluídas.

## O que o APD valida

Dois autômatos, cada um descrito em um arquivo JSON na pasta `automatos/`:

| Autômato | Arquivo | O que reconhece |
|---|---|---|
| Tags XML/HTML (subconjunto) | `automatos/xml_tags.json` | Abertura e fechamento corretamente aninhados das tags `html`, `body`, `div`, `p`, `ul` e `li`, com texto entre elas |
| Expressões balanceadas | `automatos/expressoes.json` | Parênteses `( )`, colchetes `[ ]` e chaves `{ }` balanceados e corretamente aninhados, com qualquer conteúdo entre eles (ex.: `{[(2+3)*a]}`) |

Detalhes que valem para a entrada XML:

- atributos são ignorados (`<div class="x">` é lido como `<div>`) e o nome da tag não
  diferencia maiúsculas de minúsculas;
- comentários `<!-- ... -->`, espaços e quebras de linha são ignorados;
- tags fora do subconjunto (`<table>`, `<br/>` etc.) são rejeitadas, porque não
  pertencem ao alfabeto de entrada Σ.

Exemplos de motivos de rejeição que o programa informa: *fechamento incompatível com o
topo da pilha*, *fechamento sem abertura correspondente*, *pilha não vazia ao fim da
entrada* e *símbolo fora do alfabeto*, sempre com linha e coluna do símbolo.

A definição formal completa (estados, alfabetos e a função de transição δ) está em
[docs/DEFINICAO_FORMAL.md](docs/DEFINICAO_FORMAL.md).

## Requisitos

- **Python 3.10 ou superior** (`python --version` para conferir).
- **Nenhuma dependência externa.** Só a biblioteca padrão (`json`, `dataclasses`,
  `argparse`, `tkinter`, `unittest` etc.). Não é preciso `pip install`.
- Para a interface gráfica: `tkinter`, que já vem com o instalador oficial do Python
  no Windows e no macOS. Em algumas distribuições Linux é preciso instalar o pacote
  `python3-tk`.

## Como executar

> **Ainda não disponível.** Os comandos `python -m apd` abaixo seguem o contrato de
> [docs/ARQUITETURA.md](docs/ARQUITETURA.md) §10 e ficam disponíveis quando a CLI (#6) e
> a GUI (#8) forem concluídas.

```bash
git clone https://github.com/SidneyCirinoSF/apd-validador.git
cd apd-validador
```

Na raiz do repositório:

```bash
python -m apd                                   # menu interativo no terminal
python -m apd --gui                             # abre a interface gráfica (tkinter)

# validar um texto direto pela linha de comando
python -m apd -a automatos/xml_tags.json -e "<div><p>oi</p></div>"

# validar o conteúdo de um arquivo
python -m apd -a automatos/expressoes.json -f exemplos/expressoes/valida_01.txt

# opções de exibição (combinam com -e ou -f)
python -m apd ... --passo                       # pausa a cada passo (Enter avança)
python -m apd ... --atraso 0.4                  # animação automática, 0,4 s por passo
python -m apd ... --definicao                   # mostra M = (...) e a tabela δ
python -m apd ... --sem-cor                     # desliga as cores ANSI
```

No Windows, se `python` não for reconhecido, use `py` no lugar (ex.: `py -m apd`).

## Como rodar os testes

Os testes usam `unittest`, da biblioteca padrão, e já rodam (hoje cobrem os modelos,
a classe APD e o carregador):

```bash
python -m unittest discover -s tests -v
```

## Exemplo de saída esperada (ilustrativo)

> **Ilustrativo:** mostra a ideia da exibição passo a passo; a formatação final será
> definida na implementação da CLI. A pilha é escrita com o **topo à esquerda**
> e Z0 marca o fundo.

Entrada aceita:

```text
$ python -m apd -a automatos/xml_tags.json -e "<div><p>oi</p></div>"

Autômato: Tags XML/HTML (subconjunto)
Fita:     <div> <p> #texto </p> </div> $

Passo  Estado  Lê      Topo  Transição                        Ação        Pilha
  1    q0      <div>   Z0    δ(q0, <div>, Z0) = (q0, DIV Z0)  empilha     DIV Z0
  2    q0      <p>     DIV   δ(q0, <p>, DIV) = (q0, P DIV)    empilha     P DIV Z0
  3    q0      #texto  P     δ(q0, #texto, P) = (q0, P)       mantém      P DIV Z0
  4    q0      </p>    P     δ(q0, </p>, P) = (q0, ε)         desempilha  DIV Z0
  5    q0      </div>  DIV   δ(q0, </div>, DIV) = (q0, ε)     desempilha  Z0
  6    q0      $       Z0    δ(q0, $, Z0) = (qf, Z0)          mantém      Z0

Resultado: ACEITA (a fita foi consumida e o estado qf ∈ F)
```

Entrada rejeitada:

```text
$ python -m apd -a automatos/xml_tags.json -e "<div><p>oi</div>"

Passo  Estado  Lê      Topo  Transição                        Ação        Pilha
  1    q0      <div>   Z0    δ(q0, <div>, Z0) = (q0, DIV Z0)  empilha     DIV Z0
  2    q0      <p>     DIV   δ(q0, <p>, DIV) = (q0, P DIV)    empilha     P DIV Z0
  3    q0      #texto  P     δ(q0, #texto, P) = (q0, P)       mantém      P DIV Z0
  -    q0      </div>  P     nenhuma transição para (q0, </div>, P)

Resultado: REJEITADA
Motivo:    fechamento incompatível com o topo da pilha
           '</div>' (linha 1, coluna 11) é incompatível com o topo da pilha '<p>':
           era esperado '</p>'.
```

O símbolo `$` é o marcador de fim de entrada que o tokenizador acrescenta ao final da
fita; o porquê dele está em [docs/ARQUITETURA.md](docs/ARQUITETURA.md) §4.

## Estrutura do repositório

```text
apd-validador/
├── apd/            pacote principal: modelos, núcleo do APD, tokenizador, diagnóstico, CLI e GUI
├── automatos/      definição formal dos autômatos em JSON
├── ferramentas/    gerador dos arquivos JSON
├── exemplos/       entradas válidas e inválidas para testar e demonstrar
├── tests/          testes com unittest
└── docs/           documentação do projeto
```

A descrição de cada módulo e de quem é responsável por ele está em
[docs/ARQUITETURA.md](docs/ARQUITETURA.md) §2.

## Mapa da documentação

| Documento | Para que serve |
|---|---|
| [docs/ENUNCIADO.md](docs/ENUNCIADO.md) | Resumo do enunciado da AV2, critérios de avaliação e onde cada requisito é atendido |
| [docs/DEFINICAO_FORMAL.md](docs/DEFINICAO_FORMAL.md) | Definição formal M = (Q, Σ, Γ, δ, q0, Z0, F) dos dois autômatos |
| [docs/ARQUITETURA.md](docs/ARQUITETURA.md) | Contrato técnico entre os módulos: nomes, assinaturas e convenções |
| [docs/CONTRIBUINDO.md](docs/CONTRIBUINDO.md) | Guia de Git e GitHub da equipe: branch, commit, pull request e Kanban |
| [docs/TAREFAS.md](docs/TAREFAS.md) | Divisão das tarefas e ordem de execução |

Quadro Kanban: aba Projects do repositório.

## Equipe

| Integrante | GitHub | Responsabilidade |
|---|---|---|
| Sidney (líder) | [@SidneyCirinoSF](https://github.com/SidneyCirinoSF) | Contratos (`modelos.py`) e núcleo do APD (`automato.py`, `carregador.py`), já concluídos; diagnóstico de falhas (`diagnostico.py`); interface de terminal (`cli.py`, `__main__.py`); roteiro da demonstração; Prezi; teste de integração e integração final |
| Joalison | [@Joalison7](https://github.com/Joalison7) | Gerador e JSON dos autômatos |
| Pedro Valença | [@PedroValencav2](https://github.com/PedroValencav2) | Exemplos de entrada e resultados esperados (`exemplos/`) |
| Fabrício | [@Cibr0](https://github.com/Cibr0) | Interface gráfica tkinter (`gui.py`) |
| Wagner Daniel | [@WagnerDaniell](https://github.com/WagnerDaniell) | Tokenizador (`tokenizador.py`) |

## Disciplina

| | |
|---|---|
| Instituição | Centro Universitário Maurício de Nassau (UNINASSAU) |
| Curso | Ciência da Computação, 6º período, turma da manhã |
| Disciplina | Linguagens Formais e Autômatos |
| Professor | Alamy Veríssimo Pereira Jr. |
| Avaliação | AV2 (2026.2), tipo Projetos, Desafio 4 |
| Apresentação | 03/12/2026 (quinta-feira), com slides no Prezi |
