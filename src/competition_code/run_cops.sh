> logs/cops.log
echo "Making temp dir"
mkdir temp
echo "Copying files"
cp main.py libs temp/
ls temp	
cp cops_controller.py temp/controller.py
echo "Starting cops"
python2 temp/main.py wdxtu > logs/cops.log
wait
rm -rf temp
echo "All done!"

