from .base import Screen, HEADER_HEIGHT

class HomeScreen(Screen):
    def __init__(self, gui):
        super().__init__(gui)

        self.btn_start = self.add_button(
            rect=(0, 0,
                320, 240),
            on_click=self._on_start
        )

    def _on_start(self):
        self.gui.start_robot(do_execute=True)
        self.gui.set_screen("mapping")


    def render_body(self, draw, header_h: int):
        draw.text((113, 127), f"Résoudre", fill=(255, 0, 0))


