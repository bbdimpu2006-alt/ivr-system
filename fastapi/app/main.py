from fastapi import FastAPI

app = FastAPI(title="IVR Admin Panel")

@app.get("/")
def read_root():
    return {"message": "IVR Admin Panel - Running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
