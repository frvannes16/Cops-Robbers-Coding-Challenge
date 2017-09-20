mkdir export
zip export/robbers.zip controller.py main.py libs/ 
cp controller.py temp_controller.py
cp cops_controller.py controller.py
zip export/cops.zip controller.py main.py libs/
mv temp_controller.py controller.py
echo "cops.zip and robbers.zip are available in ${pwd}/export"
