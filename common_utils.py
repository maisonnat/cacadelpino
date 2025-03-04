import asyncio
import random
from playwright.async_api import Page

async def random_delay(min_ms: int, max_ms: int) -> None:
    """Adds a random delay in seconds between min_ms and max_ms."""
    if min_ms < 0 or max_ms < min_ms:
        raise ValueError("Invalid delay range")
    delay = random.randint(min_ms, max_ms) / 1000.0
    await asyncio.sleep(delay)

async def move_mouse(page: Page, x_range: tuple[int, int], y_range: tuple[int, int]) -> None:
    """Moves the mouse to a random position within the given ranges."""
    if not isinstance(x_range, tuple) or not isinstance(y_range, tuple):
        raise TypeError("Range parameters must be tuples")
    if len(x_range) != 2 or len(y_range) != 2:
        raise ValueError("Range tuples must contain exactly 2 values")
    if x_range[0] > x_range[1] or y_range[0] > y_range[1]:
        raise ValueError("Invalid coordinate ranges")
    
    x = random.randint(x_range[0], x_range[1])
    y = random.randint(y_range[0], y_range[1])
    await page.mouse.move(x, y)