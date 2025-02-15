import uvicorn
from fastapi import FastAPI
from routes import router

app = FastAPI()

# Include routes
app.include_router(router)

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Use Render's assigned port
    uvicorn.run(app, host="0.0.0.0", port=port)