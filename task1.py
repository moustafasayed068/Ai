from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def hi(name):
    return "hi " + name