import uvicorn

uvicorn.run(
    "app.core:server",
    host="127.0.0.1",
    port=5000,
    reload=True,
    log_level="debug"
)