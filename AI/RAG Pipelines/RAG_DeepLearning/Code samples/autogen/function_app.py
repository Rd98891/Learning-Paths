import azure.functions as func
from .main_fastapi import app as fastapi_app

# Create an ASGI Function App that directly integrates with FastAPI
# This automatically handles all HTTP routing through the FastAPI app
app = func.AsgiFunctionApp(
    app=fastapi_app, 
    http_auth_level=func.AuthLevel.ANONYMOUS
)