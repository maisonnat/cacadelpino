import asyncio
import logging
import os
import argparse
from datetime import datetime
from pathlib import Path
from src.account_manager import AccountManager
from config import CREDENTIALS_FILE
import log_config  # Inicializa la configuración de logging
import random  # Added import for random module

# Global variables to track HTML saving state and interval
save_html = False
last_html_save = None
HTML_SAVE_INTERVAL = 5  # Save HTML every 5 seconds

async def save_page_html(page, description):
    """Save the HTML content of a page if HTML saving is enabled."""
    global last_html_save
    
    if not save_html:
        return
    
    current_time = datetime.now()
    
    # Create html_dumps directory if it doesn't exist
    html_dir = Path('html_dumps')
    html_dir.mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = current_time.strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{description}.html"
    filepath = html_dir / filename
    
    # Get and save HTML content
    content = await page.content()
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    logging.info(f"Saved HTML content to {filepath}")
    last_html_save = current_time

async def periodic_html_save(page):
    """Periodically save HTML content if enabled."""
    if not save_html:
        return
        
    current_time = datetime.now()
    if last_html_save is None or (current_time - last_html_save).total_seconds() >= HTML_SAVE_INTERVAL:
        await save_page_html(page, "periodic_save")

async def run_single_account(max_retries=3):
    """Ejecuta el proceso para una sola cuenta (primera en el archivo de credenciales)
    
    Args:
        max_retries: Número máximo de intentos en caso de error por rate limiting
    """
    from playwright.async_api import async_playwright
    from auth import login, handle_stay_signed_in_prompt, verify_navigation
    from activities import complete_daily_activities, complete_more_activities
    from config import URL
    from humanization import move_mouse, random_delay
    from antibot_evasion import AntiBotEvasion
    from human_behavior import HumanBehavior
    
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                # Exponential backoff between retry attempts
                backoff_seconds = min(300, 60 * (2 ** (attempt - 2)))  # Start with 60s, max 5 min
                jitter = random.uniform(0.8, 1.2)  # Add 20% jitter
                wait_time = int(backoff_seconds * jitter)
                logging.info(f"Retry attempt {attempt}/{max_retries}. Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)
            
            logging.info(f"Starting Bing Rewards automation for single account (attempt {attempt}/{max_retries})")
            with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                username, password = first_line.split(':')
                logging.info(f"Loaded credentials for user: {username}")

            # Add initial delay to avoid detection patterns
            await HumanBehavior.random_delay(3000, 8000)

            async with async_playwright() as p:
                try:
                    logging.info("Launching browser")
                    # Configuración mejorada para sigilo
                    browser_args = [
                        '--incognito',
                        '--no-sandbox',
                        '--start-maximized',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-extensions',
                        '--disable-automation',
                        '--disable-dev-shm-usage',
                        '--disable-features=IsolateOrigins,site-per-process',
                        '--disable-site-isolation-trials'
                    ]
                    
                    # Inicializar el sistema de evasión de detección de bots
                    antibot = AntiBotEvasion()
                    
                    browser = await p.chromium.launch(headless=False, args=browser_args)
                    # Usar el contexto mejorado con técnicas anti-detección
                    context = await antibot.setup_browser_context(browser)
                    page = await context.new_page()
                    
                    # Aplicar técnicas de sigilo adicionales
                    await antibot.apply_stealth_techniques(page)
                    await periodic_html_save(page)  # Save HTML after page creation
                    
                    # Humanizar antes de iniciar cualquier acción
                    await HumanBehavior.move_mouse_naturally(page, 100, 100)
                    await HumanBehavior.random_delay(1000, 2000)
                    await periodic_html_save(page)  # Save HTML after mouse movement
                    
                    # Simular comportamiento humano aleatorio antes de iniciar el login
                    await HumanBehavior.random_delay(2000, 5000)
                    
                    logging.info("Attempting login")
                    try:
                        await login(page, username, password)
                        await periodic_html_save(page)
                        await save_page_html(page, "after_login")
                        
                        # Añadir pausa adicional después del login para evitar detección
                        await HumanBehavior.random_delay(5000, 10000)
                        await periodic_html_save(page)
                        
                        if await handle_stay_signed_in_prompt(page):
                            logging.info("Successfully handled stay signed in prompt")
                            await periodic_html_save(page)
                            await save_page_html(page, "after_stay_signed_in")
                            
                            # Verify successful navigation to rewards page with increased retries
                            if await verify_navigation(page, "rewards.bing.com", max_retries=5):
                                logging.info("Successfully verified navigation to rewards page")
                                await periodic_html_save(page)
                                await save_page_html(page, "rewards_page")
                                
                                # Añadir pausa antes de iniciar actividades
                                await HumanBehavior.random_delay(3000, 7000)
                                await periodic_html_save(page)
                                
                                logging.info("Starting daily activities")
                                await complete_daily_activities(page)
                                await periodic_html_save(page)
                                await save_page_html(page, "after_daily_activities")
                                
                                # Pausa entre conjuntos de actividades
                                await HumanBehavior.random_delay(5000, 10000)
                                await periodic_html_save(page)
                                
                                logging.info("Starting more activities")
                                await complete_more_activities(page)
                                await periodic_html_save(page)
                                await save_page_html(page, "after_more_activities")
                            else:
                                logging.error("Failed to navigate to rewards page after login")
                                await periodic_html_save(page)  # Save HTML on navigation failure
                        else:
                            logging.error("Failed to handle stay signed in prompt")
                            await periodic_html_save(page)  # Save HTML on prompt handling failure
                    except Exception as e:
                        logging.error(f"Error during login or activities: {str(e)}")
                        # Take screenshot and save HTML for debugging
                        await page.screenshot(path="error_screenshot.png")
                        await save_page_html(page, "error_state")
                        logging.info("Error screenshot saved as error_screenshot.png")
                    
                    # Añadir pausa antes de cerrar el navegador
                    await HumanBehavior.random_delay(2000, 5000)
                    await periodic_html_save(page)  # Final HTML save before closing
                    logging.info("Closing browser")
                    await browser.close()
                except Exception as e:
                    logging.error(f"An error occurred: {str(e)}")
                    raise
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            raise

async def run_multiple_accounts():
    """Ejecuta el proceso para múltiples cuentas usando AccountManager"""
    try:
        logging.info("Starting Bing Rewards automation for multiple accounts")
        # Crear directorio de progreso si no existe
        progress_dir = 'progress'
        os.makedirs(progress_dir, exist_ok=True)
        
        # Inicializar el gestor de cuentas
        account_manager = AccountManager(CREDENTIALS_FILE, progress_dir)
        
        # Procesar todas las cuentas secuencialmente
        await account_manager.process_all_accounts()
        
        logging.info("Completed processing all accounts")
    except Exception as e:
        logging.error(f"An error occurred in multi-account processing: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Bing Rewards Automation')
        parser.add_argument('-HTML', action='store_true', help='Save HTML content of pages for analysis')
        args = parser.parse_args()
        
        # Set global HTML saving flag
        save_html = args.HTML
        
        # Descomentar la línea que se desee utilizar:
        # Para procesar una sola cuenta (la primera en el archivo):
        asyncio.run(run_single_account())
        
        # Para procesar múltiples cuentas secuencialmente:
        # asyncio.run(run_multiple_accounts())
    except Exception as e:
        logging.error(f"Application failed: {str(e)}")