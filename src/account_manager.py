import asyncio
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import logging
import random
from playwright.async_api import async_playwright

from auth import login, handle_stay_signed_in_prompt, verify_navigation
from activities import complete_daily_activities, complete_more_activities
from config import DELAY_RANGES
from humanization import random_delay

class AccountManager:
    def __init__(self, credentials_file: str, progress_dir: str = 'progress'):
        self.credentials_file = credentials_file
        self.progress_dir = Path(progress_dir)
        self.progress_dir.mkdir(exist_ok=True)
        self.accounts = self._load_credentials()
        
    def _load_credentials(self) -> List[Dict[str, str]]:
        """Load credentials from the credentials file."""
        accounts = []
        with open(self.credentials_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    username, password = line.strip().split(':')
                    accounts.append({
                        'username': username,
                        'password': password
                    })
        return accounts
    
    def _get_progress_file(self, username: str) -> Path:
        """Get the progress file path for a specific account."""
        return self.progress_dir / f"{username}_progress.json"
    
    def _load_progress(self, username: str) -> Dict:
        """Load progress for a specific account."""
        progress_file = self._get_progress_file(username)
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                return json.load(f)
        return {
            'last_run': None,
            'completed_activities': [],
            'points_earned': 0
        }
    
    def _save_progress(self, username: str, progress: Dict) -> None:
        """Save progress for a specific account."""
        progress_file = self._get_progress_file(username)
        with open(progress_file, 'w') as f:
            json.dump(progress, f, indent=4)
    
    async def process_account(self, account: Dict[str, str]) -> None:
        """Process a single account."""
        username = account['username']
        progress = self._load_progress(username)
        
        try:
            async with async_playwright() as p:
                # Configuración mejorada para sigilo
                browser_args = [
                    '--incognito',
                    '--no-sandbox',
                    '--start-maximized',
                    '--disable-blink-features=AutomationControlled'
                ]
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                
                browser = await p.chromium.launch(headless=False, args=browser_args)
                context = await browser.new_context(user_agent=user_agent)
                page = await context.new_page()
                
                # Ajustar navegador para parecer más humano
                await page.evaluate("delete window.navigator.__proto__.webdriver")
                await page.evaluate("window.scrollTo(0, 0)")
                await random_delay(*DELAY_RANGES["medium"])
                
                # Login
                await login(page, username, account['password'])
                if not await handle_stay_signed_in_prompt(page):
                    logging.error(f"Failed to handle stay signed in prompt for {username}")
                    return
                
                # Verify successful navigation to rewards page
                if not await verify_navigation(page, "rewards.bing.com"):
                    logging.error(f"Failed to navigate to rewards page after login for {username}")
                    return
                
                # Complete activities
                daily_points = await complete_daily_activities(page)
                more_points = await complete_more_activities(page)
                
                # Update progress
                progress['last_run'] = datetime.now().isoformat()
                progress['points_earned'] += (daily_points + more_points)
                self._save_progress(username, progress)
                
                await browser.close()
                
        except Exception as e:
            logging.error(f"Error processing account {username}: {e}")
    
    async def process_all_accounts(self) -> None:
        """Process all accounts sequentially."""
        for account in self.accounts:
            logging.info(f"Processing account: {account['username']}")
            await self.process_account(account)
            logging.info(f"Completed processing account: {account['username']}")
            
            # Add humanized delay between accounts to avoid detection
            # Random delay between 15-60 seconds to mimic human behavior
            import random
            delay_seconds = random.randint(15, 60)
            logging.info(f"Waiting {delay_seconds} seconds before processing next account...")
            await asyncio.sleep(delay_seconds)