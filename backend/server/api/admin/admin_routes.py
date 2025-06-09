"""
Admin routes for the application.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import httpx
from ..auth import validate_token

router = APIRouter()


# SQLite Web proxy route
@router.get("/db-query{path:path}")
async def proxy_sqlite_web(
    path: str,
    user_info: dict = Depends(validate_token),
):
    """
    Proxy requests to sqlite-web, ensuring only admins can access.
    """
    # Check if user is admin (email is in allowed list)
    if not user_info.get("is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Only administrators can access the database query interface",
        )

    # Forward request to sqlite-web
    async with httpx.AsyncClient() as client:
        try:
            # Forward the request to sqlite-web
            response = await client.get(
                f"http://sqlite-web:8081{path}",
                headers={"X-Forwarded-For": "127.0.0.1"},
                follow_redirects=True,
            )

            # Stream the response back to the client
            return StreamingResponse(
                response.aiter_bytes(),
                media_type=response.headers.get("content-type", "text/html"),
                headers=dict(response.headers),
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502, detail=f"Error connecting to sqlite-web: {str(e)}"
            )
