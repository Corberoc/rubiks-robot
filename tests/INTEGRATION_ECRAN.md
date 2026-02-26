PLAN INTEGRATION
----------------
ATTENTION ==> Ne pas écraser les fichiers Ecran/main.py, Ecran/screns/home.py
    Les modifications sont à faire à la "main"
    Le fichier Ecran/screns/pipeline.py est nouveau

DEBUT
-----
0)Vérifier que Ecran/main.py existe bien (avec un e Majsucule)
	Attention si e minuscule il faut changer le fichier 9_main.sh
		==> Ecran/main.py et MODULE="Ecran.main"
		==> if [ ! -f "Ecran/main.py" ]
	Attendu : pas d’erreur “module not found”, pas d’erreur “File not found”
1)Ajouter le fichier pipeline.py dans Ecran/screens
2) Rajouter le fichier 9_main.sh à la racine
3) faire un chmod a+x *.sh
4) Rajouter les fichiers suivant à la racine si ils n'existent pas 
	- rbx_ui_adapter.py
	- rbx_ui_callback.py
	- rbx_ui_contracts.py
	- rbx_ui_listener.py
	- rbx_ui_runner.py
	- rbx_ui_state_store.py
	- rbx_ui_test_console.py
5) MODIFICATIONS des fichiers existants 
5.1) Fichier Ecran/main.py
	Reporter toutes les modification où est écrit "GALDRIC" (attention il y a GALDRIC et GALDRIC FIN)
	Il faut ajouter des blocs GALDRIC jusqu'à GALDRIC FIN
5.2) Fichier Ecran/screens/home.py
	Ajout d'un bouton Start
	Reporter toutes les modification où est écrit "GALDRIC" (attention il y a GALDRIC et GALDRIC FIN)
	Il faut ajouter des blocs GALDRIC jusqu'à GALDRIC FIN
6) Mette à jour les 2 fichiers README.md et INTEGRATION_ECRAN.md à la racine
FIN
---


RESUME CHAT GPT ==>
0) Vérifs “fichiers”
	Ecran/main.py existe bien (casse Linux) 
	Ecran/screens/pipeline.py existe bien 
	pipeline
	Ton script 9_main.sh pointe bien vers Ecran.main et vérifie Ecran/main.py
1) Lancement 
	chmod +x 9_main.sh
	./9_main.sh
	Attendu : pas d’erreur “module not found”, pas d’erreur “File not found”.
2) Écran affiche quelque chose
	Tu dois voir l’UI (menu / settings / start).
	Si écran noir → problème hardware/driver/luma (pas ton intégration robot).
3)START fonctionne
	Appuie sur START (bouton ajouté dans HomeScreen) 
	Attendu :changement d’écran vers PipelineScreen (car start_robot() fait set_screen("pipeline"))
4) Pipeline se lance réellement
	Sur la console, tu dois voir des logs du pipeline (ou au minimum pas d’exception).
	Si rien ne bouge à l’écran, vérifie que runner.start(... progress_callback=self.rbx_listener) est bien appelé.
5) L’écran Pipeline se met à jour
	Dans PipelineScreen, l’état affiché vient de : st = self.app.rbx_store.get()
	Attendu : line1/line2/pct changent pendant capture/detection/solve.
6) STOP (optionnel)
	Tu as déjà le bouton STOP à l’écran :
	affiche “STOP”
	appelle self.app.stop_robot() (=> runner.estop())
