sudo cp /home/roger/sdq/monitor/alpha-citic-guyan.service /etc/systemd/system/
sudo cp /home/roger/sdq/monitor/yk-cicc-margin.service /etc/systemd/system/
sudo cp /home/roger/sdq/monitor/jq2-db-margin.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable alpha-citic-guyan.service
sudo systemctl enable jq2-db-margin.service
sudo systemctl enable yk-cicc-margin.service
sudo systemctl start alpha-citic-guyan.service
sudo systemctl start jq2-db-margin.service
sudo systemctl start yk-cicc-margin.service