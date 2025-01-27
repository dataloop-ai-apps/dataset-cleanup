FROM docker.io/dataloopai/dtlpy-agent:cpu.py3.10.opencv
USER 1000
ENV HOME=/tmp
RUN pip install --user  \
    fastapi  \
    uvicorn  \
    dtlpy \
    scikit-learn \
    https://storage.googleapis.com/dtlpy/single-export-be/dtlpy_exporter-0.1.3-py3-none-any.whl \
    faiss-cpu