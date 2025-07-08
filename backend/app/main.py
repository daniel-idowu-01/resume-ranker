from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Resume Ranker backend is running!"}
