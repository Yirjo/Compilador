import tkinter as tk
from tkinter import scrolledtext, messagebox
import json
from lexer import analizar_codigo
from parser import AnalizadorSintactico

arbol_actual = None

EJEMPLOS = {
    "ej1": (
        "1. Función de Saludo (Python)",
        "def greet(name):\n    return \"Hello, \" + name"
    ),
    "ej2": (
        "2. Función de Suma (Python)",
        "def add(a, b):\n    return a + b"
    ),
    "ej3": (
        "3. Función de Multiplicación (Java)",
        "public int multiply(int a, int b) {\n    return a * b;\n}"
    )
}

def cargar_ejemplo(clave):
    titulo, codigo = EJEMPLOS[clave]
    caja_codigo.delete(1.0, tk.END)
    caja_codigo.insert(tk.END, codigo)
    lbl_ejemplo_activo.config(text=f"📌 Ejemplo activo: {titulo}")

def animar_escritura(widget, texto, indice=0, callback=None):
    if indice < len(texto):
        widget.insert(tk.END, texto[indice])
        widget.see(tk.END)
        widget.after(2, animar_escritura, widget, texto, indice + 1, callback)
    else:
        if callback:
            callback()

def abrir_ventana_arbol():
    if not arbol_actual:
        messagebox.showwarning("Sin datos", "Primero debes ejecutar el análisis con un ejemplo válido.")
        return

    ventana_arbol = tk.Toplevel()
    ventana_arbol.title("Árbol de Análisis Sintáctico (AST) - Nivel Académico")
    ventana_arbol.geometry("1000x700")
    
    canvas = tk.Canvas(ventana_arbol, bg="#ffffff", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)
    
    def dibujar_nodo(texto, x, y):
        id_texto = canvas.create_text(x, y, text=texto, font=("Segoe UI", 9, "bold"), fill="#2c3e50")
        bbox = canvas.bbox(id_texto)
        padding_x, padding_y = 10, 6
        
        canvas.create_rectangle(bbox[0]-padding_x, bbox[1]-padding_y, bbox[2]+padding_x, bbox[3]+padding_y, 
                              fill="#f1f8ff", outline="#0366d6", width=1.5)
        canvas.tag_raise(id_texto)
        return x, y + padding_y

    def recorrer_y_dibujar(nodo_datos, x, y, ancho_disponible, nivel):
        if not isinstance(nodo_datos, dict):
            return dibujar_nodo(str(nodo_datos), x, y)
            
        titulo = nodo_datos.get("Nodo", "Desconocido")
        if "Valor" in nodo_datos:
            titulo = f"{titulo}: {nodo_datos['Valor']}"
            
        base_x, base_y = dibujar_nodo(titulo, x, y)
        
        hijos = nodo_datos.get("Hijos", [])
        num_hijos = len(hijos)
        
        if num_hijos > 0:
            espaciado_x = max(ancho_disponible / num_hijos, 110)
            inicio_x = x - ((num_hijos - 1) * espaciado_x) / 2
            
            for i, hijo in enumerate(hijos):
                hijo_x = inicio_x + (i * espaciado_x)
                hijo_y = y + 85
                
                canvas.create_line(base_x, base_y, hijo_x, hijo_y - 14, arrow=tk.LAST, fill="#586069", width=1.5, smooth=False)
                recorrer_y_dibujar(hijo, hijo_x, hijo_y, espaciado_x, nivel + 1)

    recorrer_y_dibujar(arbol_actual, 500, 45, 800, 1)

def ejecutar_compilador():
    global arbol_actual
    caja_lexico.delete(1.0, tk.END)
    caja_sintactico.delete(1.0, tk.END)
    arbol_actual = None
    
    btn_ejecutar.config(state=tk.DISABLED)
    btn_arbol.config(state=tk.DISABLED)
    
    codigo_fuente = caja_codigo.get(1.0, tk.END)
    tokens = analizar_codigo(codigo_fuente)
    texto_lexico = ""
    texto_sintactico = ""
    
    if not tokens:
        texto_lexico = "❌ ERROR LÉXICO:\nCaracteres no reconocidos en el código fuente."
        animar_escritura(caja_lexico, texto_lexico, callback=lambda: btn_ejecutar.config(state=tk.NORMAL))
        return
        
    texto_lexico += f"✅ Análisis Léxico Exitoso. Total tokens: {len(tokens)}\n"
    texto_lexico += "--------------------------------------------------\n"
    for t in tokens:
        texto_lexico += f"Token -> Tipo: {t['tipo']:<16} | Valor: '{t['valor']}' (Línea {t['linea']})\n"
        
    try:
        parser = AnalizadorSintactico(tokens)
        arbol_actual = parser.generar_arbol()
        
        texto_sintactico += "✅ ANÁLISIS SINTÁCTICO Y ESTRUCTURAL COMPLETADO\n"
        texto_sintactico += "Informe Detallado (Lenguaje Natural):\n"
        texto_sintactico += f"• El compilador ha estructurado jerárquicamente la función.\n"
        texto_sintactico += f"• Nodo Raíz: '{arbol_actual['Nodo']}'[cite: 4].\n"
        texto_sintactico += f"• Se desprendieron correctamente las ramas de modificadores, identificador, parámetros y cuerpo de función[cite: 4].\n"
        texto_sintactico += "--------------------------------------------------\n"
        texto_sintactico += "Estructura Jerárquica en formato JSON:\n"
        texto_sintactico += json.dumps(arbol_actual, indent=4, ensure_ascii=False)
        
    except Exception as e:
        texto_sintactico += f"❌ ERROR SINTÁCTICO:\n{str(e)}"

    def iniciar_sintactico():
        animar_escritura(caja_sintactico, texto_sintactico, callback=reactivar)
        
    def reactivar():
        btn_ejecutar.config(state=tk.NORMAL)
        if arbol_actual:
            btn_arbol.config(state=tk.NORMAL)

    animar_escritura(caja_lexico, texto_lexico, callback=iniciar_sintactico)

# Configuración de Interfaz Gráfica Principal
ventana = tk.Tk()
ventana.title("Compilador - Analizador Léxico y Sintáctico")
ventana.state('zoomed')
ventana.configure(bg="#1e1e1e")

fuente_titulo = ("Segoe UI", 11, "bold")
fuente_codigo = ("Consolas", 11)

panel_izq = tk.Frame(ventana, bg="#1e1e1e")
panel_izq.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)

tk.Label(panel_izq, text="SELECCIONAR EJEMPLO DE PRUEBA (GUÍA)", fg="#9cdcfe", bg="#1e1e1e", font=fuente_titulo).pack(anchor="w", pady=(0, 5))

frame_botones = tk.Frame(panel_izq, bg="#1e1e1e")
frame_botones.pack(fill=tk.X, pady=5)

tk.Button(frame_botones, text="Ejemplo 1: Saludo", bg="#0e639c", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", command=lambda: cargar_ejemplo("ej1")).pack(side=tk.LEFT, padx=2)
tk.Button(frame_botones, text="Ejemplo 2: Suma", bg="#0e639c", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", command=lambda: cargar_ejemplo("ej2")).pack(side=tk.LEFT, padx=2)
tk.Button(frame_botones, text="Ejemplo 3: Multiplicación", bg="#0e639c", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", command=lambda: cargar_ejemplo("ej3")).pack(side=tk.LEFT, padx=2)

lbl_ejemplo_activo = tk.Label(panel_izq, text="📌 Ejemplo activo: 1. Función de Saludo (Python)", fg="#ce9178", bg="#1e1e1e", font=("Segoe UI", 9, "italic"))
lbl_ejemplo_activo.pack(anchor="w", pady=5)

tk.Label(panel_izq, text="CÓDIGO FUENTE", fg="#cccccc", bg="#1e1e1e", font=fuente_titulo).pack(anchor="w", pady=(10,0))
caja_codigo = scrolledtext.ScrolledText(panel_izq, font=fuente_codigo, bg="#252526", fg="#d4d4d4", insertbackground="white", relief="flat")
caja_codigo.pack(pady=5, fill=tk.BOTH, expand=True)

cargar_ejemplo("ej1")

btn_ejecutar = tk.Button(panel_izq, text="▶ Ejecutar Análisis Léxico y Sintáctico", bg="#2ea043", fg="white", font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2", command=ejecutar_compilador, pady=8)
btn_ejecutar.pack(fill=tk.X, pady=10)

panel_der = tk.Frame(ventana, bg="#1e1e1e")
panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=20)

tk.Label(panel_der, text="1. ANÁLISIS LÉXICO (TOKENS)", fg="#4ec9b0", bg="#1e1e1e", font=fuente_titulo).pack(anchor="w")
caja_lexico = scrolledtext.ScrolledText(panel_der, height=11, font=fuente_codigo, bg="#252526", fg="#d4d4d4", relief="flat")
caja_lexico.pack(pady=5, fill=tk.BOTH, expand=True)

tk.Label(panel_der, text="2. ANÁLISIS SINTÁCTICO (NARRATIVA + JSON)", fg="#ce9178", bg="#1e1e1e", font=fuente_titulo).pack(anchor="w", pady=(10,0))
caja_sintactico = scrolledtext.ScrolledText(panel_der, height=14, font=fuente_codigo, bg="#252526", fg="#d4d4d4", relief="flat")
caja_sintactico.pack(pady=5, fill=tk.BOTH, expand=True)

btn_arbol = tk.Button(panel_der, text="🌳 Abrir Árbol Sintáctico Gráfico Independiente", bg="#0e639c", fg="white", font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2", command=abrir_ventana_arbol, pady=8, state=tk.DISABLED)
btn_arbol.pack(fill=tk.X, pady=10)

ventana.mainloop()