from .base import Screen, HEADER_HEIGHT, COLORS

class MappingScreen(Screen):
    def __init__(self, gui):
        super().__init__(gui)

    def render_body(self, draw, header_h: int):
        st = self.gui.rbx_store.get()

        face_size = 78
        x, y = 3, 2

        state = self.get_init_colors()

        face = None
        if "Captur" in st.line2: face = st.line2.split(" ")[1]

        self.draw_cube_pattern(draw, x, y, face_size, state["U"], state["L"], state["F"], state["R"], state["D"], state["B"], selected=face)

        current_step = "c"

        draw.text((174, 7),  "Scan       : 01:05:14", font=self.gui.font_small,
                  fill= COLORS['RED'] if "s" in current_step else COLORS['BLACK'])

        draw.text((174, 17),  "Calcul     : 00:02:34", font=self.gui.font_small,
                  fill= COLORS['RED'] if "c" in current_step else COLORS['BLACK'])

        draw.text((174, 27),  "Résolution : --:--:--", font=self.gui.font_small,
                  fill= COLORS['RED'] if "r" in current_step else COLORS['BLACK'])

        draw.text((174, 37),  "────────────", font=self.gui.font_small, fill=COLORS['BLACK'])
        draw.text((174, 47),  "Total      : 00:07:48", font=self.gui.font_small, fill=COLORS['BLACK'])


    def get_init_colors(self):
        """
        Simmule la récupération des couleurs depuis la caméra

        Returns
        -------
        dict
            DESCRIPTION.

        """
        return {
            "U" : (COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY']),
            "D" : (COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY']),
            "F" : (COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY']),
            "B" : (COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY']),
            "L" : (COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY']),
            "R" : (COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY'], COLORS['GRAY']),
            }
