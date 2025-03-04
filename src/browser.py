import asyncio
import logging
import random
from typing import Dict, Optional
from playwright.async_api import async_playwright, Browser as PlaywrightBrowser, Page

from config import DELAY_RANGES
from utils import random_delay, move_mouse

class Browser:
    """Browser wrapper class for Microsoft Rewards automation."""
    
    def __init__(self, headless: bool = False, user_agent: Optional[str] = None):
        self.headless = headless
        self.user_agent = user_agent
        self.browser: Optional[PlaywrightBrowser] = None
        self.page: Optional[Page] = None
    
    async def __aenter__(self):
        return await self.launch()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def launch(self):
        """Launch the browser and create a new page."""
        playwright = await async_playwright().start()
        browser_args = []
        
        if self.user_agent:
            browser_args.append(f'--user-agent={self.user_agent}')
        
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=browser_args
        )
        
        self.page = await self.browser.new_page()
        return self
    
    async def close(self):
        """Close the browser properly."""
        if self.browser:
            try:
                await self.browser.close()
                self.browser = None
                self.page = None
                logging.info("Browser closed successfully")
            except Exception as e:
                logging.error(f"Error closing browser: {e}")
    
    async def navigate(self, url: str, timeout: int = 30000):
        """Navigate to a URL with proper error handling."""
        if not self.page:
            raise ValueError("Browser not initialized. Call launch() first.")
        
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            return True
        except Exception as e:
            logging.error(f"Navigation error: {e}")
            return False
    
    async def is_logged_in(self) -> bool:
        """Check if the user is currently logged in."""
        if not self.page:
            return False
        
        try:
            # Look for elements that indicate a logged-in state
            # This will depend on the specific Microsoft Rewards page structure
            profile_element = await self.page.query_selector('#id_n')
            return profile_element is not None
        except Exception as e:
            logging.error(f"Error checking login status: {e}")
            return False
    
    async def switch_to_new_tab(self, wait_time: int = 5):
        """Switch to a newly opened tab."""
        if not self.browser:
            return False
        
        try:
            await asyncio.sleep(wait_time)  # Wait for the new tab to open
            pages = await self.browser.pages()
            if len(pages) > 1:
                self.page = pages[-1]  # Switch to the last opened page
                await random_delay(*DELAY_RANGES["short"])
                return True
            return False
        except Exception as e:
            logging.error(f"Error switching to new tab: {e}")
            return False
    
    async def close_current_tab(self):
        """Close the current tab and switch back to the previous one."""
        if not self.browser or not self.page:
            return False
        
        try:
            await self.page.close()
            pages = await self.browser.pages()
            if pages:
                self.page = pages[0]  # Switch back to the first page
                return True
            return False
        except Exception as e:
            logging.error(f"Error closing current tab: {e}")
            return False