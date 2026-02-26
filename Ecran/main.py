#### GALDRIC PREFIXE PAR Ecran ####

from Ecran.screens.home import HomeScreen
from Ecran.screens.mapping import MappingScreen
#from Ecran.screens.parameters import ParametersScreen
#from Ecran.screens.none import NoneScreen

from Ecran.tools.network import NetworkTools
from Ecran.tools.system import SystemTools

from Ecran.hardware.touchv2 import TouchHandler2

import signal
import threading

from luma.core.interface.serial import spi
from luma.lcd.device import ili9341
from PIL import ImageFont

#### GALDRIC LIGNE RAJOUTE POUR LIEN ROBOT ####
from rbx_ui_state_store import RBXScreenStateStore
from rbx_ui_listener import make_rbx_ui_listener
from rbx_ui_runner import RBXPipelineRunner
from robot_solver import RobotCubeSolver
from Ecran.screens.pipeline import PipelineScreen
#### GALDRIC FIN LIGNE RAJOUTE POUR LIEN ROBOT ####


import time

GPIO_DC = 25
GPIO_RST = 24

class RubikGUI:

    def __init__(self):
        import Ecran.screens.base as b
        print("[BASE FILE]", b.__file__)
        print("[HAS last_touch]", "last_touch" in b.Screen.__init__.__code__.co_names)        
        #self.serial = spi(port=0, device=0, gpio_DC=GPIO_DC, gpio_RST=GPIO_RST)
        self.serial = spi(port=0, device=0, gpio_DC=GPIO_DC)  #### MOMODIFICATION POUR ENLEVER LE RESET !!! Le restart fonctionne
        self.device = ili9341(self.serial)
        self._last_press_ts = 0.0
        self._last_release_ts = 0.0
        self._stop_event = threading.Event()
        
        self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=11)
        
        self.net = NetworkTools()
        self.sys = SystemTools()
        
        self.current_screen_name = "home"
        #self.current_screen_name = "parameters" ### GALDRIC (rem chatgpt) si on veut voir directement start mettre ==> self.current_screen_name = "home"
        self.screens = {
            "home": HomeScreen(self),
            "mapping": MappingScreen(self),
            #"debug": DebugScreen(self),  #### GALDRIC PAS DE DEBUG SCREEN ?
            #"parameters": ParametersScreen(self),
            "pipeline": PipelineScreen(self), #### GALDRIC AJOUT DE L'ECRAN DU PIPELINE (permet de visualiser l'avanncemment du robot)            
            #"none": NoneScreen(self),
        }
        
        # Init tactile avec callbacks séparés
        #self.touch = TouchHandler2(
        #    on_press=self.on_touch_press,
        #    on_release=self.on_touch_release,
        #    on_move=self.on_touch_move,
        #    width=self.device.width,
        #    height=self.device.height,
        #    rotate=1          # <- test 0/1/2/3         
        #)

        #self.touch = TouchHandler2(
        #    on_press=lambda x, y: print("[T] PRESS", x, y),
        #    on_release=lambda x, y: print("[T] RELEASE", x, y),
        #    on_move=lambda x, y: print("[T] MOVE", x, y),
        #    width=self.device.width,
        #    height=self.device.height,
        #    rotate=1,
        #    move_threshold_px=1,
        #)

        print("[DBG] on_touch_press=", self.on_touch_press, "callable?", callable(self.on_touch_press))
        print("[DBG] on_touch_release=", self.on_touch_release, "callable?", callable(self.on_touch_release))
        print("[DBG] on_touch_move=", self.on_touch_move, "callable?", callable(self.on_touch_move))
        self.touch = TouchHandler2(
            on_press=self.on_touch_press,
            on_release=self.on_touch_release,
            on_move=self.on_touch_move,
            width=self.device.width,
            height=self.device.height,
            rotate=1,
            move_threshold_px=1,
        )

        #self.touch = TouchHandler2(
        #    on_press=self._dbg_press,
        #    on_release=self._dbg_press,
        #    on_move=self._dbg_press,
        #    width=self.device.width,
        #    height=self.device.height,
        #    rotate=1,
        #    move_threshold_px=1,
        #)
                 
        self.touch.start()

        ### GALDRIC DEBUT AJOUT ###
        # RBX UI state (thread-safe)
        self.rbx_store = RBXScreenStateStore()
        self.rbx_listener = make_rbx_ui_listener(self.rbx_store)

        # Solver + runner (thread)
        self.solver = RobotCubeSolver(image_folder="tmp", debug="text")
        self.runner = RBXPipelineRunner(self.solver)
        ### GALDRIC FIN AJOUT ###        

    #### GALDRIC FONCTIONS POUR APPELER LE ROBOT ####
    def start_robot(self, do_execute=True):
        print("[HOME] start_robot")
        # lance le pipeline en thread + progress vers rbx_listener
        self.set_screen("pipeline")
        self.runner.start(
            do_solve=True,
            do_execute=do_execute,
            auto_calibrate=False,
            progress_callback=self.rbx_listener
        )
    def stop_robot(self):
        # STOP immédiat (emergency_stop / stop_flag.set)
        self.runner.estop()
    def robot_state(self):
        return self.rbx_store.get()
    def robot_running(self):
        return self.runner.is_running()
    #### GALDRIC FIN FONCTIONS POUR APPELER LE ROBOT ####
    def _dbg_press(self, x, y):
        print("[DBG] PRESS", x, y)
        
    #def on_touch_press(self, x, y):
    #    print("[GUI] PRESS", x, y, "screen=", self.current_screen_name)

    #def on_touch_release(self, x, y):
    #    print("[GUI] RELEASE", x, y, "screen=", self.current_screen_name)

    #def on_touch_move(self, x, y):
    #    print("[GUI] MOVE", x, y, "screen=", self.current_screen_name)


    def on_touch_press(self, x, y):
        print("[GUI] PRESS", x, y, "screen=", self.current_screen_name)
        screen = self.screens.get(self.current_screen_name)
        if screen:
            screen.on_touch_press(x, y)

    def on_touch_release(self, x, y):
        print("[GUI] RELEASE", x, y, "screen=", self.current_screen_name)
        screen = self.screens.get(self.current_screen_name)
        if screen:
            screen.on_touch_release(x, y)

    def on_touch_move(self, x, y):
        # print("[GUI] MOVE", x, y, "screen=", self.current_screen_name)  # tu peux laisser/commenter
        screen = self.screens.get(self.current_screen_name)
        if screen:
            screen.on_touch_move(x, y)      

    def signal_handler(self, sig, frame):
        """Gère SIGTERM de systemd"""
        print("Arrêt demandé (SIGTERM/SIGINT)...")
        self._stop_event.set()
    
    def set_screen(self, name: str):
        if name in self.screens:
            self.current_screen_name = name
    
    def render(self):
        screen = self.screens.get(self.current_screen_name)
        if not screen:
            print("[RENDER] unknown screen:", self.current_screen_name)
            return
        try:
            # debug: quel écran est rendu
            # print("[RENDER]", self.current_screen_name, type(screen).__name__)
            img = screen.render()
            self.device.display(img)
        except Exception as e:
            print("[RENDER] crash on screen:", self.current_screen_name, repr(e))
    
    def cleanup(self):
        """Nettoyage GPIO/écran"""
        print("Nettoyage LCD/GPIO...")
        self.touch.cleanup()
        
        try:
            self.device.clear()
        except:
            pass
        
        self.serial.cleanup()
    
    def run(self):
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            while not self._stop_event.is_set():
                time.sleep(0.1)
                self.render()
        finally:
            self.cleanup()

if __name__ == "__main__":
    app = None
    try:
        app = RubikGUI()
        app.run()
    except KeyboardInterrupt:
        pass
    finally:
        if app:
            app.cleanup()
