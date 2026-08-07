"""
RAGTUNE Input Security Pipeline - FastAPI Security Gateway Middleware
Intercepts all inbound HTTP requests and enforces the 8-stage input security pipeline.
"""

import json

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from auth.storage.auth_db import AuthDatabaseRepository
from input_security.framework.pipeline import InputSecurityPipeline
from input_security.framework.stage import (
    SecurityRequestContainer,
    SecurityViolationException,
)

EXCLUDED_PATHS = {"/health", "/api/v1/health", "/docs", "/openapi.json", "/redoc"}

# Global pipeline instance
auth_db = AuthDatabaseRepository()
security_pipeline = InputSecurityPipeline(auth_db)


class InputSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)


        # Read raw request body
        raw_body = await request.body()
        client_ip = request.client.host if request.client else None
        headers_dict = dict(request.headers)

        parsed_payload = {}
        user_query = None

        if raw_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                parsed_payload = json.loads(raw_body.decode("utf-8"))
                if isinstance(parsed_payload, dict):
                    user_query = parsed_payload.get("query")
            except Exception:
                pass

        container = SecurityRequestContainer(
            raw_body=raw_body,
            headers=headers_dict,
            client_ip=client_ip,
            path=request.url.path,
            method=request.method,
            parsed_payload=parsed_payload,
            user_query=user_query,
        )

        try:
            enriched_request = security_pipeline.process_request(container)
            request.state.security_request = enriched_request
            request.state.security_context = enriched_request.security_context
        except SecurityViolationException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": "SecurityViolation",
                    "stage": e.stage_name,
                    "message": e.message,
                    "risk_score": e.risk_score,
                },
            )

        response = await call_next(request)
        response.headers["X-RAGTUNE-Security-Request-ID"] = enriched_request.request_id
        response.headers["X-RAGTUNE-Trust-Level"] = enriched_request.trust_level.value
        response.headers["X-RAGTUNE-Threat-Risk-Score"] = str(
            enriched_request.cumulative_risk_score
        )
        return response
