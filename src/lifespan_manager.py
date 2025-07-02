from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI


class LifespanManager:
    def __init__(self, mcp_app):
        self.mcp_app = mcp_app
        self.startup_tasks = []
        self.shutdown_tasks = []

    def add_startup_task(self, task):
        """Add a startup task (async function)"""
        self.startup_tasks.append(task)

    def add_shutdown_task(self, task):
        """Add a shutdown task (async function)"""
        self.shutdown_tasks.append(task)

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncGenerator[None, None]:
        # Run custom startup tasks
        for task in self.startup_tasks:
            await task()

        # Start MCP lifespan
        async with self.mcp_app.lifespan(app):
            yield

        # Run custom shutdown tasks
        for task in self.shutdown_tasks:
            await task()
