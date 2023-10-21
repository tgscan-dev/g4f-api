import uvicorn

if __name__ == "__main__":
    uvicorn.run("g4f_api.app:app", host="0.0.0.0", reload=True, port=7000)
