import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
from lexer import analizar_con_afd, obtener_afds
from parser import AnalizadorSintactico, generar_ast_json, generar_parse_tree_json

# ============================================================
# PALETA DE COLORES TEMA VS CODE OSCURO
# ============================================================
C_BG          = "#1e1e1e"   # Fondo principal
C_BG_PANEL    = "#252526"   # Fondo de paneles
C_BG_TAB      = "#2d2d2d"   # Fondo pestañas inactivas
C_BG_EDITOR   = "#1e1e1e"   # Fondo del editor
C_FG          = "#d4d4d4"   # Texto claro principal
C_FG_DIM      = "#808080"   # Texto atenuado
C_ACCENT      = "#0e639c"   # Azul VS Code
C_ACCENT_HOVER= "#1177bb"
C_GREEN       = "#2ea043"   # Botón ejecutar
C_CYAN        = "#4ec9b0"   # Tokens / títulos
C_ORANGE      = "#ce9178"   # Strings / AST
C_YELLOW      = "#dcdcaa"   # Parse tree
C_BLUE_LIGHT  = "#9cdcfe"   # Títulos
C_BORDER      = "#3c3c3c"   # Bordes

# Estado global del análisis
ast_actual = None
parse_tree_actual = None
trazas_afd_actuales = None

FUENTE_TITULO = ("Segoe UI", 10, "bold")
FUENTE_SUBTITULO = ("Segoe UI", 9, "bold")
FUENTE_CODIGO = ("Consolas", 10)
FUENTE_LABEL = ("Segoe UI", 8, "italic")

EJEMPLOS = {
    "ej1": ("Ejemplo 1 (Básico)", "if a01"),
    "ej2": ("Ejemplo 2 (Operaciones)", "b11 = a0 + a1\nif b11"),
    "ej3": ("Ejemplo 3 (Complejo)", "a0 = 10\nb1 = 20\na11 = a0 * (b1 + 10)"),
}


# ============================================================
# ESTILOS TTK (MODO OSCURO PROFUNDO)
# ============================================================
def configurar_estilos(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        style.theme_use("default")

    # --- TNotebook (pestañas) ---
    style.configure("TNotebook",
                    background=C_BG,
                    borderwidth=0,
                    tabmargins=[0, 0, 0, 0])
    style.configure("TNotebook.Tab",
                    background=C_BG_TAB,
                    foreground=C_FG_DIM,
                    padding=[14, 8],
                    font=("Segoe UI", 9, "bold"),
                    borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", C_BG_PANEL), ("active", "#3a3a3a")],
              foreground=[("selected", "#ffffff"), ("active", C_FG)])

    # --- Treeview (tablas de AFD) ---
    style.configure("Treeview",
                    background=C_BG_PANEL,
                    foreground=C_FG,
                    fieldbackground=C_BG_PANEL,
                    rowheight=24,
                    borderwidth=0,
                    font=("Consolas", 10))
    style.map("Treeview",
              background=[("selected", C_ACCENT)],
              foreground=[("selected", "#ffffff")])

    style.configure("Treeview.Heading",
                    background="#333333",
                    foreground="#ffffff",
                    relief="flat",
                    font=("Segoe UI", 9, "bold"),
                    padding=[6, 6])
    style.map("Treeview.Heading",
              background=[("active", "#3f3f3f")])

    # --- Scrollbar oscura ---
    style.configure("Vertical.TScrollbar",
                    background="#3a3a3a", troughcolor=C_BG,
                    bordercolor=C_BG, arrowcolor=C_FG)
    style.configure("Horizontal.TScrollbar",
                    background="#3a3a3a", troughcolor=C_BG,
                    bordercolor=C_BG, arrowcolor=C_FG)

    # --- PanedWindow ---
    style.configure("TPanedwindow", background=C_BG)


# ============================================================
# CARGA DE EJEMPLO
# ============================================================
def cargar_ejemplo(clave):
    titulo, codigo = EJEMPLOS[clave]
    caja_codigo.delete(1.0, tk.END)
    caja_codigo.insert(tk.END, codigo)
    lbl_ejemplo_activo.config(text=f"📌 Ejemplo activo: {titulo}")


# ============================================================
# ANIMACIÓN DE ESCRITURA (EFECTO MÁQUINA DE ESCRIBIR)
# ============================================================
def animar_escritura(widget, texto, indice=0, callback=None):
    if indice < len(texto):
        widget.insert(tk.END, texto[indice])
        widget.see(tk.END)
        widget.after(2, animar_escritura, widget, texto, indice + 1, callback)
    else:
        if callback:
            callback()


# ============================================================
# DIBUJO DE ÁRBOLES EN CANVAS
# ============================================================
def dibujar_arbol_en_canvas(canvas, nodo_datos, es_parse_tree=False):
    canvas.delete("all")

    SEP_H = 115   # Separación horizontal mínima garantizada entre hojas
    SEP_V = 70    # Separación vertical entre niveles

    def obtener_titulo(nodo):
        if not isinstance(nodo, dict):
            return str(nodo)
        if es_parse_tree:
            simbolo = nodo.get("simbolo", "Nodo")
            valor = nodo.get("valor")
            regla = nodo.get("regla")
            if valor is not None:
                return f"{simbolo}: '{valor}'"
            if regla:
                parte = regla.split("→")[-1].strip() if "→" in regla else regla
                return f"[{simbolo}]\n→ {parte}"
            return f"[{simbolo}]"
        titulo = nodo.get("Nodo", "Desconocido")
        if "Valor" in nodo:
            titulo = f"{titulo}: {nodo['Valor']}"
        return titulo

    def obtener_hijos(nodo):
        if not isinstance(nodo, dict):
            return []
        return nodo.get("hijos", []) if es_parse_tree else nodo.get("Hijos", [])

    # ------------------------------------------------------------------
    # FASE 1: Calcular posiciones usando una rejilla basada en hojas.
    # Cada hoja recibe una columna consecutiva; los padres se centran
    # sobre sus hijos. Así se garantiza separación mínima entre hermanos.
    # ------------------------------------------------------------------
    posiciones = {}          # id(nodo) -> (x, y)
    contador_hoja = [0]

    def asignar_posiciones(nodo, profundidad):
        y = 30 + profundidad * SEP_V
        hijos = obtener_hijos(nodo)

        if not hijos:
            x = contador_hoja[0] * SEP_H
            contador_hoja[0] += 1
            posiciones[id(nodo)] = (x, y)
            return x

        xs_hijos = [asignar_posiciones(h, profundidad + 1) for h in hijos]
        x = (xs_hijos[0] + xs_hijos[-1]) / 2
        posiciones[id(nodo)] = (x, y)
        return x

    asignar_posiciones(nodo_datos, 0)

    # ------------------------------------------------------------------
    # FASE 2: Dibujar cajas, líneas y texto usando las posiciones calculadas.
    # ------------------------------------------------------------------
    def dibujar_nodo(texto, x, y, es_terminal):
        fill = "#e8f5e9" if es_terminal else "#e1f5fe"
        outline = "#388e3c" if es_terminal else "#0288d1"
        color = "#1b5e20" if es_terminal else "#01579b"
        id_texto = canvas.create_text(x, y, text=texto, font=("Segoe UI", 8, "bold"),
                                      fill=color, justify="center")
        bbox = canvas.bbox(id_texto)
        if not bbox:
            return y + 4, y - 4
        px, py = 6, 4
        rect = canvas.create_rectangle(bbox[0]-px, bbox[1]-py, bbox[2]+px, bbox[3]+py,
                                       fill=fill, outline=outline, width=1.5)
        canvas.tag_raise(id_texto, rect)
        # (borde_inferior, borde_superior)
        return bbox[3] + py, bbox[1] - py

    def recorrer(nodo):
        """Dibuja el nodo y su subárbol; retorna (borde_inferior, borde_superior)."""
        es_term = nodo.get("es_terminal", False) if isinstance(nodo, dict) else True
        x, y = posiciones[id(nodo)]
        borde_inf, borde_sup = dibujar_nodo(obtener_titulo(nodo), x, y, es_term)

        for hijo in obtener_hijos(nodo):
            hx, _hy = posiciones[id(hijo)]
            _h_inf, h_sup = recorrer(hijo)  # el hijo se dibuja una sola vez
            # La línea parte del borde inferior del padre y llega al borde
            # superior del hijo, sin invadir los rectángulos.
            id_linea = canvas.create_line(x, borde_inf, hx, h_sup,
                                          arrow=tk.LAST, fill="#78909c", width=1.5)
            canvas.tag_lower(id_linea)

        return borde_inf, borde_sup

    recorrer(nodo_datos)

    # Ajustar el área de desplazamiento para permitir scroll en árboles grandes
    canvas.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))


def abrir_ventana_arbol(tipo="ast"):
    nodo_root = ast_actual if tipo == "ast" else parse_tree_actual
    titulo = ("Árbol de Sintaxis Abstracta (AST)"
              if tipo == "ast" else "Árbol de Derivación (Parse Tree Completo)")
    if not nodo_root:
        messagebox.showwarning("Sin datos",
                               "Primero ejecuta el análisis con código MiniCode válido.")
        return

    ventana_arbol = tk.Toplevel()
    ventana_arbol.title(titulo)
    ventana_arbol.geometry("1100x750")
    ventana_arbol.configure(bg=C_BG)

    frame = tk.Frame(ventana_arbol, bg=C_BG)
    frame.pack(fill=tk.BOTH, expand=True)

    hbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
    hbar.pack(side=tk.BOTTOM, fill=tk.X)
    vbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
    vbar.pack(side=tk.RIGHT, fill=tk.Y)

    canvas = tk.Canvas(frame, bg="#ffffff", highlightthickness=0,
                       xscrollcommand=hbar.set, yscrollcommand=vbar.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    hbar.config(command=canvas.xview)
    vbar.config(command=canvas.yview)

    dibujar_arbol_en_canvas(canvas, nodo_root, es_parse_tree=(tipo == "parse_tree"))


# ============================================================
# TABLAS DE AUTÓMATAS FINITOS
# ============================================================
def llenar_tabla_afd(tree, afd):
    for item in tree.get_children():
        tree.delete(item)
    for fila in afd.obtener_tabla_transiciones_limpia():
        if fila['es_inicial']:
            prefijo = "→ "
        elif fila['es_aceptacion']:
            prefijo = "* "
        else:
            prefijo = "   "
        tree.insert("", tk.END, values=(
            f"{prefijo}{fila['origen']}",
            fila['simbolo'],
            fila['destino'],
            "Aceptación" if fila['es_aceptacion']
            else ("Inicial" if fila['es_inicial'] else "Intermedio")
        ))


def renderizar_afd_tablas():
    afds = obtener_afds()
    llenar_tabla_afd(tree_afd_if, afds['if'])
    llenar_tabla_afd(tree_afd_id, afds['identificador'])
    llenar_tabla_afd(tree_afd_b01, afds['binario_01'])
    llenar_tabla_afd(tree_afd_b0011, afds['binario_00_11'])


def mostrar_trazas_afd(trazas):
    caja_traza_afd.delete(1.0, tk.END)
    texto = "=== TRAZAS DE EJECUCIÓN DE AUTÓMATAS FINITOS ===\n\n"

    textos = [
        ("if", "📌 PALABRA RESERVADA 'if' (AFD_if):"),
        ("identificador", "📌 IDENTIFICADORES MiniCode (AFD_ID [ab][ab01]*):"),
        ("binario_01", "📌 CADENAS BINARIAS TERMINADAS EN 01 (AFD_BIN_01):"),
        ("binario_00_11", "📌 CADENAS CON 00 o 11 (AFD_BIN_00_11):"),
    ]

    for clave, cabecera in textos:
        lista = trazas.get(clave, [])
        if not lista:
            continue
        texto += f"{cabecera}\n"
        for t in lista:
            estado = "✅ ACEPTADO" if t['aceptado'] else "❌ RECHAZADO"
            texto += f"  • Lexema: '{t['lexema']}' -> {estado} (Línea {t['linea']})\n"
            for paso in t['traza']:
                if paso.get('es_inicial'):
                    texto += f"      [Inicio] Estado Inicial: '{paso['estado']}'\n"
                elif 'error' in paso:
                    texto += f"      [Error] {paso['error']}\n"
                else:
                    texto += f"      δ('{paso['caracter']}') -> '{paso['estado']}'\n"
        texto += "\n"

    caja_traza_afd.insert(tk.END, texto)


# ============================================================
# EJECUCIÓN DEL ANÁLISIS
# ============================================================
def ejecutar_compilador():
    global ast_actual, parse_tree_actual, trazas_afd_actuales

    # Bloquear botón mientras corre la animación para evitar reentradas
    btn_ejecutar.config(state=tk.DISABLED)

    caja_lexico.delete(1.0, tk.END)
    caja_ast.delete(1.0, tk.END)
    caja_parse_tree.delete(1.0, tk.END)

    codigo_fuente = caja_codigo.get(1.0, tk.END)
    tokens, trazas = analizar_con_afd(codigo_fuente)
    trazas_afd_actuales = trazas

    # --- Tokens ---
    texto_lexico = f"✅ ANÁLISIS LÉXICO COMPLETADO. Total tokens: {len(tokens)}\n"
    texto_lexico += "-" * 60 + "\n"
    for t in tokens:
        marca = "⚠️ " if t['tipo'] == 'MISMATCH' else ""
        texto_lexico += (f"{marca}Token -> Tipo: {t['tipo']:<16} | "
                         f"Valor: '{t['valor']}' (Línea {t['linea']})\n")

    mostrar_trazas_afd(trazas)

    # --- Datos del análisis sintáctico (se calculan de inmediato) ---
    texto_ast = ""
    texto_pt = ""
    try:
        parser = AnalizadorSintactico(tokens)
        ast, parse_tree, errores = parser.parsear()
        ast_actual = ast
        parse_tree_actual = parse_tree

        texto_ast = "✅ ÁRBOL DE SINTAXIS ABSTRACTA (AST)\n"
        if errores:
            texto_ast += "⚠️ Advertencias durante el parseo:\n"
            for err in errores:
                texto_ast += f"  • {err}\n"
        texto_ast += "-" * 60 + "\n"
        texto_ast += generar_ast_json(ast) if ast else "{}"

        texto_pt = "✅ ÁRBOL DE DERIVACIÓN COMPLETO (PARSE TREE)\n"
        texto_pt += "Símbolos No Terminales entre corchetes [] y Terminales como valores.\n"
        texto_pt += "-" * 60 + "\n"
        texto_pt += generar_parse_tree_json(parse_tree) if parse_tree else "{}"
    except Exception as e:
        texto_ast = f"❌ ERROR SINTÁCTICO:\n{str(e)}"
        texto_pt = f"❌ ERROR SINTÁCTICO:\n{str(e)}"

    # --- AST y Parse Tree se imprimen instantáneamente ---
    caja_ast.insert(tk.END, texto_ast)
    caja_parse_tree.insert(tk.END, texto_pt)

    def reactivar():
        btn_ejecutar.config(state=tk.NORMAL)
        if ast_actual:
            btn_arbol_ast.config(state=tk.NORMAL)
        if parse_tree_actual:
            btn_arbol_pt.config(state=tk.NORMAL)

    # --- Solo el Análisis Léxico usa animación de máquina de escribir ---
    animar_escritura(caja_lexico, texto_lexico, callback=reactivar)


# ============================================================
# CONSTRUCCIÓN DE LA INTERFAZ
# ============================================================
ventana = tk.Tk()
ventana.title("Compilador MiniCode")
ventana.state('zoomed')
ventana.configure(bg=C_BG)
configurar_estilos(ventana)

paned = tk.PanedWindow(ventana, orient=tk.HORIZONTAL, bg=C_BG, bd=0,
                       sashwidth=4)
paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# ---------- PANEL IZQUIERDO: EDITOR ----------
panel_izq = tk.Frame(paned, bg=C_BG)
paned.add(panel_izq, width=430)

tk.Label(panel_izq, text="Compilador MiniCode", fg=C_BLUE_LIGHT, bg=C_BG,
         font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 8))

frame_ejemplos = tk.Frame(panel_izq, bg=C_BG)
frame_ejemplos.pack(fill=tk.X, pady=2)

tk.Label(frame_ejemplos, text="Ejemplos:", fg=C_FG_DIM, bg=C_BG,
         font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=(0, 4))

for clave, (titulo, _codigo) in EJEMPLOS.items():
    tk.Button(frame_ejemplos, text=titulo.split(" (")[0], bg=C_ACCENT, fg="white",
              font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2",
              activebackground=C_ACCENT_HOVER, activeforeground="white",
              command=lambda c=clave: cargar_ejemplo(c)).pack(side=tk.LEFT, padx=2)

tk.Button(frame_ejemplos, text="Limpiar", bg="#3a3a3a", fg=C_FG,
          font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2",
          activebackground="#4a4a4a", activeforeground="white",
          command=lambda: caja_codigo.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=2)

lbl_ejemplo_activo = tk.Label(panel_izq, text="📌 Ejemplo activo: Ejemplo 1 (Básico)",
                              fg=C_ORANGE, bg=C_BG, font=FUENTE_LABEL)
lbl_ejemplo_activo.pack(anchor="w", pady=6)

tk.Label(panel_izq, text="Código fuente", fg=C_FG, bg=C_BG,
         font=FUENTE_TITULO).pack(anchor="w", pady=(8, 2))

caja_codigo = scrolledtext.ScrolledText(panel_izq, font=FUENTE_CODIGO,
                                        bg=C_BG_EDITOR, fg=C_FG,
                                        insertbackground="#ffffff",
                                        relief="flat", borderwidth=0,
                                        highlightthickness=1,
                                        highlightbackground=C_BORDER,
                                        highlightcolor=C_ACCENT)
caja_codigo.pack(fill=tk.BOTH, expand=True, pady=4)
cargar_ejemplo("ej1")

btn_ejecutar = tk.Button(panel_izq, text="▶  Ejecutar MiniCode",
                         bg=C_GREEN, fg="white", font=("Segoe UI", 12, "bold"),
                         relief="flat", cursor="hand2",
                         activebackground="#3fb950", activeforeground="white",
                         command=ejecutar_compilador, pady=10)
btn_ejecutar.pack(fill=tk.X, pady=10)

# ---------- PANEL DERECHO: NOTEBOOK ----------
panel_der = tk.Frame(paned, bg=C_BG)
paned.add(panel_der)

notebook = ttk.Notebook(panel_der)
notebook.pack(fill=tk.BOTH, expand=True)

# --- Pestaña 1: Análisis Léxico ---
tab_lexico = tk.Frame(notebook, bg=C_BG_PANEL)
notebook.add(tab_lexico, text="  Análisis Léxico  ")
tk.Label(tab_lexico, text="Tokens Reconocidos", fg=C_CYAN, bg=C_BG_PANEL,
         font=FUENTE_TITULO).pack(anchor="w", padx=10, pady=(10, 2))
caja_lexico = scrolledtext.ScrolledText(tab_lexico, font=FUENTE_CODIGO,
                                        bg=C_BG_EDITOR, fg=C_CYAN,
                                        relief="flat", borderwidth=0,
                                        highlightthickness=1,
                                        highlightbackground=C_BORDER)
caja_lexico.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

# --- Pestaña 2: AST (JSON) ---
tab_ast = tk.Frame(notebook, bg=C_BG_PANEL)
notebook.add(tab_ast, text="  AST (JSON)  ")
caja_ast = scrolledtext.ScrolledText(tab_ast, font=FUENTE_CODIGO,
                                     bg=C_BG_EDITOR, fg=C_ORANGE,
                                     relief="flat", borderwidth=0,
                                     highlightthickness=1,
                                     highlightbackground=C_BORDER)
caja_ast.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))
btn_arbol_ast = tk.Button(tab_ast, text="🌳  Abrir AST en Canvas Gráfico",
                          bg=C_ACCENT, fg="white", font=("Segoe UI", 9, "bold"),
                          relief="flat", cursor="hand2",
                          activebackground=C_ACCENT_HOVER, activeforeground="white",
                          command=lambda: abrir_ventana_arbol("ast"),
                          state=tk.DISABLED, pady=7)
btn_arbol_ast.pack(fill=tk.X, padx=10, pady=(0, 10))

# --- Pestaña 3: Árbol de Derivación ---
tab_pt = tk.Frame(notebook, bg=C_BG_PANEL)
notebook.add(tab_pt, text="  Árbol de Derivación  ")
caja_parse_tree = scrolledtext.ScrolledText(tab_pt, font=FUENTE_CODIGO,
                                            bg=C_BG_EDITOR, fg=C_YELLOW,
                                            relief="flat", borderwidth=0,
                                            highlightthickness=1,
                                            highlightbackground=C_BORDER)
caja_parse_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))
btn_arbol_pt = tk.Button(tab_pt, text="🌿  Abrir Parse Tree en Canvas Gráfico",
                         bg=C_ACCENT, fg="white", font=("Segoe UI", 9, "bold"),
                         relief="flat", cursor="hand2",
                         activebackground=C_ACCENT_HOVER, activeforeground="white",
                         command=lambda: abrir_ventana_arbol("parse_tree"),
                         state=tk.DISABLED, pady=7)
btn_arbol_pt.pack(fill=tk.X, padx=10, pady=(0, 10))

# --- Pestaña 4: Autómatas Finitos ---
tab_afd = tk.Frame(notebook, bg=C_BG_PANEL)
notebook.add(tab_afd, text="  Autómatas Finitos  ")

paned_afd = tk.PanedWindow(tab_afd, orient=tk.VERTICAL, bg=C_BG_PANEL,
                           bd=0, sashwidth=4)
paned_afd.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

frame_tablas = tk.Frame(paned_afd, bg=C_BG_PANEL)
paned_afd.add(frame_tablas, height=320)

tk.Label(frame_tablas, text="Tablas de Transición δ(Estado, Símbolo) → Estado Destino",
         fg=C_BLUE_LIGHT, bg=C_BG_PANEL, font=FUENTE_TITULO).pack(anchor="w", pady=(0, 5))

grid = tk.Frame(frame_tablas, bg=C_BG_PANEL)
grid.pack(fill=tk.BOTH, expand=True)

columnas = ("estado", "entrada", "destino", "tipo")


def crear_tree_afd(parent, titulo, color):
    lf = tk.LabelFrame(parent, text=f" {titulo} ", fg=color, bg=C_BG_PANEL,
                       font=("Segoe UI", 9, "bold"), bd=1, relief="solid")
    tree = ttk.Treeview(lf, columns=columnas, show="headings", height=7)
    tree.heading("estado", text="Estado")
    tree.heading("entrada", text="Entrada")
    tree.heading("destino", text="Destino")
    tree.heading("tipo", text="Tipo Estado")
    tree.column("estado", width=80, anchor="center")
    tree.column("entrada", width=140, anchor="center")
    tree.column("destino", width=80, anchor="center")
    tree.column("tipo", width=95, anchor="center")
    tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
    return lf, tree


# Fila 1
f_if, tree_afd_if = crear_tree_afd(grid, "AFD_if  (Palabra Reservada)", C_CYAN)
f_if.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

f_id, tree_afd_id = crear_tree_afd(grid, "AFD_ID  (Identificador MiniCode)", C_ORANGE)
f_id.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)

# Fila 2
f_b01, tree_afd_b01 = crear_tree_afd(grid, "AFD_BIN_01  (Termina en 01)", C_YELLOW)
f_b01.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

f_b0011, tree_afd_b0011 = crear_tree_afd(grid, "AFD_BIN_00_11  (Contiene 00 o 11)", "#c586c0")
f_b0011.grid(row=1, column=1, sticky="nsew", padx=4, pady=4)

grid.rowconfigure(0, weight=1)
grid.rowconfigure(1, weight=1)
grid.columnconfigure(0, weight=1)
grid.columnconfigure(1, weight=1)

# Sub-panel de trazas
frame_trazas = tk.Frame(paned_afd, bg=C_BG_PANEL)
paned_afd.add(frame_trazas)

tk.Label(frame_trazas, text="Traza de Evaluación de Lexemas con AFD",
         fg=C_BLUE_LIGHT, bg=C_BG_PANEL, font=FUENTE_TITULO).pack(anchor="w", pady=(6, 2))
caja_traza_afd = scrolledtext.ScrolledText(frame_trazas, font=FUENTE_CODIGO,
                                           bg=C_BG_EDITOR, fg=C_FG,
                                           relief="flat", borderwidth=0,
                                           highlightthickness=1,
                                           highlightbackground=C_BORDER)
caja_traza_afd.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

# Inicializar tablas de autómatas
renderizar_afd_tablas()

ventana.mainloop()
