# Compilador MiniCode - Análisis Léxico, Sintáctico y Autómatas Finitos

Proyecto académico desarrollado para la materia **Compiladores** en la **Universidad de La Guajira**.

## Autores
- **Saith Martinez**
- **Yair Ospino**
- **Luís Lopez**

---

## Descripción del Proyecto

Aplicación de escritorio desarrollada en **Python** que integra tres fases del diseño de un compilador sobre el lenguaje académico **MiniCode**:

1. **Análisis Léxico (Lexer):** Escanea el código fuente y extrae el listado de tokens válidos. Los componentes principales (palabra reservada `if`, identificadores, cadenas binarias) se validan mediante **Autómatas Finitos Deterministas (AFD)**.
2. **Análisis Sintáctico (Parser):** Valida la gramática con un analizador descendente recursivo, respetando la **precedencia de operadores** y los **paréntesis**, y genera dos representaciones:
   - **AST** (Árbol de Sintaxis Abstracta) resumido en formato JSON.
   - **Árbol de Derivación (Parse Tree)** completo, con símbolos Terminales y No Terminales y las reglas gramaticales aplicadas.
3. **Autómatas Finitos:** Tablas de transición δ(Estado, Símbolo) → Estado Destino y trazas de evaluación paso a paso de cada lexema.

---

## Autómatas Finitos Implementados

| AFD | Descripción | Estados |
|-----|-------------|---------|
| **AFD_if** | Reconoce la palabra reservada `if` | q0, q1, q2 (aceptación), qd (trampa) |
| **AFD_ID** | Identificadores MiniCode con regla estricta `[ab][ab01]*` | q0, q1 (aceptación), qd |
| **AFD_BIN_01** | Cadenas binarias que terminan exactamente en `01` | q0, q1, q2 (aceptación), qd |
| **AFD_BIN_00_11** | Cadenas binarias que contienen `00` o `11` | q0, q1, q2, q3 (aceptación), qd |

> Las transiciones hacia el estado trampa `qd` se agrupan en una sola fila `[Otros caracteres] → qd` para una visualización limpia.

---

## Gramática de MiniCode

```
Programa        → ListaSentencias
ListaSentencias → Sentencia ListaSentencias | ε
Sentencia       → IfStmt | Asignacion | ExpresionStmt
IfStmt          → "if" Expresion
Asignacion      → ID "=" Expresion
Expresion       → Termino { ("+" | "-") Termino }
Termino         → Factor { ("*" | "/") Factor }
Factor          → NUM | BIN_01 | BIN_00_11 | ID | "(" Expresion ")"
```

La jerarquía `Expresion → Termino → Factor` garantiza que la multiplicación y división tengan mayor precedencia que la suma y resta, y que los paréntesis alteren la evaluación correctamente.

---

## Estructura del Proyecto

```
compilador/
├── lexer.py       # Análisis léxico + definición de los 4 AFD
├── parser.py      # Análisis sintáctico, AST y Árbol de Derivación
├── interfaz.py    # Interfaz gráfica (tkinter)
└── README.md
```

---

## Interfaz Gráfica

Construida con **tkinter** en estilo oscuro profesional (tema tipo VS Code). Distribución a dos columnas:

- **Panel izquierdo:** título, selector de 3 ejemplos de MiniCode, editor de código y botón **▶ Ejecutar MiniCode**.
- **Panel derecho:** sistema de pestañas (`ttk.Notebook`):
  1. **Análisis Léxico** — lista de tokens (con animación de máquina de escribir).
  2. **AST (JSON)** — árbol de sintaxis abstracta + botón para renderizarlo gráficamente.
  3. **Árbol de Derivación** — Parse Tree completo + botón para renderizarlo gráficamente.
  4. **Autómatas Finitos** — las 4 tablas de transición y la traza de evaluación de lexemas.

Los árboles se dibujan en **ventanas independientes** sobre un `Canvas` con scrollbars, autoajustables mediante una rejilla basada en hojas que evita la superposición de nodos.

### Ejemplos incluidos

**Ejemplo 1 (Básico):**
```
if a01
```

**Ejemplo 2 (Operaciones):**
```
b11 = a0 + a1
if b11
```

**Ejemplo 3 (Complejo):**
```
a0 = 10
b1 = 20
a11 = a0 * (b1 + 10)
```

---

## Requisitos del Sistema
- **Python 3.13+** instalado en el equipo.
- Utiliza exclusivamente librerías nativas (`tkinter`, `re`, `json`), por lo que **no requiere instalaciones externas**.

---

## Cómo Ejecutar el Proyecto
1. Clonar o descargar el repositorio en tu equipo.
2. Abrir una terminal o línea de comandos en la carpeta raíz del proyecto.
3. Ejecutar la interfaz gráfica principal con el siguiente comando:
   ```bash
   python interfaz.py
   ```

---

## Técnica del Árbol de Derivación y los Autómatas

- **Árbol de Derivación:** Se construye con la técnica de **análisis descendente recursivo**. A medida que cada función de parsing reconoce una regla gramatical, se genera en paralelo un nodo del Parse Tree que conserva tanto los símbolos No Terminales (p. ej. `Expresion`, `Termino`, `Factor`) como los Terminales (tokens concretos). El AST se genera simultáneamente como una versión resumida de ese mismo proceso.
- **Autómatas Finitos:** Se modelan como objetos `AFD` con estados, alfabeto, función de transición δ, estado inicial y estados de aceptación. El lexer evalúa cada lexema contra el autómata correspondiente y registra la traza de transiciones, que la interfaz muestra en tiempo de ejecución.
