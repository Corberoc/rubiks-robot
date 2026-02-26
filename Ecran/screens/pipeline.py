# =============================================================================
#  Ecran/screens/pipeline.py
#  ------------------------
#  Objectif :
#     Définir l’écran “Pipeline” de l’interface embarquée : un rendu **simple,
#     lisible et temps-réel** de l’état du solveur (étape, message, progression).
#
#     Cet écran :
#       - récupère le **snapshot d’état** du robot via `self.app.robot.get_state()`,
#       - dessine une UI minimale avec Pillow (PIL) :
#           * 2 lignes de statut (line1 / line2),
#           * une barre de progression (pct 0.0 → 1.0),
#           * des “boutons” texte (HOME / STOP) en bas,
#       - gère en option des zones tactiles (touch release) pour naviguer / arrêter.
#
#  Rôle dans l’architecture UI :
#     [RobotController] ----> RBXScreenStateStore ----> (get_state)
#             |                                        |
#             +-- events pipeline (listeners)          v
#     [pipeline.py]  : affiche l’état courant (polling léger) + actions UI
#
#  Méthodes principales :
#     - render() -> PIL.Image
#         Construit une image RGB de la taille de l’écran et y dessine :
#           * texte : `st.line1`, `st.line2`
#           * barre : `st.pct` clampée entre 0 et 1
#           * repères : HOME / STOP
#
#     - on_touch_release(x, y)
#         Interprète des “zones” en bas de l’écran :
#           * bas-gauche  -> retour HOME (`self.app.set_screen("home")`)
#           * bas-droite  -> STOP si `self.app.robot.stop()` existe
#         (Optionnel : utile si ton matériel est tactile ; sinon peut rester no-op)
#
#  Convention de l’état affiché :
#     `st` provient du store (snapshot thread-safe) et expose typiquement :
#       - st.line1 : titre / étape courante (“Capture…”, “Solve…”, etc.)
#       - st.line2 : sous-message / détail (“Face U (1/6)”, “AWB lock…”, etc.)
#       - st.pct   : progression normalisée 0.0..1.0
#
#  Dépendances :
#     - Pillow : Image, ImageDraw (dessin 2D)
#     - app/device : `self.app.device.size`, polices `self.app.font_small`
#     - RobotController : `get_state()` (et `stop()` si tu l’implémentes)
#
#  Notes d’intégration :
#     - Le rendu est volontairement “stateless” : à chaque frame on redessine tout.
#     - La barre clamp `pct` évite les débordements si un event dépasse [0..1].
#     - Pour un STOP réel, implémenter `RobotController.stop()` côté robot
#       (E-STOP / stop_flag) et l’exposer ici via `hasattr(self.app.robot, "stop")`.
# =============================================================================

from PIL import Image, ImageDraw
from Ecran.screens.base import Screen

class PipelineScreen(Screen):

    def __init__(self, app):
        super().__init__(app)  # app = gui
        self.app = app

    def render_body(self, draw, header_h):
        st = self.app.rbx_store.get()
        w, h = self.app.device.size

        draw.rectangle([(0, 0), (w, h)], fill=(0, 0, 0))  # fond noir

        draw.text((w // 2 - 50, 10), "RUBIK SOLVER", font=self.app.font_small, fill=(255, 255, 0))
        draw.text((10, 30), st.line1, font=self.app.font_small, fill=(255, 255, 255))
        draw.text((10, 50), st.line2, font=self.app.font_small, fill=(200, 200, 200))

        bx, by = 10, h - 25
        bw, bh = w - 20, 12
        draw.rectangle([bx, by, bx + bw, by + bh], outline=(120, 120, 120))
        fw = int(bw * max(0.0, min(1.0, st.pct)))
        draw.rectangle([bx, by, bx + fw, by + bh], fill=(255, 255, 255))

        draw.text((10, h - 50), "HOME", font=self.app.font_small, fill=(180, 180, 255))
        draw.text((w - 60, h - 50), "STOP", font=self.app.font_small, fill=(255, 180, 180))

    def on_touch_release(self, x, y):
        w, h = self.app.device.size
        if y > h - 60 and x < 90:
            self.app.set_screen("home")
        if y > h - 60 and x > w - 90:
            if hasattr(self.app, "stop_robot"):
                self.app.stop_robot()
                

