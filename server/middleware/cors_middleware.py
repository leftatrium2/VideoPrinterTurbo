from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


# CORS
def register_cors_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        # Allowed origin addresses for cross-origin requests
        allow_origins=[
            # "http://localhost:8080",
            # "http://localhost:5173",
            # "http://127.0.0.1:8080",
            # "http://127.0.0.1:5173",
            # "*" means allow all domains (for dev only, not recommended for production)
            "*"
        ],
        allow_credentials=True,  # Allow cookies
        allow_methods=["*"],  # Allow all HTTP methods: GET/POST/PUT/DELETE...
        allow_headers=["*"],  # Allow all request headers
    )
