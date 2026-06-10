from fastapi import FastAPI
from mongo_connector import *
from agent import process_query
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str

app = FastAPI()


@app.get("/")
def home():
    return {"message": "AI Database Copilot API Running"}


@app.get("/collections")
def collections():
    return {"collections": get_collections()}


@app.get("/customers")
def customers():
    return {"customers": get_all_customers()}


@app.get("/customer-count")
def customer_count():
    return {"count": count_customers()}


@app.post("/query")
def query_agent(request: QueryRequest):

    result = process_query(request.query)

    return {
        "query": request.query,
        "result": result
    }