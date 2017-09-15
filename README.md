# IRL_application_on_ErrP
IRL control using Error Related Signals from EEG.

How to run the IRL integrated with CNBI's loop*
-------------------------------------------------
Requirements: 	In order for the IRL algorithm to perform well it requires
				to be run in Python 2.7 with the following libraries installed or in the
				same file: 
				- numpy, random, tqdm, matplotlib, os, getch, ConfigParser, sys, time, math, string, cnbiloop.

HOW TO RUN:		Open three terminals and insert the following commands in the established
				terminal and order:
				
				-Terminal 1:	Start the loop. 
						Insert in the Terminal: >>cl_runloop -r -d [.gdf file]

				-Terminal 2:	Start the process sending and receiving TID signals.
								The received TID signal from the IRL algorithm will be
								a number from 1 to 5 representing the action taken by
								the agent at each time-step.
								TID = 1: Upward movement.
								TID = 2: Downward movement.
								TID = 3: Leftward movement
								TID = 4: Rightward movement
								TID = 5: End trajectory movement.
								The signal sent to the IRL algorithm must be an integer 
								from 10 to 1010. The IRL will translate it to a floating 
								point number going from 0 to 1 representing how correct
								is the action considered (0 for totally incorrect, 1 for
								totally correct).
						(Only for testing TID reception from the IRL algorithm)
						Insert in the Terminal: >>cl_tidsender -u

				-Terminal 3:	Start the IRL algorithm.
						Insert in the Terminal: >>python IRL_alvorithm_loop.py IRL_config.ini

