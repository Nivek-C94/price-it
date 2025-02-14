import uvicorn
from fastapi import FastAPI, Query
from app.routes import router

app = FastAPI()

# Include routes
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)