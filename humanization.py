import random
from playwright.async_api import Page
from common_utils import random_delay, move_mouse

async def human_scroll(page: Page, scroll_amount: int) -> None:
    """Realiza un desplazamiento natural con un retraso posterior."""
    await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
    await random_delay(500, 1500)

async def human_type(page: Page, selector: str, text: str, error_rate: float = 0.05) -> None:
    """Escribe texto carácter por carácter como lo haría un humano, con posibles errores y correcciones."""
    await page.focus(selector)
    
    # Clear any existing text first
    await page.evaluate(f"document.querySelector('{selector}').value = ''")
    await random_delay(100, 300)
    
    for i, char in enumerate(text):
        # Posibilidad de cometer un error de escritura
        if random.random() < error_rate and i < len(text) - 1:
            # Escribir un carácter incorrecto (cercano en el teclado)
            wrong_char = get_nearby_key(char)
            await page.keyboard.press(wrong_char)
            await random_delay(50, 200)
            
            # Borrar el error
            await page.keyboard.press("Backspace")
            await random_delay(200, 400)  # Pausa más larga al corregir
        
        # Escribir el carácter correcto
        await page.keyboard.type(char, delay=random.randint(50, 150))
        
        # Ocasionalmente hacer una pausa más larga (como pensando)
        if random.random() < 0.1:
            await random_delay(300, 800)
    
    # Verify text was entered correctly
    await random_delay(200, 500)
def get_nearby_key(char: str) -> str:
    """Devuelve una tecla cercana a la tecla dada en un teclado QWERTY."""
    keyboard_layout = {
        'a': ['s', 'q', 'z', 'w'],
        'b': ['v', 'n', 'g', 'h'],
        'c': ['x', 'v', 'd', 'f'],
        'd': ['s', 'f', 'e', 'r', 'c', 'x'],
        'e': ['w', 'r', 'd', 's'],
        'f': ['d', 'g', 'r', 't', 'v', 'c'],
        'g': ['f', 'h', 't', 'y', 'b', 'v'],
        'h': ['g', 'j', 'y', 'u', 'n', 'b'],
        'i': ['u', 'o', 'k', 'j'],
        'j': ['h', 'k', 'u', 'i', 'm', 'n'],
        'k': ['j', 'l', 'i', 'o', ',', 'm'],
        'l': ['k', ';', 'o', 'p', '.', ','],
        'm': ['n', ',', 'j', 'k'],
        'n': ['b', 'm', 'h', 'j'],
        'o': ['i', 'p', 'k', 'l'],
        'p': ['o', '[', 'l', ';'],
        'q': ['w', 'a', '1', '2'],
        'r': ['e', 't', 'd', 'f'],
        's': ['a', 'd', 'w', 'e', 'z', 'x'],
        't': ['r', 'y', 'f', 'g'],
        'u': ['y', 'i', 'h', 'j'],
        'v': ['c', 'b', 'f', 'g'],
        'w': ['q', 'e', 'a', 's'],
        'x': ['z', 'c', 's', 'd'],
        'y': ['t', 'u', 'g', 'h'],
        'z': ['a', 'x', 's'],
        '0': ['9', '-'],
        '1': ['2', 'q'],
        '2': ['1', '3', 'q', 'w'],
        '3': ['2', '4', 'w', 'e'],
        '4': ['3', '5', 'e', 'r'],
        '5': ['4', '6', 'r', 't'],
        '6': ['5', '7', 't', 'y'],
        '7': ['6', '8', 'y', 'u'],
        '8': ['7', '9', 'u', 'i'],
        '9': ['8', '0', 'i', 'o'],
        '.': [',', '/', 'l', ';'],
        ',': ['m', '.', 'k', 'l'],
        ';': ['l', "'", 'p', '['],
        "'": [';', '\\', '[', ']'],
        '[': ['p', ']', ';', "'"],
        ']': ['[', '\\', "'"],
        '\\': [']', "'"],
        '/': ['.', 'l', ';'],
        '-': ['0', '='],
        '=': ['-', 'p', '['],
        ' ': ['c', 'v', 'b', 'n', 'm']
    }
    
    char = char.lower()
    if char in keyboard_layout and keyboard_layout[char]:
        return random.choice(keyboard_layout[char])
    return char  # Si no hay teclas cercanas definidas, devolver la misma tecla