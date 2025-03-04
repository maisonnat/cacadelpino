import logging
from playwright.async_api import Page
from humanization import move_mouse, random_delay, human_scroll
from config import SELECTORS, DELAY_RANGES

async def complete_daily_activities(page: Page) -> int:
    logging.info("Starting daily activities completion")
    try:
        # Mover el ratón y desplazar la página
        await move_mouse(page, (100, 500), (100, 300))
        await human_scroll(page, 200)
        await random_delay(*DELAY_RANGES["medium"])
        
        # Import and use the selector validation function
        from selector_validation import validate_selector
        
        # Validate daily set cards before interaction
        if not await validate_selector(page, SELECTORS["daily_set_cards"], timeout=15000):
            logging.error("Daily set cards not found or not visible")
            return 0
        
        # Obtener todas las tarjetas del Daily Set y filtrar a las 3 primeras válidas
        daily_set_cards = await page.query_selector_all(SELECTORS["daily_set_cards"])
        completed_count = 0
        
        if len(daily_set_cards) != 3:
            logging.warning(f"Expected 3 daily set activities, but found {len(daily_set_cards)}")
        
        for i, card in enumerate(daily_set_cards[:3], start=1):
            try:
                await random_delay(*DELAY_RANGES["short"])  # Pausa como si estuviera leyendo cada tarjeta
                activity_name = f'Activity {i}'
                
                # Intentar extraer el nombre de la actividad
                heading_element = await card.query_selector(SELECTORS["activity_title"])
                if heading_element:
                    text = await heading_element.inner_text()
                    if text and text.strip():
                        activity_name = text.strip()
                else:
                    icon_element = await card.query_selector(SELECTORS["activity_icon"])
                    if icon_element:
                        aria_label = await icon_element.get_attribute('aria-label')
                        if aria_label and aria_label.strip():
                            activity_name = aria_label.strip()
                
                logging.info(f"Processing daily activity: {activity_name}")
                
                # Buscar el ícono "+10"
                plus_10_icon = await card.query_selector(SELECTORS["points_10"])
                if plus_10_icon:
                    logging.info(f"Activity {activity_name} has +10 points, clicking...")
                    await move_mouse(page, (200, 600), (150, 350))
                    await random_delay(*DELAY_RANGES["short"])
                    await card.click()
                    await random_delay(*DELAY_RANGES["medium"])
                    completed_count += 1
                    logging.info(f"Completed {activity_name} successfully")
                else:
                    logging.info(f"Activity {activity_name} doesn't have +10 points, skipping")
            except Exception as e:
                logging.error(f"Error processing daily activity {activity_name}: {e}")
        
        logging.info(f"Completed {completed_count} daily activities")
        return completed_count
    except Exception as e:
        logging.error(f"Error in daily activities: {str(e)}")
        return 0

async def complete_more_activities(page: Page) -> int:
    logging.info("Starting more activities completion")
    try:
        # Mover el ratón y desplazar más abajo
        await move_mouse(page, (100, 500), (100, 300))
        await human_scroll(page, 400)
        await random_delay(*DELAY_RANGES["medium"])
        
        # Esperar que "More Activities" sea visible
        await page.wait_for_selector(SELECTORS["more_activities_cards"], state='visible', timeout=15000)
        
        more_activities_cards = await page.query_selector_all(SELECTORS["more_activities_cards"])
        completed_count = 0
        
        for i, card in enumerate(more_activities_cards, start=1):
            try:
                await random_delay(*DELAY_RANGES["short"])
                activity_name = f'Activity {i}'
                
                # Intentar extraer el nombre de la actividad
                heading_element = await card.query_selector(SELECTORS["activity_title"])
                if heading_element:
                    text = await heading_element.inner_text()
                    if text and text.strip():
                        activity_name = text.strip()
                else:
                    icon_element = await card.query_selector(SELECTORS["activity_icon"])
                    if icon_element:
                        aria_label = await icon_element.get_attribute('aria-label')
                        if aria_label and aria_label.strip():
                            activity_name = aria_label.strip()
                
                logging.info(f"Processing more activity: {activity_name}")
                
                # Buscar íconos con +50, +5 o +10
                points = 0
                for selector, value in [(SELECTORS["points_50"], 50), (SELECTORS["points_10"], 10), (SELECTORS["points_5"], 5)]:
                    plus_icon = await card.query_selector(selector)
                    if plus_icon:
                        points = value
                        break
                
                if points > 0:
                    logging.info(f"Activity {activity_name} has +{points} points, clicking...")
                    await move_mouse(page, (200, 600), (150, 350))
                    await random_delay(*DELAY_RANGES["short"])
                    await card.click()
                    await random_delay(*DELAY_RANGES["medium"])
                    
                    # Si es una actividad con +50, buscar y cerrar el pop-up
                    if points == 50:
                        logging.info(f"Waiting for popup after completing +50 activity: {activity_name}")
                        await random_delay(*DELAY_RANGES["long"])
                        close_button = await page.query_selector(SELECTORS["close_popup"])
                        if close_button:
                            await move_mouse(page, (400, 700), (300, 500))
                            await random_delay(*DELAY_RANGES["medium"])
                            await close_button.click()
                            logging.info(f"Closed popup for {activity_name} successfully")
                            await random_delay(*DELAY_RANGES["medium"])
                        else:
                            logging.warning(f"No close button found for {activity_name} popup")
                    
                    completed_count += 1
                    logging.info(f"Completed {activity_name} with +{points} points successfully")
                else:
                    logging.info(f"Activity {activity_name} has no points, skipping")
            except Exception as e:
                logging.error(f"Error processing more activity {activity_name}: {e}")
        
        logging.info(f"Completed {completed_count} more activities")
        return completed_count
    except Exception as e:
        logging.error(f"Error in more activities: {str(e)}")
        return 0