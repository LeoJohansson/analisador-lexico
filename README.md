# analisador-lexico

# 🧠 Analisador Léxico em Python

Este projeto implementa um **analisador léxico (scanner)** desenvolvido em Python, como parte de estudos na disciplina de **Compiladores**.

O analisador é responsável por ler um código fonte e transformá-lo em uma sequência de **tokens**, que são as unidades básicas para as próximas fases de um compilador (análise sintática e semântica).

---

## 🚀 Funcionalidades

O analisador reconhece e classifica os seguintes tipos de tokens:

* 🔑 **Palavras reservadas** (if, while, return, etc.)
* 🏷️ **Identificadores** (nomes de variáveis e funções)
* 🔢 **Literais** (números inteiros, reais e strings)
* ➕ **Operadores** (+, -, *, /, ==, !=, etc.)
* 📌 **Delimitadores** ((), {}, [], vírgulas, pontos, etc.)
* 🧾 **Comentários** (ignorados pelo analisador)
* ⚠️ **Erros léxicos** (símbolos inválidos e strings não finalizadas)
* 📄 **EOF (End Of File)**

---

## ⚙️ Como funciona

O analisador utiliza a técnica de **dois ponteiros**:

* `inicio`: marca o início do token
* `atual`: percorre o código caractere por caractere

Além disso, utiliza **lookahead** para identificar tokens compostos, como:

* `==`
* `!=`
* `<=`
* `>=`

---

## 📂 Estrutura do Projeto

* `TipoToken` → Enum com as categorias de tokens
* `Token` → Estrutura que representa um token
* `AnalisadorLexico` → Classe principal do scanner
* `processar()` → Função que lê o arquivo de entrada e gera a saída

---

## ▶️ Como executar

1. Crie um arquivo de entrada, por exemplo:

```
teste.py
```

2. Execute o script:

```bash
python nome_do_arquivo.py
```

3. O programa irá gerar um arquivo:

```
saida_tokens.txt
```

---

## 📊 Saída

O arquivo de saída contém uma tabela com:

* Linha
* Coluna
* Categoria do token
* Lexema (texto original)

Exemplo:

```
LINHA  | COL  | CATEGORIA           | LEXEMA
------------------------------------------------------------
1      | 1    | PALAVRA_RESERVADA   | if
1      | 4    | IDENTIFICADOR       | x
1      | 6    | OPERADOR            | ==
1      | 9    | LITERAL             | 10
```

---

## ⚠️ Tratamento de Erros

O analisador identifica erros léxicos como:

* Caracteres inválidos (ex: `@`, `$`)
* Strings não finalizadas

Nestes casos, é gerado um token do tipo:

```
ERRO_LEXICO
```

---

## 📌 Observações

* Comentários são reconhecidos, mas **ignorados** (não geram tokens)
* Strings podem ser delimitadas por aspas simples `'` ou duplas `"`
* Suporte a números inteiros e reais
* Implementação inspirada em linguagens como Python

---

## 🎓 Objetivo Acadêmico

Este projeto foi desenvolvido com o objetivo de compreender na prática:

* Funcionamento de um analisador léxico
* Reconhecimento de padrões em linguagens formais
* Estrutura de compiladores

---

## 👨‍💻 Autor

Desenvolvido para fins acadêmicos na disciplina de Compiladores.

---

## 📎 Possíveis melhorias

* Separação entre tipos de literais (inteiro, real, string)
* Suporte a mais operadores (&&, ||)
* Melhor tratamento de erros léxicos
* Implementação de tabela de símbolos

---

💡 *Projeto didático com foco no aprendizado de compiladores e análise léxica.*
