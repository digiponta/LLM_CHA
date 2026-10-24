"""v0.6.2: optional GUI-only math rendering. No TeX subprocess is used.

Input format: LATEX( raw LaTeX ). The CLI and underlying evidence stay unchanged.
"""
import base64
import io
import re
import tkinter as tk

MARKER = re.compile(r"LATEX\(\s*(.*?)\s*\)", re.DOTALL)
MAX_FORMULA_LENGTH = 500

def split_latex(text):
    """Split LATEX(...) with balanced parentheses, including TeX math arguments."""
    if not isinstance(text, str):
        return []
    result = []
    cursor = 0
    while True:
        start = text.find("LATEX(", cursor)
        if start < 0:
            break
        depth = 1
        pos = start + len("LATEX(")
        while pos < len(text) and depth:
            if text[pos] == "(":
                depth += 1
            elif text[pos] == ")":
                depth -= 1
            pos += 1
        if depth:
            break  # malformed marker: preserve original source as text
        if start > cursor:
            result.append((False, text[cursor:start]))
        result.append((True, text[start+len("LATEX("):pos-1].strip()))
        cursor = pos
    if cursor < len(text):
        result.append((False, text[cursor:]))
    return result

def render_formula_png(formula, dpi=145):
    """Render a small transparent PNG using matplotlib's internal mathtext.

    Does not enable external LaTeX execution. Raises on unsupported notation,
    so the GUI can show the original LATEX( ... ) text instead.
    """
    if not isinstance(formula, str) or not formula.strip() or len(formula) > MAX_FORMULA_LENGTH:
        raise ValueError("Empty or overlong formula")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    figure = Figure(figsize=(8, 0.7), dpi=dpi)
    FigureCanvasAgg(figure)
    figure.patch.set_alpha(0)
    figure.text(0, 0.5, "$" + formula.strip() + "$", va="center", fontsize=14, color="#174b34")
    stream = io.BytesIO()
    figure.savefig(stream, format="png", dpi=dpi, transparent=True,
                   bbox_inches="tight", pad_inches=0.04)
    return stream.getvalue()

def insert_gui_message(widget, message, tag, images):
    """Tkinter main-thread only; append text interleaved with in-line formula images."""
    for is_formula, content in split_latex(message):
        if not is_formula:
            widget.insert("end", content, tag)
            continue
        try:
            image = tk.PhotoImage(data=base64.b64encode(render_formula_png(content)).decode("ascii"))
            images.append(image)  # Tk images must remain referenced.
            widget.image_create("end", image=image, padx=3, pady=2)
        except (ImportError, ValueError, RuntimeError, SyntaxError, OverflowError, tk.TclError):
            widget.insert("end", "LATEX( " + content + " )", tag)
