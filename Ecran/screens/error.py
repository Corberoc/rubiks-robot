from .base import Screen

class HomeScreen(Screen):
    def __init__(self, gui):
        super().__init__(gui)

        self.btn_home = self.add_button(
            rect=(0, 0,
                320, 240),
            on_click=self.gui.set_screen("error")
        )

    def render_body(self, draw, header_h: int):
        draw.text((113, 127), f"Résoudre", fill=(255, 0, 0))
