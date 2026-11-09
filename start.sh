# The user-JWT flow needs dtlpy_exporter >= 0.1.10 (ExportBase accepts a per-user sdk).
# The agent's requirements step has installed an older version, so upgrade at pod start when missing.
python -c "from dtlpy_exporter import ExportBase; assert hasattr(ExportBase, 'set_sdk')" 2>/dev/null \
    || python -m pip install --no-deps --user --upgrade https://storage.googleapis.com/dtlpy/single-export-be/dtlpy_exporter-0.1.10-py3-none-any.whl \
    || echo "WARNING: failed to install dtlpy_exporter 0.1.10; per-user export will fail"

python -m uvicorn "app:app" \
        --host="0.0.0.0" \
        --port=3000 \
        --timeout-keep-alive=60
