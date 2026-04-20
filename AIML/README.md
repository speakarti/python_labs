## conda vs venv vs uv ##
conda  =  full container for everything
          (Python + system libs + packages)

venv   =  lightweight bubble
          (just Python packages)

uv     =  venv but 10-15x faster
          (modern replacement for pip+venv)
All three manage Python environments — but solve different problems.

conda → ML/AI projects needing GPU, CUDA, or non-Python libraries
venv → simple projects, beginners, when you want zero extra tools
uv → everything else — fast, modern, great for web/backend/CI pipelines

## python packages ##
flask, fastAPI - rest API, swagger
pytorch, tensorflow
scikit, sciearn
huggingface, trnsformers, colab.research.google.com
https://huggingface.co/

pip install "fastapi[all]"
pip install fastapi
pip install uvicorn[standard] -> ASGI Server