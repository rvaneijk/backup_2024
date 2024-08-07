#!/bin/bash

echo -e "\nRunning monthly_backup.py with parameter 240501 and 60 sec timeout for unattended operation"
python3 monthly_backup.py --par 240806  --timeout

echo -e "\nRunning monthly_backup.py with parameter 240706 and 60 sec timeout for unattended operation"
python3 monthly_backup.py --par 240706 --timeout
