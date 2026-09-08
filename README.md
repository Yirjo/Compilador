# Compilador Interactivo - Análisis Léxico y Sintáctico

Proyecto académico desarrollado para la materia **Compiladores** en la **Universidad de La Guajira**.

## Autores
- **Saith Martinez**
- **Yair Ospino**

---

## Descripción del Proyecto
Esta aplicación de escritorio desarrollada en **Python** integra las dos primeras fases del diseño de un compilador:
1. **Análisis Léxico (Lexer):** Escanea el código fuente y extrae el listado detallado de tokens válidos.
2. **Análisis Sintáctico (Parser):** Valida la gramática y genera el Árbol de Sintaxis Abstracta (AST) en formato JSON, acompañado de un informe analítico en lenguaje natural y un renderizador gráfico independiente.

---

## Requisitos del Sistema
- **Python 3.x** instalado en el equipo.
- Utiliza exclusivamente librerías nativas (`tkinter`, `re`, `json`), por lo que **no requiere instalaciones externas**.

---

## Cómo Ejecutar el Proyecto
1. Clonar o descargar el repositorio en tu equipo.
2. Abrir una terminal o línea de comandos en la carpeta raíz del proyecto.
3. Ejecutar la interfaz gráfica principal con el siguiente comando:
   ```bash
   python interfaz.py