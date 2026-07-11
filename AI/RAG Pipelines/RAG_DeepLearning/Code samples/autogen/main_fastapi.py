from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from autogenmultiagentwithrag import router as autogen_router
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="AutoGen Multi-Agent API",
    description="Azure Function with FastAPI for AutoGen multi-agent conversations",
    version="1.0.0",
    docs_url='/docs',
    openapi_url='/openapi.json',
    redoc_url='/redoc'
)

# Enable CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AutoGen Multi-Agent API",
        "message": "Service is running successfully"
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "AutoGen Multi-Agent API",
        "version": "1.0.0",
        "description": "Multi-agent conversation system using AutoGen",
        "endpoints": {
            "invoke-agent": "/invoke-agent (POST)",
            "health": "/health (GET)",
            "docs": "/docs (GET)",
            "openapi": "/openapi.json (GET)"
        }
    }


# Include autogen multi-agent router
app.include_router(autogen_router, tags=["autogen"])

# Optional: Run the app locally for development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)