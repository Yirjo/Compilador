# main.py
import json
from lexer import analizar_codigo
from parser import AnalizadorSintactico

def probar_compilador():
    # Prueba enfocada en la secuencia básica para visualizar el árbol
    codigo_prueba = """
    x = 10 + 5
    print(x)
    """

    print("=== INICIANDO COMPILADOR MINILANG ===")
    print(f"Código fuente:{codigo_prueba}")
    
    # 1. FASE LÉXICA
    print("\n--- FASE 1: ANÁLISIS LÉXICO ---")
    tokens = analizar_codigo(codigo_prueba)
    
    if tokens:
        for token in tokens:
            print(f"  {token}")
            
        # 2. FASE SINTÁCTICA (Generación del Árbol)
        print("\n--- FASE 2: ANÁLISIS SINTÁCTICO (AST) ---")
        try:
            parser = AnalizadorSintactico(tokens)
            arbol_sintactico = parser.generar_arbol()
            
            # Imprimimos el árbol con formato JSON para que se vea estructurado
            print(json.dumps(arbol_sintactico, indent=4, ensure_ascii=False))
        except Exception as e:
            print(e)

if __name__ == '__main__':
    probar_compilador()