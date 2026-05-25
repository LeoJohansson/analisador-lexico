# 🧠 Analisador Léxico e Sintático em Python

Este projeto implementa um **analisador léxico (scanner)** e um **analisador sintático (parser)** desenvolvidos em Python, como parte da disciplina de **Compiladores**.

O sistema realiza duas etapas principais:

- 🔎 **Análise Léxica** → transforma o código fonte em uma sequência de tokens
- 🌳 **Análise Sintática** → interpreta os tokens e gera uma AST (*Abstract Syntax Tree*)

O analisador léxico identifica os elementos básicos da linguagem, enquanto o parser organiza esses elementos de acordo com regras gramaticais.

---

# 🚀 Funcionalidades

O sistema reconhece e processa os seguintes elementos:

- 🔑 **Palavras reservadas** (`if`, `while`, `return`, `class`, `def`, `import`, etc.)
- 🏷️ **Identificadores** (nomes de variáveis, funções e classes)
- 🔢 **Literais** (números inteiros, reais e strings)
- ➕ **Operadores** (`+`, `-`, `*`, `/`, `==`, `!=`, etc.)
- 📌 **Delimitadores** (`()`, `{}`, `[]`, `:`, `,`, `.` etc.)
- 🧾 **Comentários** (ignorados pelo analisador)
- ⚠️ **Erros léxicos** (símbolos inválidos, strings não finalizadas e números mal formados)
- 🌳 **Geração de AST simplificada**
- 📄 **EOF (End Of File)**

---

# ⚙️ Como funciona

O analisador léxico utiliza a técnica de **dois ponteiros**:

- `inicio` → marca o início do token
- `atual` → percorre o código caractere por caractere

Além disso, utiliza **lookahead** para identificar tokens compostos, como:

- `==`
- `!=`
- `<=`
- `>=`

Após a análise léxica, os tokens são enviados ao parser.

O parser foi implementado utilizando a técnica de **Recursive Descent Parser (Parser Descendente Recursivo)**, onde cada método representa uma regra da gramática.

O parser também implementa:

- atribuições
- expressões aritméticas
- precedência de operadores
- importações
- funções
- classes
- retorno (`return`)
- recuperação simples de erros

---

# 📂 Estrutura do Projeto

- `TipoToken` → Enum com as categorias de tokens
- `Token` → Estrutura que representa um token
- `AnalisadorLexico` → Classe principal do scanner
- `Parser` → Classe responsável pela análise sintática
- `processar()` → Função que executa todo o fluxo do sistema

---

# ▶️ Como executar

## 1. Crie um arquivo de entrada

Exemplo:

```python
teste.py
```

---

## 2. Execute o script

```bash
python nome_do_arquivo.py
```

---

## 3. Arquivos gerados

O programa irá gerar os arquivos:

```txt
saida_tokens.txt
saida_ast.txt
```

---

# 📊 Saída Léxica

O arquivo `saida_tokens.txt` contém:

- linha
- coluna
- categoria do token
- lexema original

## Exemplo

```txt
LINHA  | COL  | CATEGORIA            | LEXEMA
----------------------------------------------------------------------
1      | 1    | PALAVRA_RESERVADA    | from
1      | 6    | IDENTIFICADOR        | math
1      | 11   | PALAVRA_RESERVADA    | import
1      | 18   | IDENTIFICADOR        | sqrt
```

---

# 🌳 Saída Sintática

O arquivo `saida_ast.txt` contém a AST (*Árvore Sintática Abstrata*) gerada pelo parser.

## Exemplo

```txt
ÁRVORE SINTÁTICA:

('FROM_IMPORT', 'math', 'sqrt')
('IMPORT', 'os')
('ATRIBUICAO', 'x', ('NUMERO', '10'))
('ATRIBUICAO', 'y', ('NUMERO', '20'))
('ATRIBUICAO', 'resultado', ('BINARIA', '+', ('VARIAVEL', 'x'), ('BINARIA', '*', ('VARIAVEL', 'y'), ('NUMERO', '2'))))
('CLASS', 'Pessoa')
('ATRIBUICAO', 'nome', ('STRING', '"João"'))
('FUNCAO', 'soma')
('RETURN', ('BINARIA', '+', ('VARIAVEL', 'x'), ('VARIAVEL', 'y')))
('NUMERO', '0.0')
('NUMERO', '0')
('ERRO', '[Linha 19] Erro léxico: Número mal formado')
```

---

# ⚠️ Tratamento de Erros

O sistema identifica erros léxicos como:

- caracteres inválidos (`@`, `$`, etc.)
- strings não finalizadas
- números mal formados (`0.0.0`)

Nestes casos, é gerado um nó de erro na AST:

```txt
('ERRO', '[Linha 19] Erro léxico: Número mal formado')
```

Também são tratados erros sintáticos, como:

- ausência de `)`
- ausência de `=`
- tokens inesperados

O parser implementa uma recuperação simples de erro para continuar a análise mesmo após encontrar problemas.

---

# 📌 Observações

- Comentários são reconhecidos, mas ignorados
- Strings podem utilizar aspas simples `'` ou duplas `"`
- Suporte a números inteiros e reais
- O parser respeita precedência de operadores:
  - multiplicação/divisão antes de soma/subtração
- AST representada utilizando tuplas Python
- Implementação inspirada na sintaxe da linguagem Python

---

# 🎓 Objetivo Acadêmico

Este projeto foi desenvolvido com o objetivo de compreender na prática:

- funcionamento de um analisador léxico
- construção de parsers
- geração de AST
- reconhecimento de padrões em linguagens formais
- estrutura básica de compiladores
- tratamento de erros léxicos e sintáticos

---

# 👨‍💻 Autor

Desenvolvido para fins acadêmicos na disciplina de Compiladores.

---

# 📎 Possíveis melhorias

- implementação de análise semântica
- tabela de símbolos
- verificação de tipos
- suporte completo à identação do Python
- suporte a condicionais e loops completos
- AST baseada em classes de nós
- visualização gráfica da árvore sintática
- implementação de interpretador

---

💡 *Projeto didático com foco no aprendizado de compiladores, análise léxica e análise sintática.*
