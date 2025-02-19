import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Include routes
app.include_router(router)

'''

uvicorn main:app --host 0.0.0.0 --port 443 --ssl-keyfile ssl\privkey.pem --ssl-certfile "ssl\fullchain.pem"

'''
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))  # Use assigned port (e.g. Render's port)
    uvicorn.run(app, host="0.0.0.0", port=port, ssl_keyfile="ssl\\privkey.pem", ssl_certfile="ssl\\fullchain.pem")
