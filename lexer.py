# lexer.py
import re
from typing import List, Dict, Optional, Tuple, Set

REGEX_REGLAS = [
    ('CADENA',        r'"[^"]*"'),
    ('OP_ARIT',       r'[+\-*/]'),
    ('ASIGNACION',    r'='),
    ('PARENTESIS_IZQ',r'\('),
    ('PARENTESIS_DER',r'\)'),
    ('LLAVE_IZQ',     r'\{'),
    ('LLAVE_DER',     r'\}'),
    ('COMA',          r','),
    ('DOS_PUNTOS',    r':'),
    ('PUNTO_COMA',    r';'),
]


class AFD:
    """Autómata Finito Determinista genérico."""
    
    def __init__(self, nombre: str, estados: Set[str], alfabeto: Set[str], 
                 transiciones: Dict[Tuple[str, str], str], estado_inicial: str, 
                 estados_aceptacion: Set[str], estado_trampa: Optional[str] = "qd"):
        self.nombre = nombre
        self.estados = estados
        self.alfabeto = alfabeto
        self.transiciones = transiciones
        self.estado_inicial = estado_inicial
        self.estados_aceptacion = estados_aceptacion
        self.estado_trampa = estado_trampa
    
    def procesar(self, cadena: str) -> Tuple[bool, List[Dict]]:
        """Procesa una cadena y retorna (aceptado, traza_estados)."""
        estado_actual = self.estado_inicial
        traza = [{'estado': estado_actual, 'caracter': '', 'es_inicial': True}]
        
        for i, char in enumerate(cadena):
            clave = (estado_actual, char)
            if char not in self.alfabeto or clave not in self.transiciones:
                estado_siguiente = self.estado_trampa if self.estado_trampa else 'RECHAZO'
                traza.append({
                    'estado': estado_siguiente,
                    'caracter': char,
                    'posicion': i,
                    'error': f"Transición no válida δ({estado_actual}, '{char}') -> {estado_siguiente}"
                })
                estado_actual = estado_siguiente
                break
            
            estado_actual = self.transiciones[clave]
            traza.append({
                'estado': estado_actual,
                'caracter': char,
                'posicion': i
            })
            if estado_actual == self.estado_trampa:
                break
        
        aceptado = estado_actual in self.estados_aceptacion
        return aceptado, traza
    
    def obtener_tabla_transiciones(self) -> List[Dict]:
        """Retorna la tabla de transiciones completa (incluye transiciones a trampa)."""
        tabla = []
        for (origen, simbolo), destino in sorted(self.transiciones.items()):
            tabla.append({
                'origen': origen,
                'simbolo': simbolo,
                'destino': destino,
                'es_aceptacion': destino in self.estados_aceptacion,
                'es_inicial': origen == self.estado_inicial
            })
        return tabla

    def obtener_tabla_transiciones_limpia(self) -> List[Dict]:
        """
        Retorna tabla de transiciones agrupando transiciones a estado trampa.
        Solo muestra transiciones válidas específicas y una fila [Otros] -> qd por estado origen.
        """
        if not self.estado_trampa:
            return self.obtener_tabla_transiciones()
        
        # Agrupar transiciones por estado origen
        trans_por_origen = {}
        for (origen, simbolo), destino in self.transiciones.items():
            if origen not in trans_por_origen:
                trans_por_origen[origen] = {'validas': [], 'a_trampa': set()}
            if destino == self.estado_trampa:
                trans_por_origen[origen]['a_trampa'].add(simbolo)
            else:
                trans_por_origen[origen]['validas'].append((simbolo, destino))
        
        tabla = []
        for origen in sorted(trans_por_origen.keys()):
            # Transiciones válidas específicas
            for simbolo, destino in sorted(trans_por_origen[origen]['validas']):
                tabla.append({
                    'origen': origen,
                    'simbolo': simbolo,
                    'destino': destino,
                    'es_aceptacion': destino in self.estados_aceptacion,
                    'es_inicial': origen == self.estado_inicial
                })
            
            # Una sola fila para "Otros caracteres" -> trampa
            if trans_por_origen[origen]['a_trampa']:
                tabla.append({
                    'origen': origen,
                    'simbolo': '[Otros caracteres]',
                    'destino': self.estado_trampa,
                    'es_aceptacion': False,
                    'es_inicial': origen == self.estado_inicial
                })
        
        return tabla


# --- RETO 1: AFD Palabra Reservada "if" ---
def crear_afd_if() -> AFD:
    """
    Reto 1: AFD para la palabra reservada 'if'.
    Estados: q0 (inicial), q1 (leyó 'i'), q2 (leyó 'f', aceptación), qd (trampa).
    """
    estados = {'q0', 'q1', 'q2', 'qd'}
    alfabeto = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_')
    transiciones = {}
    
    # Transiciones desde q0
    transiciones[('q0', 'i')] = 'q1'
    for c in alfabeto:
        if c != 'i':
            transiciones[('q0', c)] = 'qd'
            
    # Transiciones desde q1
    transiciones[('q1', 'f')] = 'q2'
    for c in alfabeto:
        if c != 'f':
            transiciones[('q1', c)] = 'qd'
            
    # Transiciones desde q2 y qd (trampa)
    for c in alfabeto:
        transiciones[('q2', c)] = 'qd'
        transiciones[('qd', c)] = 'qd'
        
    return AFD(
        nombre="AFD Palabra Reservada 'if'",
        estados=estados,
        alfabeto=alfabeto,
        transiciones=transiciones,
        estado_inicial='q0',
        estados_aceptacion={'q2'},
        estado_trampa='qd'
    )


# --- RETO 3: AFD Identificador MiniCode ([ab][ab01]*) ---
def crear_afd_identificador_minicode() -> AFD:
    """
    Reto 3: AFD para Identificadores en MiniCode.
    Regla estricta: Debe comenzar con 'a' o 'b', seguido solo por 'a', 'b', '0', '1'.
    """
    estados = {'q0', 'q1', 'qd'}
    alfabeto = set('ab01')
    transiciones = {}
    
    # Desde q0 sólo 'a' o 'b' van a q1
    transiciones[('q0', 'a')] = 'q1'
    transiciones[('q0', 'b')] = 'q1'
    transiciones[('q0', '0')] = 'qd'
    transiciones[('q0', '1')] = 'qd'
    
    # Desde q1 cualquier carácter en {a,b,0,1} se mantiene en q1
    for c in 'ab01':
        transiciones[('q1', c)] = 'q1'
        transiciones[('qd', c)] = 'qd'
        
    return AFD(
        nombre="AFD Identificador MiniCode",
        estados=estados,
        alfabeto=alfabeto,
        transiciones=transiciones,
        estado_inicial='q0',
        estados_aceptacion={'q1'},
        estado_trampa='qd'
    )


# --- RETO 2: AFD Cadenas Binarias que terminan en "01" ---
def crear_afd_binario_01() -> AFD:
    """
    Reto 2: AFD para cadenas binarias que terminan exactamente en '01'.
    """
    estados = {'q0', 'q1', 'q2', 'qd'}
    alfabeto = {'0', '1'}
    transiciones = {
        ('q0', '0'): 'q1',
        ('q0', '1'): 'q0',
        ('q1', '0'): 'q1',
        ('q1', '1'): 'q2',  # Aceptación (termina en 01)
        ('q2', '0'): 'q1',
        ('q2', '1'): 'q0',
    }
    return AFD(
        nombre="AFD Binario terminado en 01",
        estados=estados,
        alfabeto=alfabeto,
        transiciones=transiciones,
        estado_inicial='q0',
        estados_aceptacion={'q2'},
        estado_trampa='qd'
    )


# --- RETO 4: AFD Cadenas Binarias que contienen "00" o "11" ---
def crear_afd_binario_00_11() -> AFD:
    """
    Reto 4: AFD para cadenas binarias que contienen '00' o '11'.
    """
    estados = {'q0', 'q1', 'q2', 'q3', 'qd'}
    alfabeto = {'0', '1'}
    transiciones = {
        ('q0', '0'): 'q1',  # Leyó 0
        ('q0', '1'): 'q2',  # Leyó 1
        ('q1', '0'): 'q3',  # Leyó 00 -> Aceptación
        ('q1', '1'): 'q2',  # Vuelve a buscar 11
        ('q2', '0'): 'q1',  # Vuelve a buscar 00
        ('q2', '1'): 'q3',  # Leyó 11 -> Aceptación
        ('q3', '0'): 'q3',  # Permanece en aceptación
        ('q3', '1'): 'q3',  # Permanece en aceptación
    }
    return AFD(
        nombre="AFD Binario contiene 00 o 11",
        estados=estados,
        alfabeto=alfabeto,
        transiciones=transiciones,
        estado_inicial='q0',
        estados_aceptacion={'q3'},
        estado_trampa='qd'
    )


# Instancias globales de los 4 AFDs
AFD_IF = crear_afd_if()
AFD_ID_MINICODE = crear_afd_identificador_minicode()
AFD_BIN_01 = crear_afd_binario_01()
AFD_BIN_00_11 = crear_afd_binario_00_11()


def analizar_con_afd(codigo_fuente: str) -> Tuple[List[Dict], Dict[str, List[Dict]]]:
    """
    Analiza el código usando los 4 AFDs requeridos para la práctica MiniCode.
    """
    tokens = []
    trazas_afd = {
        'if': [],
        'identificador': [],
        'binario_01': [],
        'binario_00_11': []
    }
    linea_actual = 1
    pos = 0
    largo = len(codigo_fuente)
    
    while pos < largo:
        char = codigo_fuente[pos]
        
        if char == '\n':
            linea_actual += 1
            pos += 1
            continue
        elif char in ' \t\r':
            pos += 1
            continue
        
        # Probar token IF
        if codigo_fuente[pos:pos+2] == 'if' and (pos+2 == largo or not codigo_fuente[pos+2].isalnum()):
            lexema = 'if'
            aceptado, traza = AFD_IF.procesar(lexema)
            trazas_afd['if'].append({'lexema': lexema, 'aceptado': aceptado, 'traza': traza, 'linea': linea_actual})
            tokens.append({'tipo': 'IF', 'valor': lexema, 'linea': linea_actual})
            pos += 2
            continue
        
        # Probar Identificador MiniCode ([ab][ab01]*)
        if char in ('a', 'b'):
            inicio = pos
            while pos < largo and codigo_fuente[pos] in ('a', 'b', '0', '1'):
                pos += 1
            lexema = codigo_fuente[inicio:pos]
            
            # Verificar con AFD
            aceptado, traza = AFD_ID_MINICODE.procesar(lexema)
            trazas_afd['identificador'].append({'lexema': lexema, 'aceptado': aceptado, 'traza': traza, 'linea': linea_actual})
            tokens.append({'tipo': 'ID', 'valor': lexema, 'linea': linea_actual})
            continue
            
        # Números y cadenas binarias: consumir la secuencia completa de dígitos
        if char.isdigit():
            inicio = pos
            while pos < largo and codigo_fuente[pos].isdigit():
                pos += 1
            lexema = codigo_fuente[inicio:pos]

            # Solo es candidato binario si todos sus dígitos son 0 o 1
            if all(d in ('0', '1') for d in lexema):
                es_01, traza_01 = AFD_BIN_01.procesar(lexema)
                es_00_11, traza_00_11 = AFD_BIN_00_11.procesar(lexema)

                if es_01:
                    trazas_afd['binario_01'].append({'lexema': lexema, 'aceptado': True, 'traza': traza_01, 'linea': linea_actual})
                    tokens.append({'tipo': 'BINARIO_01', 'valor': lexema, 'linea': linea_actual})
                    continue
                if es_00_11:
                    trazas_afd['binario_00_11'].append({'lexema': lexema, 'aceptado': True, 'traza': traza_00_11, 'linea': linea_actual})
                    tokens.append({'tipo': 'BINARIO_00_11', 'valor': lexema, 'linea': linea_actual})
                    continue

            tokens.append({'tipo': 'NUMERO', 'valor': lexema, 'linea': linea_actual})
            continue
        
        # Otros Tokens por RegEx (operadores, asignaciones, cadenas, etc.)
        coincidencia = None
        for nombre, patron in REGEX_REGLAS:
            match = re.match(patron, codigo_fuente[pos:])
            if match:
                coincidencia = (nombre, match.group())
                break
        
        if coincidencia:
            tipo, valor = coincidencia
            tokens.append({'tipo': tipo, 'valor': valor, 'linea': linea_actual})
            pos += len(valor)
        else:
            tokens.append({'tipo': 'MISMATCH', 'valor': char, 'linea': linea_actual})
            pos += 1
            
    return tokens, trazas_afd


def analizar_codigo(codigo_fuente: str) -> Optional[List[Dict]]:
    tokens, _ = analizar_con_afd(codigo_fuente)
    return tokens


def obtener_afds() -> Dict[str, AFD]:
    return {
        'if': AFD_IF,
        'identificador': AFD_ID_MINICODE,
        'binario_01': AFD_BIN_01,
        'binario_00_11': AFD_BIN_00_11
    }
