@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Opening port 8090 in Windows Firewall (allows Android device connections)...
netsh advfirewall firewall delete rule name="Flask Backend Port 8090" >nul 2>&1
netsh advfirewall firewall add rule name="Flask Backend Port 8090" dir=in action=allow protocol=TCP localport=8090
echo.
echo Starting Smart Construction MongoDB Backend on port 8090...
python app.py
