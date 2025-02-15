import os
import uvicorn
from fastapi import FastAPI
from routes import router

app = FastAPI()

# Include routes
app.include_router(router)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Use assigned port (e.g. Render's port)
    uvicorn.run(app, host="0.0.0.0", port=port)
