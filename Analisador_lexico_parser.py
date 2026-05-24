from enum import Enum
import os

# ==========================================
# 1. DEFINIÇÕES DE TOKENS
# ==========================================

class TipoToken(Enum):

    PALAVRA_RESERVADA = 'PALAVRA_RESERVADA'
    IDENTIFICADOR     = 'IDENTIFICADOR'

    NUMERO            = 'NUMERO'
    STRING            = 'STRING'

    OPERADOR          = 'OPERADOR'
    DELIMITADOR       = 'DELIMITADOR'

    EOF               = 'FIM_DE_ARQUIVO'
    ERRO              = 'ERRO_LEXICO'


# ==========================================
# 2. TOKEN
# ==========================================

class Token:

    def __init__(
        self,
        tipo,
        lexema,
        linha,
        coluna
    ):

        self.tipo = tipo
        self.lexema = lexema
        self.linha = linha
        self.coluna = coluna

    def __repr__(self):

        return (
            f"{self.tipo.value}"
            f"('{self.lexema}')"
        )


# ==========================================
# 3. LEXER
# ==========================================

class AnalisadorLexico:

    def __init__(self, codigo_fonte):

        self.codigo = codigo_fonte

        self.inicio = 0
        self.atual = 0

        self.linha = 1
        self.coluna = 1
        self.inicio_coluna = 1

        self.tokens = []

        self.reservadas = {

            'if','else','elif','while','for','def','return',
            'class','import','from','as','with','in','try',
            'except','finally','pass','break','continue',
            'and','or','not','True','False','None'
        }

    # ==========================================
    # NAVEGAÇÃO
    # ==========================================

    def no_final(self):

        return self.atual >= len(self.codigo)

    def avancar(self):

        char = self.codigo[self.atual]

        self.atual += 1

        if char == '\n':

            self.linha += 1
            self.coluna = 1

        else:

            self.coluna += 1

        return char

    def espiar(self):

        if self.no_final():
            return '\0'

        return self.codigo[self.atual]

    def espiar_proximo(self):

        if self.atual + 1 >= len(self.codigo):
            return '\0'

        return self.codigo[self.atual + 1]

    def combinar(self, esperado):

        if self.no_final():
            return False

        if self.codigo[self.atual] != esperado:
            return False

        self.atual += 1
        self.coluna += 1

        return True

    def adicionar_token(
        self,
        tipo,
        lexema_custom=None
    ):

        texto = (

            lexema_custom

            if lexema_custom

            else self.codigo[
                self.inicio:self.atual
            ]
        )

        self.tokens.append(

            Token(
                tipo,
                texto,
                self.linha,
                self.inicio_coluna
            )
        )

    # ==========================================
    # COMENTÁRIOS
    # ==========================================

    def tratar_comentario_linha(self):

        while (
            self.espiar() != '\n'
            and not self.no_final()
        ):
            self.avancar()

    def tratar_comentario_bloco(self):

        while not self.no_final():

            if (
                self.codigo[
                    self.atual:self.atual+3
                ] == '"""'
            ):

                for _ in range(3):
                    self.avancar()

                return

            self.avancar()

    # ==========================================
    # STRING
    # ==========================================

    def tratar_string(self, delimitador):

        while (
            self.espiar() != delimitador
            and not self.no_final()
        ):
            self.avancar()

        if self.no_final():

            self.adicionar_token(
                TipoToken.ERRO,
                "String não finalizada"
            )

            return

        self.avancar()

        self.adicionar_token(
            TipoToken.STRING
        )

    # ==========================================
    # NÚMERO
    # ==========================================

    def tratar_numero(self):

        while self.espiar().isdigit():
            self.avancar()

        # decimal

        if self.espiar() == '.':

            if not self.espiar_proximo().isdigit():

                self.adicionar_token(
                    TipoToken.NUMERO
                )

                return

            self.avancar()

            while self.espiar().isdigit():
                self.avancar()

            # evita 0.0.0

            if self.espiar() == '.':

                while (
                    self.espiar().isdigit()
                    or self.espiar() == '.'
                ):
                    self.avancar()

                self.adicionar_token(
                    TipoToken.ERRO,
                    "Número mal formado"
                )

                return

        self.adicionar_token(
            TipoToken.NUMERO
        )

    # ==========================================
    # TOKENIZAÇÃO
    # ==========================================

    def escanear_token(self):

        c = self.avancar()

        # espaços

        if c in [' ', '\r', '\t', '\n']:
            return

        # comentário linha

        if c == '#':

            self.tratar_comentario_linha()
            return

        # comentário bloco

        if (
            c == '"'
            and self.espiar() == '"'
            and self.espiar_proximo() == '"'
        ):

            for _ in range(2):
                self.avancar()

            self.tratar_comentario_bloco()
            return

        # delimitadores

        elif c in '()[]{},.:':
            self.adicionar_token(
                TipoToken.DELIMITADOR
            )

        # operadores

        elif c in '+-*/%':

            self.adicionar_token(
                TipoToken.OPERADOR
            )

        # relacionais

        elif c in '=!<>':

            if (
                c == '!'
                and not self.combinar('=')
            ):

                self.adicionar_token(
                    TipoToken.ERRO
                )

            else:

                self.combinar('=')

                self.adicionar_token(
                    TipoToken.OPERADOR
                )

        # strings

        elif c == '"' or c == "'":

            self.tratar_string(c)

        # números

        elif c.isdigit():

            self.tratar_numero()

        # identificadores

        elif c.isalpha() or c == '_':

            while (
                self.espiar().isalnum()
                or self.espiar() == '_'
            ):
                self.avancar()

            texto = self.codigo[
                self.inicio:self.atual
            ]

            if texto in self.reservadas:

                self.adicionar_token(
                    TipoToken.PALAVRA_RESERVADA
                )

            else:

                self.adicionar_token(
                    TipoToken.IDENTIFICADOR
                )

        # erro

        else:

            self.adicionar_token(
                TipoToken.ERRO
            )

    # ==========================================
    # LOOP PRINCIPAL
    # ==========================================

    def analisar(self):

        while not self.no_final():

            self.inicio = self.atual
            self.inicio_coluna = self.coluna

            self.escanear_token()

        self.tokens.append(

            Token(
                TipoToken.EOF,
                'EOF',
                self.linha,
                self.coluna
            )
        )

        return self.tokens


# ==========================================
# 4. PARSER
# ==========================================

class Parser:

    def __init__(self, tokens):

        self.tokens = tokens
        self.atual = 0
        self.erros = []

    # ==========================================
    # NAVEGAÇÃO
    # ==========================================

    def token_atual(self):

        return self.tokens[self.atual]

    def no_final(self):

        return (
            self.token_atual().tipo
            == TipoToken.EOF
        )

    def avancar(self):

        if not self.no_final():
            self.atual += 1

        return self.tokens[self.atual - 1]

    def verificar(self, lexema):

        if self.no_final():
            return False

        return (
            self.token_atual().lexema
            == lexema
        )

    def verificar_tipo(self, tipo):

        if self.no_final():
            return False

        return (
            self.token_atual().tipo
            == tipo
        )

    def consumir(self, lexema, mensagem):

        if self.verificar(lexema):
            return self.avancar()

        token = self.token_atual()

        raise Exception(

            f"[Linha {token.linha}] "
            f"Erro sintático: {mensagem}"
        )

    # ==========================================
    # LOOP PRINCIPAL
    # ==========================================

    def analisar(self):

        comandos = []

        while not self.no_final():

            try:

                resultado = self.declaracao()

                if resultado is not None:
                    comandos.append(resultado)

            except Exception as erro:

                self.erros.append(str(erro))

                self.avancar()

        return comandos

    # ==========================================
    # DECLARAÇÕES
    # ==========================================

    def declaracao(self):

        token = self.token_atual()

        # ignora delimitadores

        if (
            token.tipo
            == TipoToken.DELIMITADOR
        ):

            self.avancar()
            return None

        # erro léxico

        if (
            token.tipo
            == TipoToken.ERRO
        ):

            erro = (
                f"[Linha {token.linha}] "
                f"Erro léxico: {token.lexema}"
            )

            self.avancar()

            return ('ERRO', erro)

        # import

        if token.lexema == 'import':
            return self.declaracao_import()

        # from import

        if token.lexema == 'from':
            return self.declaracao_from()

        # class

        if token.lexema == 'class':
            return self.declaracao_class()

        # função

        if token.lexema == 'def':
            return self.declaracao_funcao()

        # return

        if token.lexema == 'return':

            self.avancar()

            valor = self.expressao()

            return (
                'RETURN',
                valor
            )

        # atribuição

        if (
            self.verificar_tipo(
                TipoToken.IDENTIFICADOR
            )

            and self.atual + 1 < len(self.tokens)

            and self.tokens[
                self.atual + 1
            ].lexema == '='
        ):

            return self.atribuicao()

        # expressão

        return self.expressao()

    # ==========================================
    # IMPORT
    # ==========================================

    def declaracao_import(self):

        self.consumir(
            'import',
            "Esperado 'import'"
        )

        modulo = self.avancar()

        return (
            'IMPORT',
            modulo.lexema
        )

    # ==========================================
    # FROM IMPORT
    # ==========================================

    def declaracao_from(self):

        self.consumir(
            'from',
            "Esperado 'from'"
        )

        origem = self.avancar()

        self.consumir(
            'import',
            "Esperado 'import'"
        )

        nome = self.avancar()

        return (
            'FROM_IMPORT',
            origem.lexema,
            nome.lexema
        )

    # ==========================================
    # CLASS
    # ==========================================

    def declaracao_class(self):

        self.consumir(
            'class',
            "Esperado 'class'"
        )

        nome = self.avancar()

        # ignora :

        if self.verificar(':'):
            self.avancar()

        return (
            'CLASS',
            nome.lexema
        )

    # ==========================================
    # FUNÇÃO
    # ==========================================

    def declaracao_funcao(self):

        self.consumir(
            'def',
            "Esperado 'def'"
        )

        nome = self.avancar()

        # ignora parâmetros

        if self.verificar('('):

            self.avancar()

            while (
                not self.verificar(')')
                and not self.no_final()
            ):
                self.avancar()

            self.consumir(
                ')',
                "Esperado ')'"
            )

        # ignora :

        if self.verificar(':'):
            self.avancar()

        return (
            'FUNCAO',
            nome.lexema
        )

    # ==========================================
    # ATRIBUIÇÃO
    # ==========================================

    def atribuicao(self):

        nome = self.avancar()

        self.consumir(
            '=',
            "Esperado '='"
        )

        valor = self.expressao()

        return (
            'ATRIBUICAO',
            nome.lexema,
            valor
        )

    # ==========================================
    # EXPRESSÃO
    # ==========================================

    def expressao(self):

        return self.termo()

    # ==========================================
    # TERMO
    # ==========================================

    def termo(self):

        expr = self.fator()

        while (
            self.verificar('+')
            or self.verificar('-')
        ):

            operador = self.avancar()

            direito = self.fator()

            expr = (

                'BINARIA',

                operador.lexema,

                expr,

                direito
            )

        return expr

    # ==========================================
    # FATOR
    # ==========================================

    def fator(self):

        expr = self.primario()

        while (
            self.verificar('*')
            or self.verificar('/')
        ):

            operador = self.avancar()

            direito = self.primario()

            expr = (

                'BINARIA',

                operador.lexema,

                expr,

                direito
            )

        return expr

    # ==========================================
    # PRIMÁRIO
    # ==========================================

    def primario(self):

        token = self.token_atual()

        # keyword

        if (
            token.tipo
            == TipoToken.PALAVRA_RESERVADA
        ):

            self.avancar()

            return (
                'KEYWORD',
                token.lexema
            )

        # número

        if (
            token.tipo
            == TipoToken.NUMERO
        ):

            self.avancar()

            return (
                'NUMERO',
                token.lexema
            )

        # string

        if (
            token.tipo
            == TipoToken.STRING
        ):

            self.avancar()

            return (
                'STRING',
                token.lexema
            )

        # variável

        if (
            token.tipo
            == TipoToken.IDENTIFICADOR
        ):

            self.avancar()

            return (
                'VARIAVEL',
                token.lexema
            )

        # agrupamento

        if token.lexema == '(':

            self.avancar()

            expr = self.expressao()

            self.consumir(
                ')',
                "Esperado ')'"
            )

            return expr

        raise Exception(

            f"[Linha {token.linha}] "
            f"Token inesperado: "
            f"{token.lexema}"
        )


# ==========================================
# 5. PROCESSAMENTO
# ==========================================

def processar(
    entrada,
    saida_tokens,
    saida_ast
):

    if not os.path.exists(entrada):

        print(
            "Arquivo não encontrado."
        )

        return

    with open(
        entrada,
        'r',
        encoding='utf-8'
    ) as f:

        codigo = f.read()

    # ==========================================
    # LEXER
    # ==========================================

    lexer = AnalisadorLexico(codigo)

    tokens = lexer.analisar()

    # ==========================================
    # SALVAR TOKENS
    # ==========================================

    with open(
        saida_tokens,
        'w',
        encoding='utf-8'
    ) as f:

        f.write(

            f"{'LINHA':<6} | "
            f"{'COL':<4} | "
            f"{'CATEGORIA':<20} | "
            f"{'LEXEMA'}\n"
        )

        f.write(
            "-" * 70 + "\n"
        )

        for t in tokens:

            f.write(

                f"{t.linha:<6} | "
                f"{t.coluna:<4} | "
                f"{t.tipo.value:<20} | "
                f"{t.lexema}\n"
            )

    # ==========================================
    # PARSER
    # ==========================================

    parser = Parser(tokens)

    ast = parser.analisar()

    # ==========================================
    # SALVAR AST
    # ==========================================

    with open(
        saida_ast,
        'w',
        encoding='utf-8'
    ) as f:

        f.write(
            "ÁRVORE SINTÁTICA:\n\n"
        )

        for item in ast:

            f.write(
                str(item) + "\n"
            )

        # erros

        if parser.erros:

            f.write(
                "\n\nERROS:\n\n"
            )

            for erro in parser.erros:

                f.write(
                    erro + "\n"
                )

    print(
        "Análise concluída."
    )


# ==========================================
# EXECUÇÃO
# ==========================================

if __name__ == "__main__":

    processar(
        'teste.py',
        'saida_tokens.txt',
        'saida_ast.txt'
    )