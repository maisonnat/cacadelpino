import random
import math
import asyncio
import logging
from typing import Dict, List, Tuple, Union, Optional
from playwright.async_api import Page, ElementHandle

class HumanBehavior:
    @staticmethod
    async def random_delay(min_ms: int, max_ms: int):
        delay = random.randint(min_ms, max_ms) / 1000.0
        await asyncio.sleep(delay)

    @staticmethod
    def generate_bezier_curve(start: Dict[str, int], end: Dict[str, int], control_points: int) -> List[Dict[str, float]]:
        points = []
        for t in range(control_points + 1):
            t = t / control_points
            x = start['x'] * (1-t)**3 + 3 * end['x'] * t * (1-t)**2 + 3 * start['x'] * t**2 * (1-t) + end['x'] * t**3
            y = start['y'] * (1-t)**3 + 3 * end['y'] * t * (1-t)**2 + 3 * start['y'] * t**2 * (1-t) + end['y'] * t**3
            points.append({'x': x, 'y': y})
        return points

    @staticmethod
    async def move_mouse_naturally(page: Page, target_x: int, target_y: int):
        # Start from a reasonable position since we can't get current position
        # Use the target coordinates as reference to create a starting point
        start_x = target_x - random.randint(100, 200)
        start_y = target_y - random.randint(50, 150)
        
        # Ensure coordinates are not negative
        start_x = max(0, start_x)
        start_y = max(0, start_y)
        
        start = {'x': start_x, 'y': start_y}
        end = {'x': target_x, 'y': target_y}
        
        # Move to starting position first
        await page.mouse.move(start_x, start_y)
        await HumanBehavior.random_delay(50, 150)
        
        points = HumanBehavior.generate_bezier_curve(start, end, random.randint(5, 10))
        
        for point in points:
            await page.mouse.move(
                point['x'],
                point['y'],
                steps=random.randint(1, 5)
            )
            await HumanBehavior.random_delay(10, 50)

    @staticmethod
    async def type_humanized(page: Page, text: str, error_rate: float = 0.05, careful_mode: bool = False):
        """
        Simula escritura humana con errores ocasionales y correcciones.
        
        Args:
            page: Objeto Page de Playwright
            text: Texto a escribir
            error_rate: Probabilidad de cometer un error (0.0 a 1.0)
            careful_mode: Si es True, reduce la velocidad y aumenta las pausas
        """
        logging.info(f"Escribiendo texto de forma humanizada (modo cuidadoso: {careful_mode})")
        
        for char in text:
            # Ajustar delays según el modo
            typing_delay = random.randint(70, 300) if careful_mode else random.randint(50, 200)
            error_correction_delay = random.randint(300, 600) if careful_mode else random.randint(200, 400)
            
            # Posible error de tipeo
            if random.random() < error_rate:
                # Generar un carácter incorrecto cercano al teclado
                if char.isalpha():
                    # Para letras, usar caracteres cercanos en el teclado
                    keyboard_neighbors = {
                        'a': ['q', 'w', 's', 'z'],
                        's': ['a', 'd', 'w', 'e', 'z', 'x'],
                        # ... (se puede expandir con más mapeos de teclado)
                    }
                    if char.lower() in keyboard_neighbors:
                        wrong_char = random.choice(keyboard_neighbors[char.lower()])
                        if char.isupper():
                            wrong_char = wrong_char.upper()
                    else:
                        # Si no está en el mapa, usar un carácter aleatorio cercano en ASCII
                        wrong_char = chr(ord(char) + random.randint(-2, 2))
                else:
                    # Para números y símbolos
                    wrong_char = chr(ord(char) + random.randint(-1, 1))
                
                await page.keyboard.press(wrong_char)
                logging.debug(f"Simulando error de tipeo: '{wrong_char}' en lugar de '{char}'")
                await HumanBehavior.random_delay(error_correction_delay, error_correction_delay + 200)
                await page.keyboard.press('Backspace')
            
            # Escribir el carácter correcto
            await page.keyboard.press(char)
            await HumanBehavior.random_delay(typing_delay, typing_delay + 100)
            
            # Pausa ocasional como si estuviera pensando
            if random.random() < 0.03:
                await HumanBehavior.random_delay(500, 1200)

    @staticmethod
    async def scroll_naturally(page: Page, max_scroll_percentage: float = 1.0, read_mode: bool = False):
        """
        Realiza scroll de manera natural en la página.
        
        Args:
            page: Objeto Page de Playwright
            max_scroll_percentage: Porcentaje máximo de la página a scrollear (0.0 a 1.0)
            read_mode: Si es True, hace scroll más lento simulando lectura
        """
        height = await page.evaluate('document.body.scrollHeight')
        max_scroll = int(height * max_scroll_percentage)
        current_position = 0
        
        logging.info(f"Iniciando scroll natural hasta {max_scroll_percentage*100}% de la página")
        
        while current_position < max_scroll:
            # En modo lectura, scroll más pequeño y pausas más largas
            if read_mode:
                scroll_amount = random.randint(50, 150)
                pause_time = random.randint(800, 2500)  # Pausas más largas para "leer"
            else:
                scroll_amount = random.randint(100, 300)
                pause_time = random.randint(50, 150)
            
            current_position += scroll_amount
            
            # Ocasionalmente hacer una pausa más larga como si algo llamara la atención
            if random.random() < 0.1:
                extra_pause = random.randint(1000, 3000)
                logging.debug(f"Pausa extra en scroll: {extra_pause}ms")
                await HumanBehavior.random_delay(extra_pause, extra_pause + 500)
            
            await page.evaluate(f'window.scrollTo(0, {min(current_position, max_scroll)})')
            await HumanBehavior.random_delay(pause_time, pause_time + 100)
            
            # Ocasionalmente hacer scroll hacia arriba un poco, como si se hubiera pasado
            if random.random() < 0.05 and current_position > 200:
                back_amount = random.randint(50, 150)
                logging.debug(f"Scroll hacia atrás: {back_amount}px")
                current_position -= back_amount
                await page.evaluate(f'window.scrollTo(0, {current_position})')
                await HumanBehavior.random_delay(300, 800)
    @staticmethod
    async def click_element_naturally(page: Page, selector: str, force: bool = False) -> bool:
        """
        Hace clic en un elemento de manera natural, moviendo el ratón de forma realista.
        
        Args:
            page: Objeto Page de Playwright
            selector: Selector CSS del elemento a hacer clic
            force: Si es True, fuerza el clic aunque el elemento no sea visible
            
        Returns:
            bool: True si el clic fue exitoso, False en caso contrario
        """
        try:
            # Esperar a que el elemento sea visible
            element = await page.wait_for_selector(selector, state='visible', timeout=10000)
            if not element:
                logging.warning(f"Elemento no encontrado o no visible: {selector}")
                return False
            
            # Obtener las coordenadas del elemento
            bbox = await element.bounding_box()
            if not bbox:
                logging.warning(f"No se pudo obtener el bounding box del elemento: {selector}")
                return False
            
            # Calcular un punto aleatorio dentro del elemento
            target_x = bbox['x'] + random.uniform(5, bbox['width'] - 5)
            target_y = bbox['y'] + random.uniform(5, bbox['height'] - 5)
            
            # Mover el ratón de forma natural
            await HumanBehavior.move_mouse_naturally(page, target_x, target_y)
            
            # Pequeña pausa antes de hacer clic
            await HumanBehavior.random_delay(300, 800)
            
            # Hacer clic
            if force:
                await element.click(force=True)
            else:
                await element.click()
                
            logging.info(f"Clic natural realizado en elemento: {selector}")
            return True
            
        except Exception as e:
            logging.error(f"Error al hacer clic en elemento {selector}: {str(e)}")
            return False

    @staticmethod
    async def hover_and_observe(page: Page, selector: str, observation_time_ms: int = None) -> bool:
        """
        Simula que el usuario pasa el ratón sobre un elemento y lo observa.
        
        Args:
            page: Objeto Page de Playwright
            selector: Selector CSS del elemento
            observation_time_ms: Tiempo en ms para "observar" el elemento (None = aleatorio)
            
        Returns:
            bool: True si la acción fue exitosa
        """
        try:
            element = await page.wait_for_selector(selector, state='visible', timeout=5000)
            if not element:
                return False
                
            bbox = await element.bounding_box()
            if not bbox:
                return False
                
            # Mover el ratón al elemento
            target_x = bbox['x'] + random.uniform(5, bbox['width'] - 5)
            target_y = bbox['y'] + random.uniform(5, bbox['height'] - 5)
            await HumanBehavior.move_mouse_naturally(page, target_x, target_y)
            
            # "Observar" el elemento
            if observation_time_ms is None:
                observation_time_ms = random.randint(500, 3000)
                
            await HumanBehavior.random_delay(observation_time_ms, observation_time_ms + 500)
            return True
            
        except Exception as e:
            logging.error(f"Error al hacer hover sobre elemento {selector}: {str(e)}")
            return False

    @staticmethod
    async def simulate_reading(page: Page, duration_ms: int = None):
        """
        Simula que el usuario está leyendo el contenido de la página.
        
        Args:
            page: Objeto Page de Playwright
            duration_ms: Duración en ms de la simulación (None = basado en contenido)
        """
        try:
            # Estimar la cantidad de texto en la página
            text_length = await page.evaluate("""() => {
                const textElements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, div');
                let totalLength = 0;
                textElements.forEach(el => {
                    if (el.innerText) totalLength += el.innerText.length;
                });
                return totalLength;
            }""")
            
            # Calcular tiempo de lectura basado en ~200 caracteres por minuto
            if duration_ms is None:
                reading_time = max(2000, min(30000, text_length * 15))  # Entre 2s y 30s
            else:
                reading_time = duration_ms
                
            logging.info(f"Simulando lectura durante {reading_time/1000} segundos")
            
            # Hacer scroll lento mientras "lee"
            await HumanBehavior.scroll_naturally(page, max_scroll_percentage=0.7, read_mode=True)
            
            # Simular movimientos ocasionales del ratón como si siguiera el texto
            scroll_position = await page.evaluate('window.scrollY')
            viewport_height = await page.evaluate('window.innerHeight')
            
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, 700)
                y = random.randint(int(scroll_position + 100), 
                                  int(scroll_position + viewport_height - 100))
                await HumanBehavior.move_mouse_naturally(page, x, y)
                await HumanBehavior.random_delay(800, 2000)
                
        except Exception as e:
            logging.error(f"Error al simular lectura: {str(e)}")
    @staticmethod
    async def move_mouse_with_zigzag(page: Page, target_x: int, target_y: int):
        """Simula movimiento del ratón con patrón zigzag para mayor naturalidad."""
        # Calcular puntos intermedios con zigzag
        points = []
        steps = random.randint(4, 7)
        start_x = random.randint(50, 150)
        start_y = random.randint(50, 150)
        
        for i in range(steps):
            progress = i / (steps - 1)
            # Posición base en la línea recta hacia el objetivo
            base_x = start_x + (target_x - start_x) * progress
            base_y = start_y + (target_y - start_y) * progress
            
            # Añadir zigzag con amplitud decreciente
            zigzag_amplitude = (1 - progress) * random.randint(20, 40)
            if i % 2 == 0:
                points.append({
                    'x': base_x + zigzag_amplitude,
                    'y': base_y - zigzag_amplitude
                })
            else:
                points.append({
                    'x': base_x - zigzag_amplitude,
                    'y': base_y + zigzag_amplitude
                })
            
            # Añadir micro-pausas aleatorias
            if random.random() < 0.3:
                points.append(points[-1])  # Repetir el último punto para simular pausa
        
        # Añadir punto final
        points.append({'x': target_x, 'y': target_y})
        
        # Ejecutar el movimiento
        await page.mouse.move(start_x, start_y)
        await HumanBehavior.random_delay(100, 300)
        
        for point in points:
            await page.mouse.move(
                point['x'],
                point['y'],
                steps=random.randint(2, 4)
            )
            await HumanBehavior.random_delay(20, 80)

    @staticmethod
    async def handle_captcha(page: Page) -> bool:
        """
        Detecta y maneja posibles CAPTCHAs en la página.
        
        Args:
            page: Objeto Page de Playwright
            
        Returns:
            bool: True si se detectó y manejó un CAPTCHA, False en caso contrario
        """
        # Esta es una implementación básica que solo detecta la presencia
        # Para una solución real, se necesitaría integrar un servicio de resolución de CAPTCHAs
        
        captcha_selectors = [
            'iframe[src*="recaptcha"]',
            'iframe[src*="captcha"]',
            '.g-recaptcha',
            '#captcha',
            '[id*="captcha"]',
            '[class*="captcha"]'
        ]
        
        for selector in captcha_selectors:
            captcha = await page.query_selector(selector)
            if captcha:
                logging.warning(f"¡CAPTCHA detectado! Selector: {selector}")
                # Aquí se implementaría la lógica para resolver el CAPTCHA
                # Por ahora, solo registramos y esperamos
                await HumanBehavior.random_delay(5000, 10000)
                return True
                
        return False