This is a set of programs for collecting data in the Photobeam BAT rig.

CameraControl.py
A python program made to allow viewing and recording from an IR camera in the rig, with the intention of recording the licking port to monitor licking behavior.

licking_beambk_Camera.py
A python program that runs a session in a BAT chamber, integrating a photobeam lick detector, LED signals, TTL outputs, and control of a behavior camera.
To run the program, open its parent folder in a terminal, and minimally, run `python licking_beambk_Camera.py`. There are numerous additional arguments that can be provided to the script, either from the terminal directly or from guis opened by the program.
From the terminal, you can (and should) stipulate the subject ID, which is the first positional argument (i.e. `python licking_beambk_Camera.py AN01`). Additionally, there are optional flagged arguments for supplying a file with session parameters (-p), specifiying an output folder (-o), using the LED indicators (-l), and using the behavior camera (-c).
An example call using all of the arguments: `python licking_beambk_Camera.py AN01 -p /path/to/paramsfile.txt -o /path/to/outputfolder/ -l True -c True`
The options for the camera are "True" and "False", and the options for the LED are "True", "False", and "Cue".
Running the script without a params file specified will open a dialog box giving you the option to select a params file via gui. If you exit the dialog box, you will be asked to provide session parameters manually in an additional gui. 

Installing:
To install PhotoBAT on a windows machine, you need to start with instacal (https://digilent.com/reference/software/instacal/start?srsltid=AfmBOood_shDyPAMH8VddG7fEJlhaGyNYgTTwMxu-M4-QOApLmNispsO). Once your MCC board is physically installed, you can run instacal to set up the firmware. It should be relatively straightforward to add the new board as board #0.

You will then need to install python. You can install Anaconda (python) here:

Or, you can install from the windows command prompt by running the following code:
```
curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe -o miniconda.exe
start /wait "" .\miniconda.exe /S
del miniconda.exe
```
Once anaconda is installed, we recommend setting up a virtual environment:
```
conda create -n MCC python=3.9
conda activate MCC
```
Inside the new MCC environment, you can run the following script to install all the rest of the packages required to run the programs:
```
conda install git
git clone https://github.com/Mraymon5/PhotoBAT.git
bash .\PhotoBAT\MCC_install.sh
```
If everything installs successfully, you should be able to start using the PhotoBAT programs.
A good place to start is with `MCC_Test.py`: this script allows for testing and calibrating the hardware interface.
```
python .\PhotoBAT\MCC_Test.py
```

To create Parameters files for running actual lick protocols, you can use `MakeParams.py`:
```
python .\PhotoBAT\MakeParams.py
```
You can also find the parameters files in the `/PhotoBAT/params/` folder, and edit them manually if you'd like. This offers some additional functionality, in that you can set different parameters for each individual trail, rather than having fixed values for all trials in a session.

Finally, to run the program itself, you can run:
```
python .\PhotoBAT\licking_MCC.py
```
