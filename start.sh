python -m uvicorn "app:app" \
        --host="0.0.0.0" \
        --port=3000 \
        --timeout-keep-alive=60 