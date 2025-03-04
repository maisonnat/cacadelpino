# ... existing imports ...
from utils.element_locator import ElementLocator

class AutomationCore:
    def __init__(self):
        self.locator = ElementLocator()
        self.metadata_store = {}
    
    async def handle_password_field(self):
        metadata = {}
        password_field = await self.locator.find(
            self.page, 
            {'css': '#password', 'xpath': '//input[@type="password"]', 'text': 'Contraseña'},
            metadata
        )
        
        if password_field:
            self.metadata_store['password_field'] = metadata
            await password_field.type("your_password")
        else:
            self._handle_missing_element(metadata)
    
    def _handle_missing_element(self, metadata):
        logger.error(f"Element detection failed. Collected metadata: {metadata}")
        # Implement fallback logic here