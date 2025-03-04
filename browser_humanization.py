import random
from typing import Dict, List, Optional
from playwright.async_api import Browser, BrowserContext, Page

class BrowserHumanizer:
    def __init__(self):
        self.viewport_sizes: List[Dict[str, int]] = [
            {"width": 1280, "height": 720},
            {"width": 1366, "height": 768},
            {"width": 1920, "height": 1080},
            {"width": 1440, "height": 900}
        ]
        
        self.user_agents: List[str] = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.2365.66"
        ]

    def get_launch_args(self) -> List[str]:
        return [
            '--incognito',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--start-maximized',
            '--disable-blink-features=AutomationControlled',
            '--disable-automation',
            '--disable-notifications',
            '--disable-popup-blocking'
        ]

    def get_random_context_options(self) -> Dict:
        viewport = random.choice(self.viewport_sizes)
        return {
            'viewport': viewport,
            'user_agent': random.choice(self.user_agents),
            'color_scheme': 'dark' if random.random() > 0.5 else 'light',
            'locale': random.choice(['en-US', 'en-GB', 'es-ES']),
            'timezone_id': random.choice(['Europe/London', 'America/New_York', 'Europe/Madrid']),
            'permissions': ['geolocation'],
            'geolocation': {'latitude': 40.4168, 'longitude': -3.7038},
            'has_touch': random.random() > 0.7
        }

    async def apply_evasions(self, page: Page):
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = { runtime: {} };
            
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = parameters => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => Math.floor(Math.random() * (16 - 2) + 2)
            });
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => Math.floor(Math.random() * (8 - 2) + 2)
            });
        """)

    async def set_headers(self, context: BrowserContext):
        await context.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })