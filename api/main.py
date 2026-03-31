from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import ai_request, data, login

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(login.router)
app.include_router(data.router)
app.include_router(ai_request.router)
