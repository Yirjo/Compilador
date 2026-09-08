# parser.py
class AnalizadorSintactico:
    def __init__(self, tokens):
        self.tokens = tokens
        self.posicion = 0

    def token_actual(self):
        if self.posicion < len(self.tokens):
            return self.tokens[self.posicion]
        return None

    def consumir(self, tipo_esperado):
        token = self.token_actual()
        if token and token['tipo'] == tipo_esperado:
            self.posicion += 1
            return token
        return None

    def generar_arbol(self):
        t = self.token_actual()
        if not t:
            return {"Nodo": "Programa", "Hijos": []}
            
        if t['valor'] in ('def', 'public'):
            return self.parsear_definicion_funcion()
        
        return {"Nodo": "Programa", "Hijos": [{"Nodo": "Instrucción", "Valor": t['valor']}]}

    def parsear_definicion_funcion(self):
        modificadores = []
        while self.token_actual() and self.token_actual()['tipo'] in ('PALABRA_CLAVE', 'ID'):
            tok = self.token_actual()
            if tok['valor'] in ('def', 'public', 'int', 'void', 'boolean'):
                modificadores.append(tok['valor'])
                self.posicion += 1
            else:
                break
                
        id_func = self.consumir('ID')
        nombre_func = id_func['valor'] if id_func else "desconocida"
        
        self.consumir('PARENTESIS_IZQ')
        lista_params = []
        while self.token_actual() and self.token_actual()['tipo'] != 'PARENTESIS_DER':
            tok = self.token_actual()
            if tok['tipo'] != 'COMA':
                lista_params.append(tok['valor'])
            self.posicion += 1
        self.consumir('PARENTESIS_DER')
        
        if self.token_actual() and self.token_actual()['tipo'] in ('DOS_PUNTOS', 'LLAVE_IZQ'):
            self.posicion += 1
            
        cuerpo = []
        while self.token_actual() and self.token_actual()['tipo'] != 'LLAVE_DER':
            tok = self.token_actual()
            if tok and tok['valor'] == 'return':
                self.posicion += 1
                expr = self.parsear_expresion()
                cuerpo.append({
                    "Nodo": "Proposición de Retorno",
                    "Hijos": [expr]
                })
            else:
                self.posicion += 1
                
        if self.token_actual() and self.token_actual()['valor'] == '}':
            self.posicion += 1

        return {
            "Nodo": "Definición de Función",
            "Hijos": [
                {
                    "Nodo": "Modifiers & Type" if "public" in modificadores else "Modificador",
                    "Hijos": [{"Nodo": "Token", "Valor": " ".join(modificadores)}]
                },
                {
                    "Nodo": "Identificador",
                    "Hijos": [{"Nodo": "Nombre", "Valor": nombre_func}]
                },
                {
                    "Nodo": "Parámetros",
                    "Hijos": [{"Nodo": "Param", "Valor": p} for p in lista_params]
                },
                {
                    "Nodo": "Cuerpo de Función",
                    "Hijos": cuerpo if cuerpo else [{"Nodo": "BloqueVacio"}]
                }
            ]
        }

    def parsear_expresion(self):
        izq = self.token_actual()
        if izq:
            self.posicion += 1
            
        op = self.token_actual()
        if op and op['tipo'] == 'OP_ARIT':
            self.posicion += 1
            der = self.token_actual()
            if der:
                self.posicion += 1
            return {
                "Nodo": "Expresión",
                "Hijos": [
                    {"Nodo": "Identificador", "Valor": izq['valor'] if izq else ""},
                    {"Nodo": "Operador", "Valor": op['valor']},
                    {"Nodo": "Identificador", "Valor": der['valor'] if der else ""}
                ]
            }
        return {
            "Nodo": "Expresión",
            "Hijos": [{"Nodo": "Valor", "Valor": izq['valor'] if izq else ""}]
        }