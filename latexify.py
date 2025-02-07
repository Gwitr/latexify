import os
import time
import codecs
import shutil
import traceback
from pathlib import Path
from subprocess import run, CalledProcessError

import pyautogui

TEMPLATE = r"""
\documentclass[preview]{standalone}
\usepackage{xcolor}
\usepackage{pagecolor}
\usepackage{fontspec}
\newcommand{\terminus}{\setmainfont{Terminus.ttf}}
%s
\begin{document}
\nopagecolor
\color{white}
%s
\end{document}
"""
LUALATEX_DIR = Path("/opt/texlive/2024/bin/x86_64-linux")
OUT_DPI = 125

def bake_latex(code):
    folder = Path("/tmp") / codecs.encode(os.urandom(8), 'hex').decode('ascii')
    folder.mkdir()
    try:
        preamble, *rest = "[latex]".join(code.split("[latex]")[1:]).split("[main]")
        preamble, main_body = (preamble, "[main]".join(rest)) if rest else ("", preamble)

        src_file, dst_file = folder / "document.tex", folder / "document.pdf"
        with open(src_file, "w", encoding="utf-8") as f:
            f.write(TEMPLATE % (preamble, main_body))

        proc = run([LUALATEX_DIR / "lualatex", f"-output-directory={folder}", src_file], capture_output=True)
        proc.check_returncode()
        proc = run(["magick", "convert", "-bordercolor", "transparent", "-border", "2", "-density", str(OUT_DPI), dst_file, "-quality", "90", "png:-"], capture_output=True)
        proc.check_returncode()

        return True, proc.stdout

    except CalledProcessError as e:
        traceback.print_exc()
        return False, b"\n".join(i for i in open(f"{folder}/document.log", "rb").read().split(b"\n") if i.startswith((b"!", b"l.", b"  ")))

    finally:
        shutil.rmtree(folder)

while True:
    proc = run(["xclip", "-selection", "clipboard", "-t", "text/plain", "-out"], capture_output=True)
    if proc.returncode != 0 or not proc.stdout.strip().startswith(b"[latex]"):
        time.sleep(.1)
        continue

    success, data = bake_latex(proc.stdout.strip().decode("utf8"))

    proc = run(["xclip", "-selection", "clipboard", "-t", "image/png" if success else "text/plain", "-in"], input=data)
    if proc.returncode == 0:
        pyautogui.hotkey("ctrl", "v")
        if success:
            time.sleep(.15)
            pyautogui.press("enter")
