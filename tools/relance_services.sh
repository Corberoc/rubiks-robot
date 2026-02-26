sudo systemctl daemon-reload
sudo systemctl reset-failed rbx-app.service rbx-gpio3-shutdown.service
sudo systemctl restart rbx-app.service rbx-gpio3-shutdown.service
sudo systemctl status rbx-app.service rbx-gpio3-shutdown.service --no-pagersudo systemctl daemon-reload
sudo systemctl reset-failed rbx-app.service rbx-gpio3-shutdown.service
sudo systemctl restart rbx-app.service rbx-gpio3-shutdown.service
sudo systemctl status rbx-app.service rbx-gpio3-shutdown.service --no-pager
