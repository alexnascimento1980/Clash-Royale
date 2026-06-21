"""
Entry point usado pelo Vercel (ver vercel.json: builds.src = "api/index.py").

Antes, este arquivo provavelmente continha uma cópia do app.py da raiz
(necessária porque o Vercel só builda o que está apontado em vercel.json),
o que significa manter a mesma lógica em dois lugares e correr o risco de
um ficar desatualizado em relação ao outro.

Agora ele só reexporta a instância `app` definida na raiz do projeto —
fonte única de verdade, tanto para rodar local (`python app.py`) quanto
para o deploy serverless.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app  # noqa: E402,F401  (reexportado para o runtime do Vercel)
