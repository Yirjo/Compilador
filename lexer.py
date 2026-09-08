# lexer.py
import re

REGLAS = [
    ('PALABRA_CLAVE', r'\b(def|return|public|int)\b'),
    ('CADENA',        r'"[^"]*"'),
    ('NUMERO',        r'\d+'),
    ('OP_ARIT',       r'[+\-*/]'),
    ('ID',            r'[A-Za-z_][A-Za-z0-9_]*'),
    ('ASIGNACION',    r'='),
    ('PARENTESIS_IZQ',r'\('),
    ('PARENTESIS_DER',r'\)'),
    ('LLAVE_IZQ',     r'\{'),
    ('LLAVE_DER',     r'\}'),
    ('COMA',          r','),
    ('DOS_PUNTOS',    r':'),
    ('PUNTO_COMA',    r';'),
    ('NUEVA_LINEA',   r'\n'),
    ('ESPACIOS',      r'[ \t]+'),
    ('MISMATCH',      r'.'),
]

def analizar_codigo(codigo_fuente):
    tokens = []
    linea_actual = 1
    regex_unido = '|'.join(f'(?P<{nombre}>{patron})' for nombre, patron in REGLAS)
    
    for coincidencia in re.finditer(regex_unido, codigo_fuente):
        tipo = coincidencia.lastgroup
        valor = coincidencia.group()
        
        if tipo == 'NUEVA_LINEA':
            linea_actual += 1
            continue
        elif tipo == 'ESPACIOS':
            continue
        elif tipo == 'MISMATCH':
            print(f"❌ Error Léxico: Carácter inesperado '{valor}' en la línea {linea_actual}")
            return None
            
        tokens.append({'tipo': tipo, 'valor': valor, 'linea': linea_actual})
    return tokens