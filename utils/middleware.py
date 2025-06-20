import os
from fastapi import Request, Response
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware

class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle maintenance mode for deployments.
    When MAINTENANCE_MODE=true, shows a "Coming Soon" page to all users
    except for health check endpoints.
    """
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Check if maintenance mode is enabled
        maintenance_mode = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"
        
        if not maintenance_mode:
            # Normal operation - continue to the app
            return await call_next(request)
        
        # Allow health check endpoints to pass through
        health_paths = ["/health", "/_ah/health", "/api/health"]
        if request.url.path in health_paths:
            return await call_next(request)
        
        # Return maintenance page for all other requests
        maintenance_html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Coming Soon - Job Matching App</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0;
                    padding: 0;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                }
                .container {
                    text-align: center;
                    max-width: 500px;
                    padding: 2rem;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }
                h1 {
                    font-size: 3rem;
                    margin-bottom: 1rem;
                    font-weight: 300;
                }
                .icon {
                    font-size: 4rem;
                    margin-bottom: 1rem;
                }
                p {
                    font-size: 1.2rem;
                    line-height: 1.6;
                    margin-bottom: 1.5rem;
                    opacity: 0.9;
                }
                .status {
                    font-size: 0.9rem;
                    opacity: 0.7;
                    margin-top: 2rem;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">🚀</div>
                <h1>Coming Soon</h1>
                <p>We're working hard to bring you the best job matching experience with AI-powered assistants.</p>
                <p>Our platform will connect talented professionals with amazing companies through intelligent conversations.</p>
                <div class="status">
                    Status: Under Development | Maintenance Mode Active
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=maintenance_html, status_code=503) 