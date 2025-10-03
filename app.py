from fastapi import FastAPI

app = FastAPI(title="Kitchen QA API")

@app.get("/health")
def health():
    return {"status": "ok"}
