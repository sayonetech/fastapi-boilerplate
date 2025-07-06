"""Lifespan manager"""

from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI

# Type alias for async startup/shutdown tasks
AsyncTask = Callable[[], Awaitable[None]]


class LifespanManager:
    """Handles app startup and shutdown events."""

    def __init__(self) -> None:
        self._startup_tasks: list[AsyncTask] = []
        self._shutdown_tasks: list[AsyncTask] = []

    def add_startup_task(self, task: AsyncTask) -> None:
        """Register a function to run on startup."""
        self._startup_tasks.append(task)

    def add_shutdown_task(self, task: AsyncTask) -> None:
        """Register a function to run on shutdown."""
        self._shutdown_tasks.append(task)

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncGenerator[None, None]:
        """FastAPI lifespan handler."""
        for task in self._startup_tasks:
            await task()

        yield  # App runs here

        for task in self._shutdown_tasks:
            await task()
