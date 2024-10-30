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
