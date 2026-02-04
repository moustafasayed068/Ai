from fastapi import FastAPI

endpoint = FastAPI()

@endpoint.get("/")
def hi(name):
    return "hi " + name