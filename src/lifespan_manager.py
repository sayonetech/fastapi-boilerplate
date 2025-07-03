from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI


class LifespanManager:
    def __init__(self, base_app=None):
        self.base_app = base_app
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

        # Start base app lifespan if provided
        if self.base_app is not None:
            async with self.base_app.lifespan(app):
                yield
        else:
            yield

        # Run custom shutdown tasks
        for task in self.shutdown_tasks:
            await task()