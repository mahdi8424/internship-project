from fastapi import FastAPI


app = FastAPI(
    title="Project & Task Management API",
    version="1.0.0",
)


@app.get("/")
def root():
    return {"message": "API is running"}