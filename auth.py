from playwright.async_api import Page
from humanization import move_mouse, random_delay, human_type
from config import SELECTORS, DELAY_RANGES, CREDENTIALS_FILE, URL
import logging
import asyncio
import random

async def login(page: Page, username: str, password: str) -> None:
    try:
        logging.info(f"Navigating to Microsoft Rewards for user: {username}")
        
        # Initialize antibot evasion for rate limit handling
        from antibot_evasion import AntiBotEvasion
        antibot = AntiBotEvasion()
        
        # Apply rate limit delay before navigation
        await antibot.apply_rate_limit_delay()
        
        await page.goto(URL, wait_until="networkidle", timeout=90000)  # Extended timeout for initial load
        logging.info("Page loaded successfully")
        
        # Check for rate limiting after page load with retries
        for attempt in range(1, 4):  # Try up to 3 times
            if await antibot.handle_rate_limit(page, attempt):
                logging.warning(f"Rate limit detected during initial page load (attempt {attempt}), applying backoff")
                # Try reloading after backoff
                await page.reload(wait_until="networkidle")
                await random_delay(*DELAY_RANGES["long"])
            else:
                break
        
        try:
            # Import and use the new selector validation function
            from selector_validation import validate_selector
            
            # Validate username field before interaction
            if not await validate_selector(page, SELECTORS["username_field"], timeout=30000):
                logging.error("Username field not found or not visible")
                raise Exception("Username field validation failed")
            
            # Mover el ratón antes de interactuar con el campo de usuario
            await move_mouse(page, (50, 200), (50, 100))
            await random_delay(*DELAY_RANGES["short"])
            
            logging.info("Filling username field")
            await human_type(page, SELECTORS["username_field"], username)
            
            # Verify next button presence before clicking
            await page.wait_for_selector(SELECTORS["next_button"], state="visible", timeout=20000)
            
            # Mover el ratón al botón "Siguiente" y hacer clic
            await move_mouse(page, (400, 700), (400, 500))
            await random_delay(*DELAY_RANGES["short"])
            await page.click(SELECTORS["next_button"])
            logging.info("Username submitted, proceeding to password")
            
            # Apply rate limit delay after username submission
            await antibot.apply_rate_limit_delay()
            
            # Wait for navigation and page stability with extended timeout
            await page.wait_for_load_state("networkidle", timeout=60000)
            await random_delay(*DELAY_RANGES["long"])

            # Handle post-login prompt and verify navigation
            if await handle_stay_signed_in_prompt(page):
                logging.info("Successfully handled stay signed in prompt")
                
                # Verify navigation after prompt handling
                if not await verify_navigation(page, "rewards.bing.com"):
                    logging.error("Failed to navigate after stay signed in prompt")
                    return False
                
                await periodic_html_save(page)
                await save_page_html(page, "after_stay_signed_in")
            
            # Additional check for page readiness
            await page.wait_for_load_state("load", timeout=30000)
            await random_delay(2000, 4000)
            
            # Check for rate limiting after username submission
            if await antibot.handle_rate_limit(page):
                logging.warning("Rate limit detected after username submission, applying backoff")
                # Try to continue anyway
                pass
        except Exception as e:
            logging.error(f"Error during username submission: {e}")
            # Take screenshot for debugging
            try:
                await page.screenshot(path="username_error.png")
                logging.info("Screenshot saved as username_error.png")
            except:
                pass
            # Try to continue anyway
            pass
        
        # Verify current URL before proceeding
        current_url = await page.evaluate("window.location.href")
        logging.info(f"Current URL after username submission: {current_url}")
        
        # Check for HTTP 400 error or other error indicators in the URL or content
        try:
            page_content = await page.content()
            if "ERROR 400" in page_content or "chrome-error" in current_url or "Too Many Requests" in page_content:
                logging.warning("Detected error page after username submission, applying recovery strategy")
                # Take screenshot for debugging
                await page.screenshot(path="error_after_username.png")
                logging.info("Screenshot saved as error_after_username.png")
                
                # Apply longer delay before retry
                await random_delay(20000, 40000)  # 20-40 seconds delay
                
                # Try to navigate back to the login page
                await page.goto(URL, wait_until="networkidle", timeout=60000)
                await random_delay(*DELAY_RANGES["long"])
                
                # Check if we need to start over
                if await page.query_selector(SELECTORS["username_field"]):
                    logging.info("Restarting login process from username field")
                    await human_type(page, SELECTORS["username_field"], username)
                    await random_delay(*DELAY_RANGES["medium"])
                    await page.click(SELECTORS["next_button"])
                    await page.wait_for_load_state("networkidle", timeout=60000)
                    await random_delay(*DELAY_RANGES["long"])
            
        except Exception as e:
            logging.error(f"Error checking for HTTP errors: {e}")
            # Continue anyway
            pass
        
        logging.info("Waiting for password field")
        try:
            await page.wait_for_selector(SELECTORS["password_field"], state="visible", timeout=60000)  # Increased timeout
            logging.info("Password field found, moving mouse")
            await move_mouse(page, (300, 600), (250, 400))
            await random_delay(*DELAY_RANGES["medium"])
        except Exception as e:
            logging.error(f"Error waiting for password field: {e}")
            # Take screenshot to debug the issue
            await page.screenshot(path="login_error.png")
            logging.info("Screenshot saved as login_error.png")
            # Try to continue anyway
            pass
        
        logging.info("Filling password field")
        try:
            # First verify the password field is still visible and focused
            password_field = await page.query_selector(SELECTORS["password_field"])
            if password_field and await password_field.is_visible():
                await password_field.focus()
                await random_delay(*DELAY_RANGES["short"])
                
                # Type password with humanized behavior
                for char in password:
                    await random_delay(50, 250)  # Longer delay for password typing
                    if random.random() < 0.15:  # 15% chance of typo
                        wrong_char = chr(random.randint(65, 90)) if char.isalpha() else chr(random.randint(48, 57))
                        await page.keyboard.press(wrong_char)
                        await random_delay(200, 500)
                        await page.keyboard.press('Backspace')
                    await page.keyboard.press(char)
                    await random_delay(50, 150)
                
                await random_delay(*DELAY_RANGES["long"])  # Longer pause before clicking sign in
                
                # Verify sign-in button is visible before clicking
                sign_in_button = await page.query_selector(SELECTORS["sign_in_button"])
                if sign_in_button and await sign_in_button.is_visible():
                    logging.info("Clicking sign-in button")
                    await move_mouse(page, (400, 700), (450, 550))
                    await random_delay(*DELAY_RANGES["medium"])
                    await sign_in_button.click(force=True)  # Force click to avoid potential overlay issues
                    await page.wait_for_load_state("networkidle", timeout=60000)
                    await random_delay(*DELAY_RANGES["long"])
                else:
                    logging.error("Sign-in button not visible after password entry")
                    await page.screenshot(path="sign_in_button_missing.png")
            else:
                logging.error("Password field not visible or focused")
                await page.screenshot(path="password_field_issue.png")
        except Exception as e:
            logging.error(f"Error during password submission: {e}")
            await page.screenshot(path="password_submission_error.png")
            # Continue and let the caller handle the error
    except Exception as e:
        logging.error(f"Error during login process: {e}")
        # Take a final screenshot before raising the exception
        try:
            await page.screenshot(path="login_process_error.png")
            logging.info("Final error screenshot saved as login_process_error.png")
        except:
            pass
        raise

async def handle_stay_signed_in_prompt(page: Page) -> bool:
    from antibot_evasion import AntiBotEvasion
    antibot = AntiBotEvasion()
    
    try:
        logging.info("Looking for 'Stay signed in' prompt")
        
        # Verify page state and handle potential rate limits
        if await antibot.handle_rate_limit(page):
            logging.warning("Rate limit detected during prompt handling")
            await page.reload(wait_until="networkidle")
            
        # Verify page is still open and ready
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception as e:
            logging.error(f"Page not ready for 'Stay signed in' prompt: {e}")
            return False
        
        # Check if page is still valid before proceeding
        try:
            await page.evaluate("false")
        except Exception as e:
            logging.error(f"Page appears to be closed: {e}")
            return False
        
        # Wait for either button with increased timeout and better error handling
        max_wait_time = 30000  # Increased from 15000
        button_found = False
        
        try:
            no_button = await page.wait_for_selector(SELECTORS["stay_signed_in_no"], 
                state="visible", timeout=max_wait_time)
            button_found = True
        except:
            try:
                yes_button = await page.wait_for_selector(SELECTORS["stay_signed_in_yes"],
                    state="visible", timeout=max_wait_time)
                button_found = True
            except:
                button_found = False
        
        if not button_found:
            logging.info("No 'Stay signed in' prompt detected after extended wait")
            return True
        
        # Human-like delay before interaction
        await random_delay(*DELAY_RANGES["long"])
        
        # Verify element is still present and clickable
        try:
            if no_button and await no_button.is_visible():
                await no_button.scroll_into_view_if_needed()
                await no_button.hover()
                await random_delay(*DELAY_RANGES["short"])
                await no_button.click(force=True)
            elif yes_button and await yes_button.is_visible():
                await yes_button.scroll_into_view_if_needed()
                await yes_button.hover()
                await random_delay(*DELAY_RANGES["short"])
                await yes_button.click(force=True)
        except Exception as e:
            logging.error(f"Error clicking 'Stay signed in' button: {e}")
            try:
                await page.screenshot(path="stay_signed_in_error.png")
                logging.info("Screenshot saved as stay_signed_in_error.png")
            except Exception as screenshot_error:
                logging.error(f"Failed to take screenshot: {screenshot_error}")
            return False
    except Exception as e:
        logging.error(f"Error handling 'Stay signed in' prompt: {e}")
        return False

async def verify_navigation(page: Page, expected_url: str, max_retries: int = 5) -> bool:
    """
    Verifica que la navegación ha sido exitosa comprobando la URL actual.
    Implementa una estrategia mejorada de reintentos y recuperación de errores.
    """
    from antibot_evasion import AntiBotEvasion
    antibot = AntiBotEvasion()
    
    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"Navigation verification attempt {attempt}/{max_retries}")
            
            # Check current URL pattern match
            current_url = await page.evaluate("window.location.href")
            if expected_url.lower() in current_url.lower():
                logging.info(f"Successfully navigated to {current_url}")
                return True
            
            # Handle potential rate limiting
            if await antibot.handle_rate_limit(page, attempt):
                logging.warning(f"Rate limited during navigation verification (attempt {attempt})")
                await page.reload(wait_until="networkidle")
                await random_delay(*DELAY_RANGES["long"])
                continue
            
            # Attempt recovery navigation
            logging.info(f"Redirecting to {expected_url} directly")
            await page.goto(expected_url, wait_until="networkidle", timeout=60000)
            await random_delay(*DELAY_RANGES["medium"])
            
            # Verify post-redirect state
            post_redirect_url = await page.evaluate("window.location.href")
            if expected_url.lower() in post_redirect_url.lower():
                return True
            
            # Session consistency check
            if attempt > 1 and not await page.query_selector(SELECTORS["username_field"]):
                logging.error("Session inconsistency detected, restarting flow")
                await page.context.clear_cookies()
                await page.goto(URL, wait_until="networkidle")
                return False
            
        except Exception as e:
            logging.error(f"Navigation verification error: {str(e)}")
            await page.screenshot(path=f"nav_error_attempt_{attempt}.png")
    
    logging.error(f"Failed to verify navigation after {max_retries} attempts")
    return False