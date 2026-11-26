"""HTTP layer for the /api endpoints in spec section 4.

Each route reads the raw request, calls the service, and turns the result or a
ServiceError into a response. No rule is checked here, and FastAPI never validates or
coerces the input: the body is read as bytes and every parameter as a string.
"""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.service import BookingService, ServiceError


def error_response(err: ServiceError) -> JSONResponse:
    """R9: exactly {"error": code, "message": text} with the rule's status."""
    return JSONResponse({"error": err.code, "message": err.message}, status_code=err.status)


def _last(request: Request, name: str) -> str | None:
    """D5: the last value of a query parameter, or None when it is absent."""
    values = request.query_params.getlist(name)
    return values[-1] if values else None


def build_router(service: BookingService) -> APIRouter:
    router = APIRouter()

    async def call(fn: Callable, *args: object) -> object:
        # The service and repository are blocking; run them off the event loop.
        return await run_in_threadpool(fn, *args)

    @router.get("/api/rooms")
    async def list_rooms() -> Response:
        rooms = await call(service.list_rooms)
        return JSONResponse([room.to_dict() for room in rooms], status_code=200)

    @router.get("/api/bookings")
    async def list_bookings(request: Request) -> Response:
        # D6: parameters other than date and room_id are ignored.
        try:
            bookings = await call(service.list_bookings, _last(request, "date"), _last(request, "room_id"))
        except ServiceError as err:
            return error_response(err)
        return JSONResponse([b.to_dict() for b in bookings], status_code=200)

    @router.post("/api/bookings")
    async def create_booking(request: Request) -> Response:
        body = await request.body()
        try:
            booking = await call(service.create_booking, body)
        except ServiceError as err:
            return error_response(err)
        return JSONResponse(booking.to_dict(), status_code=201)

    @router.delete("/api/bookings/{booking_id}")
    async def cancel_booking(booking_id: str) -> Response:
        try:
            await call(service.cancel_booking, booking_id)
        except ServiceError as err:
            return error_response(err)
        return Response(status_code=204)

    return router
