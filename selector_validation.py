import logging
from playwright.async_api import Page

async def validate_selector(page: Page, selector: str, timeout: int = 5000) -> bool:
    """
    Comprueba la existencia y visibilidad de un selector CSS antes de interactuar con él.
    
    Args:
        page: Objeto Page de Playwright
        selector: Selector CSS a validar
        timeout: Tiempo máximo de espera en milisegundos
        
    Returns:
        bool: True si el selector existe y es visible, False en caso contrario
    """
    try:
        await page.wait_for_selector(selector, state='visible', timeout=timeout)
        return True
    except Exception as e:
        logging.warning(f"Selector {selector} no encontrado: {e}")
        return False