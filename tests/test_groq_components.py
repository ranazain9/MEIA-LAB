import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from backend.core.rate_limiter import GroqRateLimiter
from backend.core.retry import execute_with_retry
from backend.core.queue_worker import QueueWorkerPool


class GroqComponentsTests(unittest.TestCase):

    def test_rate_limiter_concurrency(self):
        limiter = GroqRateLimiter(max_concurrent=1, requests_per_minute=10)

        async def run_task():
            async with limiter:
                await asyncio.sleep(0.01)

        async def run_all():
            await asyncio.gather(run_task(), run_task())

        asyncio.run(run_all())
        self.assertEqual(len(limiter.request_timestamps), 2)

    def test_retry_mechanism_success(self):
        call_count = 0

        async def mock_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                err = Exception("Rate limit hit")
                err.status_code = 429
                raise err
            return "success"

        res = asyncio.run(execute_with_retry(mock_call, max_retries=3, base_delay=0.01))
        self.assertEqual(res, "success")
        self.assertEqual(call_count, 2)

    def test_retry_mechanism_fatal_error(self):
        async def mock_call():
            err = Exception("Auth failed")
            err.status_code = 401
            raise err

        with self.assertRaises(Exception) as context:
            asyncio.run(execute_with_retry(mock_call, max_retries=3, base_delay=0.01))
        self.assertEqual(getattr(context.exception, "status_code"), 401)

    def test_queue_worker_pool(self):
        """Workers correctly process submitted tasks and return results."""

        async def test_job(val: int) -> int:
            await asyncio.sleep(0.01)
            return val * 2

        async def run():
            pool = QueueWorkerPool(worker_count=2)
            pool.start()
            res1, res2 = await asyncio.gather(
                pool.submit(test_job, 5),
                pool.submit(test_job, 10),
            )
            await pool.shutdown()
            return res1, res2

        res = asyncio.run(run())
        self.assertEqual(res, (10, 20))


if __name__ == "__main__":
    unittest.main()
