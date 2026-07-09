import asyncio
import logging
from typing import Any, Callable, Coroutine, Tuple

logger = logging.getLogger(__name__)

class QueueWorkerPool:
    """
    Worker pool processing tasks through an asyncio.Queue.
    Ensures a bounded number of concurrent active request workers.
    """

    def __init__(self, worker_count: int = 2) -> None:
        self.queue: asyncio.Queue[Tuple[Callable[..., Coroutine[Any, Any, Any]], Tuple[Any, ...], dict[str, Any], asyncio.Future[Any]]] = asyncio.Queue()
        self.worker_count = worker_count
        self.workers: list[asyncio.Task[None]] = []
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        for i in range(self.worker_count):
            task = asyncio.create_task(self._worker_loop(i))
            self.workers.append(task)
            logger.info("Started Groq Queue Worker %d", i)

    async def _worker_loop(self, worker_id: int) -> None:
        while True:
            try:
                func, args, kwargs, future = await self.queue.get()
                try:
                    if future.cancelled():
                        continue
                    res = await func(*args, **kwargs)
                    future.set_result(res)
                except Exception as exc:
                    if not future.done():
                        future.set_exception(exc)
                finally:
                    self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Queue worker %d loop encountered error: %s", worker_id, exc)

    async def submit(self, func: Callable[..., Coroutine[Any, Any, Any]], *args: Any, **kwargs: Any) -> Any:
        self.start()
        future = asyncio.get_running_loop().create_future()
        await self.queue.put((func, args, kwargs, future))
        return await future

    async def shutdown(self) -> None:
        for worker in self.workers:
            worker.cancel()
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        self._started = False
