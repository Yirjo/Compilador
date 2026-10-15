# parser.py
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class NodoParseTree:
    """Nodo del Árbol de Derivación (Parse Tree)."""
    simbolo: str
    es_terminal: bool = False
    valor: Optional[str] = None
    hijos: List['NodoParseTree'] = field(default_factory=list)
    regla_aplicada: Optional[str] = None

    def to_dict(self) -> Dict:
        resultado = {"simbolo": self.simbolo, "es_terminal": self.es_terminal}
        if self.valor is not None:
            resultado["valor"] = self.valor
        if self.regla_aplicada:
            resultado["regla"] = self.regla_aplicada
        if self.hijos:
            resultado["hijos"] = [h.to_dict() for h in self.hijos]
        return resultado


class AnalizadorSintactico:
    """
    Parser descendente recursivo para MiniCode.
    Genera simultáneamente el AST (resumido) y el Árbol de Derivación (completo).
    Maneja precedencia de operadores (*, / antes que +, -) y paréntesis.
    """

    GRAMATICA = {
        'Programa':       'Programa → ListaSentencias',
        'ListaSentencias':'ListaSentencias → Sentencia ListaSentencias | ε',
        'Sentencia':      'Sentencia → IfStmt | Asignacion | ExpresionStmt',
        'IfStmt':         'IfStmt → "if" Expresion',
        'Asignacion':     'Asignacion → ID "=" Expresion',
        'ExpresionStmt':  'ExpresionStmt → Expresion',
        'Expresion':      'Expresion → Termino { ("+" | "-") Termino }',
        'Termino':        'Termino → Factor { ("*" | "/") Factor }',
        'Factor':         'Factor → NUM | BIN_01 | BIN_00_11 | ID | "(" Expresion ")"',
    }

    TIPOS_LITERAL = ('NUMERO', 'BINARIO_01', 'BINARIO_00_11')

    def __init__(self, tokens: List[Dict]):
        self.tokens = tokens
        self.posicion = 0
        self.errores: List[str] = []
        self.parse_tree_root: Optional[NodoParseTree] = None

    def token_actual(self) -> Optional[Dict]:
        return self.tokens[self.posicion] if self.posicion < len(self.tokens) else None

    def consumir(self, tipo_esperado: str) -> Optional[Dict]:
        token = self.token_actual()
        if token and token['tipo'] == tipo_esperado:
            self.posicion += 1
            return token
        return None

    def consumir_valor(self, valor_esperado: str) -> Optional[Dict]:
        token = self.token_actual()
        if token and token['valor'] == valor_esperado:
            self.posicion += 1
            return token
        return None

    def error(self, mensaje: str):
        token = self.token_actual()
        linea = token['linea'] if token else 'EOF'
        self.errores.append(f"Línea {linea}: {mensaje}")

    # ------------------------------------------------------------------
    # ENTRADA PRINCIPAL
    # ------------------------------------------------------------------
    def parsear(self) -> Tuple[Optional[Dict], Optional[Dict], List[str]]:
        self.posicion = 0
        self.errores = []
        ast = self.parsear_programa()
        pt = self.parse_tree_root.to_dict() if self.parse_tree_root else None
        return ast, pt, self.errores

    def parsear_programa(self) -> Dict:
        nodo_pt = NodoParseTree("Programa", regla_aplicada=self.GRAMATICA['Programa'])
        self.parse_tree_root = nodo_pt

        sentencias_ast = []
        sentencias_pt = []

        while self.token_actual():
            tok = self.token_actual()
            if tok['tipo'] == 'MISMATCH':
                self.error(f"Token no reconocido: '{tok['valor']}'")
                self.posicion += 1
                continue

            s_ast, s_pt = self.parsear_sentencia()
            if s_ast is not None:
                sentencias_ast.append(s_ast)
            if s_pt is not None:
                sentencias_pt.append(s_pt)

        nodo_pt.hijos = sentencias_pt
        return {"Nodo": "Programa", "Hijos": sentencias_ast}

    # ------------------------------------------------------------------
    # SENTENCIAS
    # ------------------------------------------------------------------
    def parsear_sentencia(self) -> Tuple[Optional[Dict], Optional[NodoParseTree]]:
        tok = self.token_actual()
        if not tok:
            return None, None

        if tok['tipo'] == 'IF':
            return self.parsear_if()
        if tok['tipo'] == 'ID':
            return self.parsear_asignacion()
        # Expresión suelta
        return self.parsear_expresion_stmt()

    def parsear_if(self) -> Tuple[Optional[Dict], Optional[NodoParseTree]]:
        nodo_pt = NodoParseTree("IfStmt", regla_aplicada=self.GRAMATICA['IfStmt'])
        self.posicion += 1  # consume 'if'
        nodo_pt.hijos.append(NodoParseTree("if", es_terminal=True, valor="if"))

        expr_ast, expr_pt = self.parsear_expresion()
        if expr_pt:
            nodo_pt.hijos.append(expr_pt)

        return {"Nodo": "IfStmt", "Condicion": expr_ast}, nodo_pt

    def parsear_asignacion(self) -> Tuple[Optional[Dict], Optional[NodoParseTree]]:
        nodo_pt = NodoParseTree("Asignacion", regla_aplicada=self.GRAMATICA['Asignacion'])

        id_tok = self.consumir('ID')
        id_pt = NodoParseTree("ID", es_terminal=True, valor=id_tok['valor'])
        nodo_pt.hijos.append(id_pt)

        self.consumir('ASIGNACION')
        nodo_pt.hijos.append(NodoParseTree("=", es_terminal=True, valor="="))

        expr_ast, expr_pt = self.parsear_expresion()
        if expr_pt:
            nodo_pt.hijos.append(expr_pt)

        self.consumir('PUNTO_COMA')  # opcional

        ast = {
            "Nodo": "Asignacion",
            "Variable": id_tok['valor'],
            "Expresion": expr_ast
        }
        return ast, nodo_pt

    def parsear_expresion_stmt(self) -> Tuple[Optional[Dict], Optional[NodoParseTree]]:
        nodo_pt = NodoParseTree("ExpresionStmt", regla_aplicada=self.GRAMATICA['ExpresionStmt'])
        expr_ast, expr_pt = self.parsear_expresion()
        if expr_pt:
            nodo_pt.hijos.append(expr_pt)
        self.consumir('PUNTO_COMA')
        return expr_ast, nodo_pt

    # ------------------------------------------------------------------
    # EXPRESIONES CON PRECEDENCIA
    # ------------------------------------------------------------------
    def parsear_expresion(self) -> Tuple[Optional[Dict], Optional[NodoParseTree]]:
        """Expresion → Termino { ('+' | '-') Termino }"""
        nodo_pt = NodoParseTree("Expresion", regla_aplicada=self.GRAMATICA['Expresion'])

        acum_ast, term_pt = self.parsear_termino()
        if term_pt:
            nodo_pt.hijos.append(term_pt)

        while self.token_actual() and self.token_actual()['tipo'] == 'OP_ARIT' \
                and self.token_actual()['valor'] in ('+', '-'):
            op = self.token_actual()
            self.posicion += 1
            op_ast = {"Nodo": "Operador", "Valor": op['valor']}
            nodo_pt.hijos.append(NodoParseTree(op['valor'], es_terminal=True, valor=op['valor']))

            der_ast, der_pt = self.parsear_termino()
            if der_pt:
                nodo_pt.hijos.append(der_pt)

            if acum_ast is not None and der_ast is not None:
                acum_ast = {"Nodo": "BinOp", "Op": op['valor'],
                            "Izq": acum_ast, "Der": der_ast}
            elif der_ast is not None:
                acum_ast = der_ast

        return acum_ast, nodo_pt

    def parsear_termino(self) -> Tuple[Optional[Dict], Optional[NodoParseTree]]:
        """Termino → Factor { ('*' | '/') Factor }"""
        nodo_pt = NodoParseTree("Termino", regla_aplicada=self.GRAMATICA['Termino'])

        acum_ast, fact_pt = self.parsear_factor()
        if fact_pt:
            nodo_pt.hijos.append(fact_pt)

        while self.token_actual() and self.token_actual()['tipo'] == 'OP_ARIT' \
                and self.token_actual()['valor'] in ('*', '/'):
            op = self.token_actual()
            self.posicion += 1
            op_ast = {"Nodo": "Operador", "Valor": op['valor']}
            nodo_pt.hijos.append(NodoParseTree(op['valor'], es_terminal=True, valor=op['valor']))

            der_ast, der_pt = self.parsear_factor()
            if der_pt:
                nodo_pt.hijos.append(der_pt)

            if acum_ast is not None and der_ast is not None:
                acum_ast = {"Nodo": "BinOp", "Op": op['valor'],
                            "Izq": acum_ast, "Der": der_ast}
            elif der_ast is not None:
                acum_ast = der_ast

        return acum_ast, nodo_pt

    def parsear_factor(self) -> Tuple[Optional[Dict], Optional[NodoParseTree]]:
        """Factor → NUM | BIN | ID | '(' Expresion ')'"""
        tok = self.token_actual()
        if not tok:
            return None, None

        # Paréntesis
        if tok['tipo'] == 'PARENTESIS_IZQ' or tok['valor'] == '(':
            self.posicion += 1
            nodo_pt = NodoParseTree("Factor", regla_aplicada=self.GRAMATICA['Factor'] + "  [paréntesis]")
            nodo_pt.hijos.append(NodoParseTree("(", es_terminal=True, valor="("))

            expr_ast, expr_pt = self.parsear_expresion()
            if expr_pt:
                nodo_pt.hijos.append(expr_pt)

            if not (self.consumir_valor(')') or self.consumir('PARENTESIS_DER')):
                self.error("Se esperaba ')'")
            nodo_pt.hijos.append(NodoParseTree(")", es_terminal=True, valor=")"))

            return expr_ast, nodo_pt

        # Literales y identificadores
        if tok['tipo'] in self.TIPOS_LITERAL or tok['tipo'] == 'ID':
            self.posicion += 1
            regla = f"Factor → {tok['tipo']}"
            nodo_pt = NodoParseTree("Factor", regla_aplicada=regla)
            nodo_pt.hijos.append(NodoParseTree(tok['tipo'], es_terminal=True, valor=tok['valor']))

            nombre = "Numero" if tok['tipo'] == 'NUMERO' else \
                     ("Identificador" if tok['tipo'] == 'ID' else "Binario")
            ast = {"Nodo": nombre, "Tipo": tok['tipo'], "Valor": tok['valor']}
            return ast, nodo_pt

        # Token inesperado
        self.error(f"Factor inesperado: '{tok['valor']}'")
        self.posicion += 1
        return None, None


def generar_ast_json(ast: Optional[Dict]) -> str:
    return json.dumps(ast, indent=4, ensure_ascii=False)


def generar_parse_tree_json(pt: Optional[Dict]) -> str:
    return json.dumps(pt, indent=4, ensure_ascii=False)
