import os
import asyncio
import time
from typing import Optional, Dict, Any
from functools import wraps
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage
from dotenv import load_dotenv
import logging

# Import the API monitor
from Utils.api_monitor import (
    log_api_request,
    get_recommended_delay,
    should_throttle_requests,
)

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class RateLimitedLLMService:
    """Rate-limited LLM service with retry logic and concurrency control"""

    def __init__(
        self,
        api_key: str,
        model: str = "qwen/qwen3-32b",  # meta-llama/llama-4-scout-17b-16e-instruct qwen/qwen3-32b
        temperature: float = 0.4,
        max_concurrent_requests: int = 3,
        requests_per_minute: int = 30,
        retry_attempts: int = 3,
        base_retry_delay: float = 1.0,
    ):

        self.max_concurrent_requests = max_concurrent_requests
        self.requests_per_minute = requests_per_minute
        self.retry_attempts = retry_attempts
        self.base_retry_delay = base_retry_delay

        # Semaphore to limit concurrent requests
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)

        # Rate limiting tracking
        self._request_times = []
        self._rate_limit_lock = asyncio.Lock()

        # Initialize the LLM
        self._llm = ChatGroq(
            api_key=api_key,
            model=model,
            temperature=temperature,
        )

        logger.info(
            f"Initialized rate-limited LLM service with {max_concurrent_requests} concurrent requests, {requests_per_minute} requests/minute"
        )

    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        async with self._rate_limit_lock:
            current_time = time.time()

            # Remove requests older than 1 minute
            self._request_times = [
                t for t in self._request_times if current_time - t < 60
            ]

            # Check if we've exceeded the rate limit
            if len(self._request_times) >= self.requests_per_minute:
                oldest_request = min(self._request_times)
                wait_time = 60 - (current_time - oldest_request)
                if wait_time > 0:
                    logger.warning(
                        f"Rate limit reached. Waiting {wait_time:.2f} seconds"
                    )
                    await asyncio.sleep(wait_time)
                    return await self._check_rate_limit()

            # Record this request
            self._request_times.append(current_time)

    async def _make_request_with_retry(self, messages, **kwargs):
        """Make LLM request with retry logic and monitoring"""
        last_exception = None
        start_time = time.time()

        # Check if we should add additional throttling based on recent patterns
        if should_throttle_requests():
            delay = get_recommended_delay()
            if delay > 0:
                logger.info(
                    f"Proactive throttling: waiting {delay:.2f} seconds based on recent API usage"
                )
                await asyncio.sleep(delay)

        for attempt in range(self.retry_attempts):
            try:
                # Check rate limits
                await self._check_rate_limit()

                # Make the actual request
                result = await asyncio.to_thread(self._llm.invoke, messages, **kwargs)

                # Log successful request
                response_time = time.time() - start_time
                log_api_request("success", response_time=response_time)

                return result

            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()
                response_time = time.time() - start_time

                # Check if it's a rate limit error
                if (
                    "429" in error_msg
                    or "rate limit" in error_msg
                    or "too many requests" in error_msg
                ):
                    log_api_request(
                        "error", error_type="rate_limit", response_time=response_time
                    )
                    wait_time = self.base_retry_delay * (2**attempt) + (
                        attempt * 5
                    )  # Exponential backoff with extra delay for rate limits
                    logger.warning(
                        f"Rate limit hit (attempt {attempt + 1}/{self.retry_attempts}). Waiting {wait_time:.2f} seconds before retry"
                    )
                    await asyncio.sleep(wait_time)
                    start_time = time.time()  # Reset start time for next attempt
                    continue

                # Check if it's a server error (5xx)
                elif any(code in error_msg for code in ["500", "502", "503", "504"]):
                    log_api_request(
                        "error", error_type="server_error", response_time=response_time
                    )
                    wait_time = self.base_retry_delay * (2**attempt)
                    logger.warning(
                        f"Server error (attempt {attempt + 1}/{self.retry_attempts}). Waiting {wait_time:.2f} seconds before retry"
                    )
                    await asyncio.sleep(wait_time)
                    start_time = time.time()  # Reset start time for next attempt
                    continue

                # For other errors, don't retry
                else:
                    log_api_request(
                        "error", error_type="other", response_time=response_time
                    )
                    logger.error(f"Non-retryable error: {e}")
                    raise e

        # If all retries failed
        logger.error(
            f"All {self.retry_attempts} retry attempts failed. Last error: {last_exception}"
        )
        log_api_request("error", error_type="retry_exhausted")
        raise last_exception

    async def ainvoke(self, messages, **kwargs):
        """Async invoke with rate limiting and concurrency control"""
        async with self._semaphore:  # Limit concurrent requests
            return await self._make_request_with_retry(messages, **kwargs)

    def invoke(self, messages, **kwargs):
        """Synchronous invoke (for backward compatibility)"""
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a new task
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, self.ainvoke(messages, **kwargs)
                    )
                    return future.result()
            else:
                # If no event loop is running, run in new loop
                return asyncio.run(self.ainvoke(messages, **kwargs))
        except RuntimeError:
            # Fallback: run in new event loop
            return asyncio.run(self.ainvoke(messages, **kwargs))


# Create rate-limited instance
_rate_limited_service = RateLimitedLLMService(
    api_key=os.getenv("GROQ_API_KEY"),
    model="qwen/qwen3-32b",  # qwen/qwen3-32b gemma2-9b-it
    temperature=0.4,
    max_concurrent_requests=2,  # Conservative limit
    requests_per_minute=25,  # Conservative rate limit
    retry_attempts=3,
    base_retry_delay=1.0,
)

# LangChain-compatible LLM for LangGraph (with rate limiting)
langgraph_llm = _rate_limited_service
