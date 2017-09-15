# uncompyle6 version 2.11.2
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.13 |Continuum Analytics, Inc.| (default, Dec 19 2016, 13:29:36) [MSC v.1500 64 bit (AMD64)]
# Embedded file name: gridworld_engine_v7.py
# Compiled at: 2017-07-13 11:57:14
"""
Created on Tue May 30 15:10:30 2017

@author: Alvaro
"""
import numpy as np
from random import random
from tqdm import tqdm
import matplotlib.pyplot as plt
import os
import getch
import ConfigParser
import sys, time, math, string

#Implementation
from cnbiloop import BCI
from time import *
# import EyeLink

"""        
function to map actions (as they are defined in the IRL algorithm) to actions as they are defined in the speller
"""
def map_polAction2spelAction(action):
    if action == 0:
        return 3
    if action == 1:
        return 4
    if action == 2:
        return 1
    if action == 3:
        return 2
    if action == 4:
        return 5

def scalar_sigmoid(x):
    return 1./(1.+math.exp(-x))
"""
load errp outputs from a recording of the speller.
"""
def load_errp_recorded_distribution():
    fh = open('probabilities.txt', 'r')
    aux = fh.readlines()
    fh.close()
    return [ (float(elemental[0]), float(elemental[1])) for elemental in [ element[:-1].split('   ')[1:] for element in aux[:-2] ] ]

"""
take the errp outputs of the recording and get 6 lists: Total Positive Actions (true),
, Total Negative Actions(false), Well Classified Positive Actions(true_true), Badly Classified Positive Actions (true_false)
, Well Classified Negative Actions (false_true), Badly Classified Negative Actions
"""
def distribute_recorded_errp_distr():
    errp_distribution = load_errp_recorded_distribution()
    true_true = [ element[1] for element in errp_distribution if element[0] == 1.0 and element[1] >= 0.5 ]
    true_false = [ element[1] for element in errp_distribution if element[0] == 1.0 and element[1] < 0.5 ]
    false_true = [ element[1] for element in errp_distribution if element[0] == -1.0 and element[1] < 0.5 ]
    false_false = [ element[1] for element in errp_distribution if element[0] == -1.0 and element[1] >= 0.5 ]
    true = [ element[1] for element in errp_distribution if element[0] == 1.0]
    false = [ element[1] for element in errp_distribution if element[0] == -1.0]
    return (
     true_true, true_false, false_true, false_false, true, false)

#Takes a sample from a list
def take_sample(lista):
    dice = int(random() * len(lista))
    return lista[dice]
"""
Function to calculate representation of the Expert's trajectory in the feature space
the chosen trajectory is an obsolete variable used to chose among predefined trajectories
present in the function "load_trajectory". We updated the way of getting our trajectories
in a way that this function was not needed anymore. However the "chosen_trajectory" variable
is deep enrooted in our code and it was easier to nullify its effects by designing a new
value (chosen_trajectory = -1) for which the updated calculus of the Expert's trajectory in 
the feature space would be always performed.
"""
def expertCalcMod(Etraject, gamma, chosen_trajectory): 
    if chosen_trajectory != -1:    
        mu = np.zeros(len(Etraject[0][0])+1)
        for traj in Etraject:
            t = 0
            for pos in traj:
                mu += np.array(pos+[1]) * gamma ** t
                t += 1
    
        mu /= float(len(Etraject))
    
    else:    
        mu = np.zeros(len(Etraject[0][0]))
        for traj in Etraject:
            t = 0
            for pos in traj:
                mu += np.array(pos) * gamma ** t
                t += 1
    
        mu /= float(len(Etraject))
        
    return mu

"""
No longer in use: Model #0 of the Error Potential: no error potential signal issued.
"""
def ferrp0():
    return 0

"""
No longer in use: Model #1 of the Error Potential:    binary error potential signal issued 
                                    if the distance to the final target position increases or remains constant.
"""
def ferrp1(position, sprim, final_point):
    distact = abs(final_point[0] - position[0]) + abs(final_point[1] - position[1])
    distpos = abs(final_point[0] - sprim[0]) + abs(final_point[1] - sprim[1])
    return int(distpos >= distact)

"""
No longer in use: Model #2 of the Error Potential:    Hand-input binary error related potential signal.
"""
def ferrp2():
    pert = int(raw_input('perturbation?(answer with 0(no)/1(yes)): '))
    return pert

"""
No longer in use: Model #3 of the Error Potential:    same model as the model #1 with an uncertainty of properly detecting it of p = 0.8.
"""
def ferrp3(position, sprim, final_point):
    distact = abs(final_point[0] - position[0]) + abs(final_point[1] - position[1])
    distpos = abs(final_point[0] - sprim[0]) + abs(final_point[1] - sprim[1])
    return int(distpos >= distact and np.random.random() < 0.8)


"""
No longer in use: Model #4 of the Error Potential:    same as model #1, including the issue of an errp signal if 
                                    we finish the trajectory in a state other than the target.
"""
def ferrp4(position, sprim, final_point, isFinished):
    if isFinished == True:
        return position == final_point
    distact = abs(final_point[0] - position[0]) + abs(final_point[1] - position[1])
    distpos = abs(final_point[0] - sprim[0]) + abs(final_point[1] - sprim[1])
    return int(distpos >= distact)
#############
#IMPORTANT:     ferrp0, ferrp1, ferrp2, ferrp3 and ferrp4 are no longer in use in the recent versions of the code.
#               They are still included as a guide to understand how we progressively modeled the errp considering
#               the situations in which a human could consider an action taken as incorrect.
#############


"""
No longer in use: Function used to get a representation and track the evolution of the state-action values in the Qtable.
"""
def debug(qtable, position, action, perturbation, isMovement):
    print position
    print qtable[0:5]
    print qtable[5:10]
    print qtable[10:15]
    print qtable[15:20]
    print qtable[20:25]
    print action
    print isMovement
    print perturbation
    raw_input('press ENTER')

"""
Map obstacle list (interpreted as in the speller/configuration file) to the obstacle list (interpreted as in the IRL algorithm)
"""
def string2obstacles(llista_obstacles, limx, limy):
    obstacles = []
    obstacles_centers = []
    for i in range(1,len(llista_obstacles)+1):
        y = i-1+limy[0]
        for ii in range(len(llista_obstacles[-i])):
            x = ii+limx[0]
            if llista_obstacles[-i][ii] == "1":
                obstacles.append((x,y,x,y))
                obstacles_centers.append((x,y))
    return obstacles, obstacles_centers
                
        
"""
Gridworld Class containing the Gridworld engine and the algorithms related 
to the implementation of the Inverse Reinforcement Learning and the adaptation to
the CNBI loop.
"""
class gridworld():

    def __init__(self, n, m, starting_point=(0, 0), final_point=(0, 4), mode = "continuous"):
        self.GWmode = mode
        if mode != "TID":
            self.dim = (n, m)
            self.start_point = starting_point
            self.final_point = final_point
            self.limx = (-n / 2 + 1, n / 2)
            self.limy = (0, m - 1)
            self.position = list(starting_point)
            self.lastaction = 0
            self.obstacles = []
            self.obstaclesCenters = []
            self.qtable = np.zeros((n * m, 5))
            self.isFinished = False
            (self.errpDist_true_true, self.errpDist_true_false,
             self.errpDist_false_true, self.errpDist_false_false,
             self.errpDist_true, self.errpDist_false) = distribute_recorded_errp_distr()
            self.n_eeg_features = 2
            self.n_non_eeg_features = self.dim[0] + self.dim[1] + 5
            self.n_features = self.n_eeg_features+self.n_non_eeg_features
    #        self.qtable[:,4] = -100; self.qtable[self.final_point, 4] = 0;
            self.atractor = False
            for x in range(self.limx[0], self.limx[1] + 1):
                ipos = self.pos2qtableindex((x, self.limy[0]))
                self.qtable[ipos, 3] = -100
    
            for x in range(self.limx[0], self.limx[1] + 1):
                ipos = self.pos2qtableindex((x, self.limy[1]))
                self.qtable[ipos, 2] = -100
    
            for y in range(self.limy[0], self.limy[1] + 1):
                ipos = self.pos2qtableindex((self.limx[0], y))
                self.qtable[ipos, 0] = -100
    
            for y in range(self.limy[0], self.limy[1] + 1):
                ipos = self.pos2qtableindex((self.limx[1], y))
                self.qtable[ipos, 1] = -100
        else:
            self.initGW()
            
    def initGW(self):
        if (len(sys.argv) == 1):
            self.config_file = "protocol_configuration.ini"
        else:
            if (string.find(sys.argv[1], '.ini') == -1):
                self.config_file = str(sys.argv[1]) + ".ini"
            else:
                self.config_file = str(sys.argv[1])

        print "Using configuration file: ", self.config_file
        config = ConfigParser.RawConfigParser(allow_no_value=True)
        config.read("./" + self.config_file)
        
        self.dim = (config.getint("interface","num_tiles_column"),config.getint("interface","num_tiles_row"))
        self.limx = (-self.dim[0] / 2 + 1, self.dim[0] / 2)
        self.limy = (0, self.dim[1] - 1)
        
        letter_distr = config.get("interface","characters")
        self.letter_distribution = letter_distr[-5:]
        for i in range(0,len(letter_distr)+1,self.dim[0])[2:]:
            self.letter_distribution += letter_distr[-i:-i+self.dim[0]]
        letter_start_point = config.get("gridworld","START_POINT")
        letter_final_point = config.get("protocol","word_to_write_OFFLINE")
        self.start_point = self.letter2pos(letter_start_point)
        self.final_point = self.letter2pos(letter_final_point)
        
        self.position = list(self.start_point)
        self.lastaction = 0
        self.qtable = np.zeros((self.dim[0] * self.dim[1], 5))
        self.isFinished = False
        
        self.n_eeg_features = 2
        self.n_non_eeg_features = self.dim[0] + self.dim[1] + 5
        self.n_features = self.n_eeg_features+self.n_non_eeg_features
        
        self.atractor = False
        self.qtableWalls()
        
        list_obstacles = config.get("gridworld","obstacles").split(',')
        self.obstacles, self.obstaclesCenters = string2obstacles(list_obstacles,self.limx, self.limy)
        
        #Offline Hyperparameters
        aux_postraj = config.get("irl","trajectory_offline")
        self.postrajectories_offline = [[list(self.letter2pos(letter)) for letter in aux_postraj ]]
        self.uncertainerrp_offline = -1
        self.chosen_trajectory_offline = -1 
        self.track_incorrectness_offline = True
        self.save_data_offline = bool(config.getint("irl","save_data_offline"))
        self.IRLepsilon_offline = float(config.get("irl","IRLepsilon_offline"))
        self.gamma_offline = float(config.get("irl","gamma_offline"))
        self.n_iterations_offline = config.getint("irl","n_iterations_offline")
        self.criteria_offline = 1
        self.plot_offline = False
        self.training_offline = True
        self.epsilon_offline = float(config.get("irl","epsilon_offline"))
        self.alpha_offline = 0.5
        self.mode_offline = "continuous"
        
        #Online Hyperparameters
        aux_postraj = config.get("irl","trajectory_online")
        self.postrajectories_online = [[list(self.letter2pos(letter)) for letter in aux_postraj ]]
        self.uncertainerrp_online = -1
        self.chosen_trajectory_online = -1
        self.track_incorrectness_online = True
        self.save_data_online = bool(config.getint("irl","save_data_online"))
        self.limit_online = np.inf
        self.IRLepsilon_online = float(config.get("irl","IRLepsilon_online"))
        self.gamma_online = float(config.get("irl","gamma_online"))
        self.n_iterations_online = config.getint("irl","n_iterations_online")
        self.criteria_online = 2
        self.plot_online = False
        self.epsilon_online = float(config.get("irl","epsilon_online"))
        self.mode_online = "TID"
        # self.mode_online = "manual"
        
        
        self.connect_to_loop = 1
        if (self.connect_to_loop) and self.mode_online == "TID":
            self.bci = BCI.BciInterface()
            self.bci.id_msg_bus.SetEvent(400)
            self.bci.iDsock_bus.sendall(self.bci.id_serializer_bus.Serialize())	

        
        (self.errpDist_true_true, self.errpDist_true_false,
             self.errpDist_false_true, self.errpDist_false_false,
             self.errpDist_true, self.errpDist_false) = distribute_recorded_errp_distr()
            

    def letter2pos(self, letter):
        return (self.letter_distribution.index(letter)%self.dim[0]+self.limx[0],
                            self.letter_distribution.index(letter)/self.dim[0]+self.limy[0])

    def qtableWalls(self):
        for x in range(self.limx[0], self.limx[1] + 1):
            ipos = self.pos2qtableindex((x, self.limy[0]))
            self.qtable[ipos, 3] = -100

        for x in range(self.limx[0], self.limx[1] + 1):
            ipos = self.pos2qtableindex((x, self.limy[1]))
            self.qtable[ipos, 2] = -100

        for y in range(self.limy[0], self.limy[1] + 1):
            ipos = self.pos2qtableindex((self.limx[0], y))
            self.qtable[ipos, 0] = -100

        for y in range(self.limy[0], self.limy[1] + 1):
            ipos = self.pos2qtableindex((self.limx[1], y))
            self.qtable[ipos, 1] = -100

    def qtableObj(self):
        self.atractor = True
        self.qtable[:,4] = -10.0
        ipos = self.pos2qtableindex((self.final_point[0], self.final_point[1]))
        self.qtable[ipos, 4] = 0

    def moveLeft(self):
        if self.position[0] == self.limx[0] or self.isObstacle((self.position[0] - 1, self.position[1])):
            return False
        else:
            self.position[0] -= 1
            self.lastaction = 1
            return True

    def moveRight(self):
        if self.position[0] == self.limx[1] or self.isObstacle((self.position[0] + 1, self.position[1])):
            return False
        else:
            self.position[0] += 1
            self.lastaction = 2
            return True

    def moveDown(self):
        if self.position[1] == self.limy[0] or self.isObstacle((self.position[0], self.position[1] - 1)):
            return False
        else:
            self.position[1] -= 1
            self.lastaction = 4
            return True

    def moveUp(self):
        if self.position[1] == self.limy[1] or self.isObstacle((self.position[0], self.position[1] + 1)):
            return False
        else:
            self.position[1] += 1
            self.lastaction = 3
            return True

    def takeAction(self, action):
        if action == 0:
            return self.moveLeft()
        if action == 1:
            return self.moveRight()
        if action == 2:
            return self.moveUp()
        if action == 3:
            return self.moveDown()
        if action == 4:
            return self.finish()

    def isFinal(self):
        return self.isFinished

    def finish(self):
        self.isFinished = True
        return True

    def goInitial(self):
        self.position = list(self.start_point)
        self.lastaction = 0
        self.isFinished = False

    def initGridworld(self, bool_obstacle = True):
        self.goInitial()
        self.initQtable()


    def initQtable(self):
        self.qtable = np.zeros((self.dim[0] * self.dim[1], 5))
        self.qtableWalls()
#        self.qtable[:,4] = -100; self.qtable[self.final_point, 4] = 0;
        if self.atractor:
            self.qtableObj()

    def qtableLookup(self, pos):
        ipos = pos[0] - self.limx[0] + (pos[1] - self.limy[0]) * self.dim[0]
        return self.qtable[ipos, :]

    def pos2qtableindex(self, pos=0):
        if pos == 0:
            pos = self.position
        ipos = pos[0] - self.limx[0] + (pos[1] - self.limy[0]) * self.dim[0]
        return ipos

    def pos2feat(self, pos=0):
        if pos == 0:
            pos = self.position
        posfeature = [
         0] * (self.dim[0] + self.dim[1])
        posfeature[pos[0] - self.limx[0]] = 1
        posfeature[self.dim[0] + pos[1]] = 1
        return posfeature
    
    def postraj2mu(self, postraj, gamma):
        self.feature(update_n_features = True)
        mu = np.zeros(self.n_features)
        for trajectory in postraj:
            last_action = 2
            action = 3
            record_actions = np.zeros(5)
            n_changes = 0
            ####################################3
            for i in range(len(trajectory)):
                if i<(len(trajectory)-1):
                    if trajectory[i][0]<trajectory[i+1][0]:
                        action = 1
                    elif trajectory[i][0]>trajectory[i+1][0]:
                        action = 0
                    if trajectory[i][1]<trajectory[i+1][1]:
                        action = 2
                    elif trajectory[i][1]>trajectory[i+1][1]:
                        action = 3
                else:
                    action = 4
                ###########################
                record_actions[action] += 1
                if action != last_action:
                    n_changes += 1
                    last_action = action  
                ############################
                mu += self.feature(trajectory[i], 0, action, i, record_actions, n_changes)*gamma**i
        mu /= float(len(postraj))
        return mu

    def observeAction(self, action):
        if action == 0 and self.position[0] != self.limx[0] and not self.isObstacle((self.position[0] - 1, self.position[1])):
            return ([self.position[0] - 1, self.position[1]], True)
        if action == 1 and self.position[0] != self.limx[1] and not self.isObstacle((self.position[0] + 1, self.position[1])):
            return ([self.position[0] + 1, self.position[1]], True)
        if action == 2 and self.position[1] != self.limy[1] and not self.isObstacle((self.position[0], self.position[1] + 1)):
            return ([self.position[0], self.position[1] + 1], True)
        if action == 3 and self.position[1] != self.limy[0] and not self.isObstacle((self.position[0], self.position[1] - 1)):
            return ([self.position[0], self.position[1] - 1], True)
        if action == 4:
            self.isFinished = True
            return (
             self.position, True)
        return (self.position, False)

    def defineObstacles(self, obstacleList):
        for obstacle in obstacleList:
            self.obstacles.append(obstacle)
            self.obstaclesCenters.append((float(obstacle[0]+obstacle[2])/2.0,float(obstacle[1]+obstacle[3])/2.0))
            

    def isObstacle(self, position):
        for obstacle in self.obstacles:
            if obstacle[0] <= position[0] <= obstacle[2]:
                if obstacle[1] <= position[1] <= obstacle[3]:
                    return True

    def right(self, perturbation):
        dice = random()
        if dice < perturbation:
            dice2 = random()
            if dice2 < 1.0 / 3.0:
                self.moveLeft()
            elif dice2 >= 2.0 / 3.0:
                self.moveUp()
            else:
                self.moveDown()
            return 1
        self.moveRight()
        return 0

    def left(self, perturbation):
        dice = random()
        if dice < perturbation:
            dice2 = random()
            if dice2 < 1.0 / 3.0:
                self.moveRight()
            elif dice2 >= 2.0 / 3.0:
                self.moveUp()
            else:
                self.moveDown()
            return 1
        self.moveLeft()
        return 0

    def up(self, perturbation):
        dice = random()
        if dice < perturbation:
            dice2 = random()
            if dice2 < 1.0 / 3.0:
                self.moveLeft()
            elif dice2 >= 2.0 / 3.0:
                self.moveRight()
            else:
                self.moveDown()
            return 1
        self.moveUp()
        return 0

    def down(self, perturbation):
        dice = random()
        if dice < perturbation:
            dice2 = random()
            if dice2 < 1.0 / 3.0:
                self.moveLeft()
            elif dice2 >= 2.0 / 3.0:
                self.moveUp()
            else:
                self.moveRight()
            return 1
        self.moveDown()
        return 0

    def e_policy(self, position, epsilon):
        iposition = self.pos2qtableindex(position)
        n_max = list(self.qtable[iposition]).count(self.qtable[iposition].max())
        sortedActionList = sorted([ i for i in enumerate(self.qtable[iposition]) ], key=lambda x: x[1], reverse=True)
        aux = int(random() * n_max)
        if random() > epsilon:
            return sortedActionList[aux][0]
        else:
            aux2 = int(random() * 5)
            while aux2 == sortedActionList[aux][0]:
                aux2 = int(random() * 5)

            return aux2

    def policy(self, position, epsilon=None):
        return self.e_policy(position, epsilon)
    
    def bfsObstacle(self, pos):
        booltable = np.zeros((self.dim[0],self.dim[1]))
        queue = []
        if pos[1] != self.limy[1] and booltable[pos[0],pos[1]+1] != 1:
            if self.isObstacle((pos[0],pos[1]+1)):
                return (pos[0],pos[1]+1)
            queue = queue + [(pos[0],pos[1]+1)]
            booltable[pos[0],pos[1]+1] = 1
            
        if pos[1] != self.limy[0] and booltable[pos[0],pos[1]-1] != 1:
            if self.isObstacle((pos[0],pos[1]-1)):
                return (pos[0],pos[1]-1)
            queue = queue + [(pos[0],pos[1]-1)]
            booltable[pos[0],pos[1]-1] = 1
            
        if pos[0] != self.limx[1] and booltable[pos[0]+1,pos[1]] != 1:
            if self.isObstacle((pos[0]+1,pos[1])):
                return (pos[0]+1,pos[1])
            queue = queue + [(pos[0]+1,pos[1])]
            booltable[pos[0]+1,pos[1]] = 1
            
        if pos[0] != self.limx[0] and booltable[pos[0]-1,pos[1]] != 1:
            if self.isObstacle((pos[0]-1,pos[1])):
                return (pos[0]-1,pos[1])
            queue = queue + [(pos[0]-1,pos[1])]
            booltable[pos[0]-1,pos[1]] = 1
            
        while len(queue) != 0:
            actualpos = list(queue[0])
            queue = queue[1:]
            if actualpos[1] != self.limy[1] and booltable[actualpos[0],actualpos[1]+1] != 1:
                if self.isObstacle((actualpos[0],actualpos[1]+1)):
                    return (actualpos[0],actualpos[1]+1)
                queue = queue + [(actualpos[0],actualpos[1]+1)]
                booltable[actualpos[0],actualpos[1]+1] = 1
                
            if actualpos[1] != self.limy[0] and booltable[actualpos[0],actualpos[1]-1] != 1:
                if self.isObstacle((actualpos[0],actualpos[1]-1)):
                    return (actualpos[0],actualpos[1]-1)
                queue = queue + [(actualpos[0],actualpos[1]-1)]
                booltable[actualpos[0],actualpos[1]-1] = 1
                
            if actualpos[0] != self.limx[1] and booltable[actualpos[0]+1,actualpos[1]] != 1:
                if self.isObstacle((actualpos[0]+1,actualpos[1])):
                    return (actualpos[0]+1,actualpos[1])
                queue = queue + [(actualpos[0]+1,actualpos[1])]
                booltable[actualpos[0]+1,actualpos[1]] = 1
                
            if actualpos[0] != self.limx[0] and booltable[actualpos[0]-1,actualpos[1]] != 1:
                if self.isObstacle((actualpos[0]-1,actualpos[1])):
                    return (actualpos[0]-1,actualpos[1])
                queue = queue + [(actualpos[0]-1,actualpos[1])]
                booltable[actualpos[0]-1,actualpos[1]] = 1
        return pos
    
    def isFinalPoint(self, pos):
        return (pos[0] == self.final_point[0] and pos[1] == self.final_point[1])
    
    def bfsFinal(self, pos):
        booltable = np.zeros((self.dim[0],self.dim[1]))
        queue = []
        if pos[0]==self.final_point[0] and pos[1]==self.final_point[1]:
            return 0
        
        if pos[1] != self.limy[1] and booltable[pos[0],pos[1]+1] != 1:
            if self.isFinalPoint((pos[0],pos[1]+1)):
                return 1.0
            queue = queue + [((pos[0],pos[1]+1),1.0)]
            booltable[pos[0],pos[1]+1] = 1
            
        if pos[1] != self.limy[0] and booltable[pos[0],pos[1]-1] != 1:
            if self.isFinalPoint((pos[0],pos[1]-1)):
                return 1.0
            queue = queue + [((pos[0],pos[1]-1),1.0)]
            booltable[pos[0],pos[1]-1] = 1
            
        if pos[0] != self.limx[1] and booltable[pos[0]+1,pos[1]] != 1:
            if self.isFinalPoint((pos[0]+1,pos[1])):
                return 1.0
            queue = queue + [((pos[0]+1,pos[1]),1.0)]
            booltable[pos[0]+1,pos[1]] = 1
            
        if pos[0] != self.limx[0] and booltable[pos[0]-1,pos[1]] != 1:
            if self.isFinalPoint((pos[0]-1,pos[1])):
                return 1.0
            queue = queue + [((pos[0]-1,pos[1]),1.0)]
            booltable[pos[0]-1,pos[1]] = 1
            
        while len(queue) != 0:
            actualpos = list(queue[0][0])
            distance = queue[0][1]
            queue = queue[1:]
            if actualpos[1] != self.limy[1] and booltable[actualpos[0],actualpos[1]+1] != 1:
                if self.isFinalPoint((actualpos[0],actualpos[1]+1)):
                    return distance+1.0
                queue = queue + [((actualpos[0],actualpos[1]+1), distance + 1.0)]
                booltable[actualpos[0],actualpos[1]+1] = 1
                
            if actualpos[1] != self.limy[0] and booltable[actualpos[0],actualpos[1]-1] != 1:
                if self.isFinalPoint((actualpos[0],actualpos[1]-1)):
                    return distance+1.0
                queue = queue + [((actualpos[0],actualpos[1]-1), distance + 1.0)]
                booltable[actualpos[0],actualpos[1]-1] = 1
                
            if actualpos[0] != self.limx[1] and booltable[actualpos[0]+1,actualpos[1]] != 1:
                if self.isFinalPoint((actualpos[0]+1,actualpos[1])):
                    return distance + 1.0
                queue = queue + [((actualpos[0]+1,actualpos[1]), distance + 1.0)]
                booltable[actualpos[0]+1,actualpos[1]] = 1
                
            if actualpos[0] != self.limx[0] and booltable[actualpos[0]-1,actualpos[1]] != 1:
                if self.isFinalPoint((actualpos[0]-1,actualpos[1])):
                    return distance + 1.0
                queue = queue + [((actualpos[0]-1,actualpos[1]), distance + 1.0)]
                booltable[actualpos[0]-1,actualpos[1]] = 1
        return np.inf
    
    def aux_graphical_gridworld_representation(self, position, sprim):
        string = ""
        for y in range(self.limy[1],self.limy[0]-1,-1):
            for x in range(self.limx[0],self.limx[1]+1):
                char = "."
                if list((x,y)) == list(self.final_point):
                    char = "F"
                if list((x,y)) == list(self.start_point):
                    char = "S"
                if self.isObstacle((x,y)):
                    char = "#"
                if list((x,y)) == list(position):
                    char = "p"
                if list((x,y)) == list(sprim):
                    char = "s"
                string += char
            string += "\n"
        print string
                    
        
    
    def binary_ferrp(self, position, sprim, final_point, Etraject, uncertainerrp, track_incorrectness=True):
        dice = np.random.random() <= uncertainerrp
        if Etraject != 0:
            sprim_boolean = True
            pos_boolean = True
            for traject in Etraject:
                if position in traject:
                    pos_boolean = False
                if sprim in traject:
                    sprim_boolean = False

            if not (sprim_boolean or pos_boolean):
                if dice:
                    aux = int(not traject.index(position) <= traject.index(sprim))
                    if not track_incorrectness:
                        aux = 1 - aux
                    return aux
                else:
                    aux = int(traject.index(position) <= traject.index(sprim))
                    if not track_incorrectness:
                        aux = 1 - aux
                    return aux

            if dice:
                aux = int(sprim_boolean)
                if not track_incorrectness:
                    aux = 1 - aux
                return aux
            else:
                aux = int(not sprim_boolean)
                if not track_incorrectness:
                    aux = 1 - aux
                return aux

    def continuous_ferrp_aux(self, position, sprim, final_point, Etraject, uncertainerrp):
        dice = np.random.random() <= uncertainerrp
#        print uncertainerrp
        if Etraject != 0:
            sprim_boolean = True
            pos_boolean = True
            for traject in Etraject:
                if position in traject:
                    pos_boolean = False
                if sprim in traject:
                    sprim_boolean = False

            if not (sprim_boolean or pos_boolean):
                if dice:
                    return (not traject.index(position) <= traject.index(sprim), False)
                else:
                    return (
                     traject.index(position) <= traject.index(sprim), True)

            if dice:
                return (sprim_boolean, False)
            else:
                return (
                 not sprim_boolean, True)

    def continuous_ferrp(self, position, sprim, final_point, Etraject, uncertainerrp, track_incorrectness=True):
        not_correct, not_well_classified = self.continuous_ferrp_aux(position, sprim, final_point, Etraject, uncertainerrp)
        if uncertainerrp == -1:
            if not_correct == True:
                aux = take_sample(self.errpDist_false)
                return aux
            if not_correct == False:
                aux = take_sample(self.errpDist_true)
                return aux
        
        if not_correct == True and not_well_classified == True:
            aux = take_sample(self.errpDist_false_false)
            if track_incorrectness:
                aux = 1 - aux
            return aux
        if not_correct == True and not_well_classified == False:
            aux = take_sample(self.errpDist_false_true)
            if track_incorrectness:
                aux = 1 - aux
            return aux
        if not_correct == False and not_well_classified == True:
            aux = take_sample(self.errpDist_true_false)
            if track_incorrectness:
                aux = 1 - aux
            return aux
        if not_correct == False and not_well_classified == False:
            aux = take_sample(self.errpDist_true_true)
            if track_incorrectness:
                aux = 1 - aux
            return aux
        
    def handle_tobiid_input(self):
        data = None
        try:
            data = self.bci.iDsock_bus.recv(512)
            self.bci.idStreamer_bus.Append(data)	
        except:
            self.nS = False
            self.dec = 0
            pass	
		# deserialize ID message
        if data:
            if self.bci.idStreamer_bus.Has("<tobiid","/>"):
                msg = self.bci.idStreamer_bus.Extract("<tobiid","/>")
                self.bci.id_serializer_bus.Deserialize(msg)
                self.bci.idStreamer_bus.Clear()
                tmpmsg = int(self.bci.id_msg_bus.GetEvent())
                print 'Received event! %d' % (tmpmsg)
                return tmpmsg    				
				
					
            elif self.bci.idStreamer_bus.Has("<tcstatus","/>"):
                MsgNum = self.bci.idStreamer_bus.Count("<tcstatus")
                for i in range(1,MsgNum-1):
            # Extract most of these messages and trash them		
                    msg_useless = self.bci.idStreamer_bus.Extract("<tcstatus","/>")   
                return -1    
        else:
            return -1
    
    def ferrp(self, position, sprim, final_point, Etraject, uncertainerrp, mode = "continuous" , track_incorrectness=True):
        if mode == "binary":
            return self.binary_ferrp(position, sprim, final_point, Etraject, uncertainerrp, track_incorrectness=track_incorrectness)
        
        if mode == "continuous":
            aux = self.continuous_ferrp(position, sprim, final_point, Etraject, uncertainerrp, track_incorrectness=track_incorrectness)
            return aux
        
        if mode == "manual":
            self.aux_graphical_gridworld_representation(position,sprim)
#            os.system("pause")
            print "Input 0 if correct, if incorrect 1: "
            aux = getch.getch()
            aux = int(aux)
            if aux == 1:
                error_potential = take_sample(self.errpDist_false)
            
            else:
                error_potential = take_sample(self.errpDist_true)
            if track_incorrectness:
                        error_potential = 1-error_potential
            print error_potential
            return error_potential
        
        if mode == "TID":
            self.aux_graphical_gridworld_representation(position,sprim)
            value = -1
            while value==-1:
                value = self.handle_tobiid_input()
            print value
            error_potential = (value - 10) / 1000.0
            if track_incorrectness:
                error_potential = 1.0 - error_potential
            print error_potential
            return error_potential
        
    def episode(self, epsilon=None, gamma=0.9, alpha=1, limit=np.inf, weights=100,
                verbose=False, Etrajectpos=0, uncertainerrp=1.0, mode = "continuous" , track_incorrectness=True,
                update = True):
        #non-position/errp related features
        t = 0
        record_actions = [0,0,0,0,0]
        last_action = 2
        n_changes = 0
        ######
        if type(weights) == list:
            weights = np.array(weights)
#        print uncertainerrp
        self.goInitial()
        score = 0
        mu = np.zeros(self.n_features)
        postraject = []
        traject = []
        keepGoing = False
        while not self.isFinal():
            iposition = self.pos2qtableindex()
            e_pol_action = self.policy(self.position, epsilon)
            sprim, isMovement = self.observeAction(e_pol_action)
            ### Send TID-Action ###################
            if mode == "TID":
                self.bci.id_msg_bus.SetEvent(map_polAction2spelAction(e_pol_action))
                self.bci.iDsock_bus.sendall(self.bci.id_serializer_bus.Serialize())
            ###update non-position/errp features###
            errp = self.ferrp(self.position, sprim, self.final_point, Etrajectpos, uncertainerrp, mode=mode, track_incorrectness=track_incorrectness)
            record_actions[e_pol_action] += 1
            if e_pol_action != last_action:
                n_changes += 1
                last_action = e_pol_action
            #######################################
            nextqtable = self.qtableLookup(sprim).max()
            reward = self.reward(weights, sprim, errp, e_pol_action,t, record_actions, n_changes)
            if update:
                if isMovement and not self.isFinished:
                    self.qtable[(iposition, e_pol_action)] += alpha * (reward + gamma * nextqtable - self.qtable[iposition, e_pol_action])
                elif not self.isFinished:
                    self.qtable[iposition, e_pol_action] = -100
                elif self.position == list(self.final_point):
                    self.qtable[(iposition, e_pol_action)] += alpha * (reward + gamma * nextqtable - self.qtable[iposition, e_pol_action])
#                    self.qtable[(iposition, e_pol_action)] += 1.0
                else:
                    if uncertainerrp == -1 and mode != "manual":
                        errp = take_sample(self.errpDist_false)
                    elif random() < uncertainerrp and mode != "manual":
                        errp = take_sample(self.errpDist_false_true)
                    elif mode != "manual":
                        errp = take_sample(self.errpDist_false_false)
                    if track_incorrectness and mode != "manual":
                        errp = 1-errp
                     ############
#                    reward = self.reward(weights, sprim, errp, e_pol_action, t, record_actions,n_changes)
                    self.qtable[(iposition, e_pol_action)] += alpha * (reward + gamma * nextqtable - self.qtable[iposition, e_pol_action])
#                    self.qtable[(iposition, e_pol_action)] += -1.0
                    #############
#                    if errp > 0.5:
#                        keepGoing = True
#                        mu = mu - self.feature(self.position, errp, e_pol_action, t, record_actions, n_changes) * gamma ** t
                    if self.atractor:
                        self.qtable[(iposition, e_pol_action)] = -10.0
            if verbose == True:
                debug(self.qtable, self.position, e_pol_action, errp, isMovement)
            ###### save features ############
            postraject.append([list(self.position), e_pol_action, errp])
            traject.append(list(self.feature(self.position, errp, e_pol_action, t, record_actions, n_changes)))
            ######append the trajectory in mu####################
            mu = mu + self.feature(self.position, errp, e_pol_action, t, record_actions, n_changes) * gamma ** t
            self.takeAction(e_pol_action)
            if keepGoing == True:
                keepGoing = False
                self.isFinished = False
                
            t += 1
            score += reward
            if t >= limit:
#                print 'limit'
                break

        return (
         mu, score, t, postraject, traject)

    def feature(self, pos = [0,0], errp = 0, action = 0 , time_steps = 0, record_actions = [0,0,0,0,0],
                n_changes = 0, update_n_features = True):
        posfeatures = []
        posfeatures += self.pos2feat(pos)
        
        actionfeat = []
        actionfeat += [0] * action + [1] + [0] * (4 - action)
        
        dist = np.array([self.final_point[0] - pos[0], self.final_point[1]-pos[1]])
        dist_feature = [math.tanh(np.linalg.norm(dist,2))]
        
        bfs_dist = float(self.bfsFinal(pos))
        bfs_dist_feature = [math.tanh(bfs_dist)]
        
        time_feature = [math.tanh(time_steps)]
        
        actions_distr_feature_1 = list(np.array(record_actions)/float(np.array(record_actions).sum()))
        actions_distr_feature_2 = [math.tanh(float(element)) for element in record_actions]
        gen_mov_feature = [math.tanh(record_actions[1]-record_actions[0]),
                        math.tanh(record_actions[2]-record_actions[3])]
        
        n_changes_feature = [math.tanh(n_changes)]
        
        close_obst = np.array(self.bfsObstacle(pos))
        distance = np.linalg.norm(close_obst-np.array(pos),2)
        if distance == 0:
            distance = 10.0
        norm_obs_dist_feature = [math.exp(-(distance-1.0))]
        
        obst_centers_feature = []
        for center in self.obstaclesCenters:
            dist = np.array([center[0]-pos[0], center[1]-pos[1]])
            obst_centers_feature.append(math.exp(-(np.linalg.norm(dist,2)-1.0)))
        
#        non_eeg_features = (dist_feature + time_feature 
#                            )
        non_eeg_features = (
                            dist_feature + #this works - 1 feature
                            time_feature #this works - 1 feature
                            + bfs_dist_feature # - 1 feature
                            + norm_obs_dist_feature #this works - 1 feature 
#                            + obst_centers_feature # - nb of obstacles (2) 
                            + n_changes_feature # - 1 feature
#                            + gen_mov_feature # - 2 features
                            + actions_distr_feature_1 # - 5 features
#                            + actions_distr_feature_2 # - 5 features
                            ) 
        
        eeg_features = [errp, 1-errp] #change if correct_track
#        eeg_features = [1-errp] #change if correct_track
        
        if update_n_features:
            self.n_eeg_features, self.n_non_eeg_features = len(eeg_features), len(non_eeg_features)
        
        features = non_eeg_features + eeg_features
        if update_n_features:
            self.n_features = len(features)
        return np.array(features)

    def reward(self, w, position, errp, e_pol_action, time_steps, record_actions, n_changes):
#        features: distance(1), record_actions(5), time_feature(1), errp(1), non-errp(1)
#        consider = [
##                2,4,19,21,22,23,24,
#                    15,16,17,18
#                    ]
        if w.any() == 100:
            return -1
        w[0] = -1.0
        w[1] = -.15
#        w[2] = -1.0
#        w[2],w[3],w[4],w[5],w[6] = 0,0,0,0,0
        features = self.feature(position, errp, e_pol_action, time_steps, record_actions, n_changes)
#        return w[consider].dot(features[consider] )
        return w.dot(features)
#        return scalar_sigmoid(w.dot(features)) #trial



    def QLearning(self, gamma=0.9, iterations=1000000, epsilon=0.05, alpha=2.0,
                  penalization=0, limit = 500000, uncertainerrp = 0.9, Etrajectpos = None, 
                  mode = "continuous", track_incorrectness = True, count = 0, w_i = 100,
                  continued = True, criteria = 0, IRLit = 1):
#        print uncertainerrp
        time_steps = 0
        if type(w_i) == list:
            w_i = np.array(w_i)
        if continued:
            self.goInitial()
        else:
            self.initGridworld()
            if self.atractor == True:
                self.qtableObj()
    #    obstacleList = [(0,1,0,1)]
    #    Qgw.defineObstacles(obstacleList)    
        scores10 = np.zeros(2)
        mu10 = ['']*10
        for it in range(iterations):
            mu_aux, score, t, postraject, traject = self.episode(epsilon=epsilon,
                                                                 alpha = 1.0/(IRLit*(it+1)),
                                                                 gamma=gamma,
                                                             limit=limit, weights=w_i, verbose=False,
                                                             Etrajectpos=Etrajectpos,
                                                             uncertainerrp=uncertainerrp,
                                                             mode=mode,
                                                             track_incorrectness=track_incorrectness)
            mu10[it % len(mu10)] = mu_aux
            scores10[it % len(scores10)] = score
            count += t
            time_steps += t
            if self.convergence_criteria(it, scores10, criteria = criteria):
                print 'postrajectory: ' + str(postraject)
                print 'w: ' + str(w_i)
                return mu_aux, count, postraject, traject, time_steps
        return np.array(mu10).mean(axis = 0), count, postraject, traject, time_steps
    
    def load_trajectory(self, chosen_trajectory = 1):
        if chosen_trajectory == -1:
            return self.traj_demo()
        if self.dim[0] == 10 and self.dim[1]==10:
            if chosen_trajectory == 1:
                from milestone_trajectories import traj10x10_traj1 as trajectories
                from milestone_trajectories import traj10x10_traj1_pos as postrajectories
            elif chosen_trajectory == 2:
                from milestone_trajectories import traj10x10_traj2 as trajectories
                from milestone_trajectories import traj10x10_traj2_pos as postrajectories
            elif chosen_trajectory == 3:
                from milestone_trajectories import traj10x10_traj3 as trajectories
                from milestone_trajectories import traj10x10_traj3_pos as postrajectories
            
        elif self.dim[0] == 5 and self.dim[1]== 6:
            if chosen_trajectory == 1:
                from milestone_trajectories import traj5x6_traj1 as trajectories
                from milestone_trajectories import traj5x6_traj1_pos as postrajectories
            elif chosen_trajectory == 2:
                from milestone_trajectories import traj5x6_traj2 as trajectories
                from milestone_trajectories import traj5x6_traj2_pos as postrajectories
            elif chosen_trajectory == 3:
                from milestone_trajectories import traj5x6_traj3 as trajectories
                from milestone_trajectories import traj5x6_traj3_pos as postrajectories
            elif chosen_trajectory == 4:
                from milestone_trajectories import traj5x6_traj4 as trajectories
                from milestone_trajectories import traj5x6_traj4_pos as postrajectories
            
        return trajectories, postrajectories
    
    def IRL_step2(self, mu, mu_bar_2, mu_expert):
        mu_bbar = mu_bar_2 + (mu - mu_bar_2) * ((mu - mu_bar_2).dot(mu_expert - mu_bar_2) / (mu - mu_bar_2).dot(mu - mu_bar_2))
        aux = mu - mu_bar_2
        aux2 = mu_bbar - mu_bar_2
        if np.linalg.norm(aux2,2) <= np.linalg.norm(aux,2) and aux.dot(aux2) > 0:
            mu_bar_1 = list(mu_bbar)
        else:
            aux3 = np.linalg.norm(mu_expert - mu, 2)
            aux4 = np.linalg.norm(mu_expert - mu_bar_2, 2)
            if aux3 > aux4:
                mu_bar_1 = list(mu_bar_2)
            else:
                mu_bar_1 = list(mu)
        return mu_bar_1
    
    def IRL_iteration(self, gamma=0.9, uncertainerrp=0.9, mode="continuous",
                      iterations=2000, limit=500000, epsilon=0.05, IRLepsilon=0.35,
                      alpha=1.0, n_iterations=40, IRLiterations=100000, weights = 0,
                      chosen_trajectory=1,trajectories=[], postrajectories=[],
                      track_incorrectness=True, save_data = True, initialization = [],
                      criteria = 0, plot = False, training = False, max_timesteps = np.inf):
        self.feature(time_steps = 0,update_n_features = True)
        self.initGridworld() #initialize gridworld
        #load expert trajectories and compute mu
        if postrajectories == []:
            trajectories, postrajectories = self.load_trajectory(chosen_trajectory = chosen_trajectory)
            mu_expert = expertCalcMod(trajectories, gamma, chosen_trajectory)
        else:
            mu_expert = self.postraj2mu(postrajectories,gamma)
        ws = []
        IRLits = []
        postrajs = []
        tss = []
        timesteps = []
        counts = []
        count = 0
        first_it = True
        t_i = 0
        bool_epsilon = False
        if epsilon == -1:
            bool_epsilon = True
        for iaux in tqdm(range(n_iterations)):
            if bool_epsilon:
                epsilon = 0.5
            mus = []
            w = np.random.random(self.n_features)
            if weights != 0:
                w = np.array(weights)
            self.initGridworld()
            if self.atractor == True:
                self.qtableObj()
#            obstacleList = [(0,1,0,1)]
#            Qgw.defineObstacles(obstacleList)
#            mu, score, t, postraject, traject = self.episode(epsilon=epsilon, gamma=gamma, verbose=False, weights=w, Etrajectpos=postrajectories, mode=mode, track_incorrectness=track_incorrectness)
            mu_save = 0
            mu_bar_2_save = 0
            qtable_save = 0
            if initialization == []:
                mu, count, postraject, traject, t = self.QLearning(gamma = gamma, iterations= iterations, epsilon=epsilon,
                                               alpha=alpha, limit = limit, uncertainerrp = uncertainerrp,
                                               Etrajectpos = postrajectories,mode = mode,
                                               track_incorrectness = track_incorrectness,
                                               count = 0 , w_i = w)
                mus.append(mu)
                t_i = np.linalg.norm(mu_expert - mu)
                w_i = (mu_expert - mu) / np.linalg.norm(mu_expert - mu, 1)
                mu_bar_2 = np.array(mu)
                mu_bar_1 = 0
#                mu_bbar = 0
            else:
                mu = np.array(initialization[0])#initialize
                mu_bar_2 = np.array(initialization[1])
                self.qtable = np.array(initialization[2])
                t = 10
            if first_it == True:
                count = 0
            time_steps = 0
            ts = []
            for IRLit in range(IRLiterations):
                if bool_epsilon:
                    epsilon = epsilon/2.0
                if IRLit > 0 or initialization != []:
                    print 'STEP 2, iteration: ' + str(IRLit)
                    mu_bar_1 = self.IRL_step2(mu[:-self.n_eeg_features], mu_bar_2[:-self.n_eeg_features], mu_expert[:-self.n_eeg_features])
#                    t_i = np.linalg.norm(mu_expert[:-self.n_eeg_features] - mu_bar_1[:-self.n_eeg_features])
                    t_i = np.linalg.norm(mu_expert[:-self.n_eeg_features] - mu_bar_1)
#                    t_i = np.linalg.norm(mu_expert[:-2] - mu_bar_1[:-2])
                    print 'mu_bar: '+str(mu_bar_1)
                    print 'mu_expert: '+str(mu_expert)
                    print 't: ' + str(t_i)+', timesteps: '+str(time_steps)+', total: '+str(count)
                    ts.append(t_i)
                    
                    if (t_i) <= IRLepsilon and IRLit > 0:
                        print 'IRL iterations until convergence: ' + str(IRLit)
                        print 'movements: ' + str(t)
                        print 'trajectory: ' + str(postraject)
                        print 'w: ' + str(w_i)
                        tss.append(ts)
                        ws.append(w_i)
                        IRLits.append(IRLit)
                        postrajs.append(postraject)
                        counts.append(count)
                        timesteps.append(time_steps)
                        
                        mu_bar_2_save = np.array(mu_bar_2)
                        mu_save = np.array(mu)
                        qtable_save = np.array(self.qtable)
                        first_it = True
                        break
                    mu_bar_1 = self.IRL_step2(mu, mu_bar_2, mu_expert)
                    w_i = mu_expert - mu_bar_1
                    w_i = w_i / np.linalg.norm(w_i, 1)
                    
#                    mu_bar_2_save = np.array(mu_bar_2)
#                    mu_save = np.array(mu)
#                    qtable_save = np.array(self.qtable)
                    
                    mu_bar_2 = list(mu_bar_1)
                mu, count, postraject, traject, time_steps = self.QLearning(gamma = gamma, iterations= iterations, epsilon=epsilon,
                                           alpha=alpha, limit = limit, uncertainerrp = uncertainerrp,
                                           Etrajectpos = postrajectories,mode = mode,
                                           track_incorrectness = track_incorrectness,
                                           count = count , w_i = w_i, continued = True,
                                           criteria=criteria,
#                                           , IRLit = (IRLit+1)
                                           )
                if count > 1000 and training == False and (mode != "manual" and mode != "TID"):
#                    first_it = False
                    break
                elif count > 400 and training == False and (mode == "manual" or mode == "TID"):
#                    first_it = False
                    break
#                print 'mu: '+str(mu)
#                print 'mu expert: '+str(mu_expert)

                mus.append(mu)

        print np.array(ws).sum(axis=0) / len(ws)
        wss = np.array(ws).sum(axis=0) / len(ws)
        wsss = list(wss)
        wslist = [ list(weightss) for weightss in ws ]
        print "time-steps median: "+str(np.median(np.array(timesteps)))
        print "time-steps mean: "+str(np.array(timesteps).mean())
        print "time-steps standard deviation: "+str(np.array(timesteps).std())
        print "IRL iterations median: "+str(np.median(np.array(IRLits)))
        print "IRL iterations mean: "+str(np.array(IRLits).mean())
        print "IRL iterations standard deviation: "+str(np.array(IRLits).std())
        print "total time-steps median: "+str(np.median(np.array(counts)))
        print "total time-steps mean: "+str(np.array(counts).mean())
        print "total time-steps standard deviation: "+str(np.array(counts).std())
        if plot:
            plt.boxplot(counts, 0, '')
        print "timesteps under 200: "+str(len(np.array(counts)[np.array(counts)<200]/np.array(counts).sum()*n_iterations))
        print  "timesteps under 400: "+str(len(np.array(counts)[np.array(counts)<400]/np.array(counts).sum()*n_iterations))
        print  "timesteps under 600: "+str(len(np.array(counts)[np.array(counts)<600]/np.array(counts).sum()*n_iterations))
        print  "timesteps under 800: "+str(len(np.array(counts)[np.array(counts)<800]/np.array(counts).sum()*n_iterations))
        tssmaxlen = np.array([ len(tlist) for tlist in tss ]).max()
        tssss = [ tlist + [0] * (tssmaxlen - len(tlist)) for tlist in tss ]
        tsss = [ np.array(tlist) for tlist in tssss ]
        tsss = np.array(tsss)
        if save_data == True:
    #        path = "/home/alvaro/Documents/Gridworld/Milestone/Logged_Results/"
            path = 'C:/Users/Alvaro/Documents/Annee_X2014-3.2/Stage/Gridworld/Milestone/Logged_Results/'
            file_name = 'last_results_' + str(int(uncertainerrp * 100)) + '_traj_' + str(chosen_trajectory) + '.out'
            final_path = path + file_name
            fh = open(final_path, 'w')
            fh.write(str(wsss) + '\n')
            fh.write(str(wslist) + '\n')
            fh.write(str(tssss) + '\n')
            fh.write(str(np.array(IRLits).mean()) + '\n')
            fh.write(str(np.array(IRLits).std()) + '\n')
            fh.write(str(np.array(counts).mean()) + '\n')
            fh.write(str(np.array(counts).std()) + '\n')
            fh.write(str(mu_save)+'\n')
            fh.write(str(mu_bar_2_save)+'\n')
            fh.close()
        if training:
            return (wsss, wslist, np.array(IRLits).mean(),
                np.array(IRLits).std(), np.array(counts).mean(),
                np.array(counts).std(),mu_save, mu_bar_2_save, qtable_save, t_i, postrajs[-1])
            
        return (wsss, wslist, np.array(IRLits).mean(),
                np.array(IRLits).std(), np.array(counts).mean(),
                np.array(counts).std(),mu_save, mu_bar_2_save, qtable_save, counts)


    def traj_demo(self):
        perturbation = 0.3
        
        ###Demonstrations###
        allowPert = False
        nDemonstrations = 1
        trajectories = []
        postrajectories = []
        for i in range(nDemonstrations):
            reject = False
            print('trajectory n' + str(i))
            trajectory = []
            postrajectory = []
            action = 0
            t = 0
            record_actions = [0,0,0,0,0]
            last_action = 2
            n_changes = 0
            while not self.isFinal():
                direction = int(raw_input('Which direction?: '))
                pert = False
                if direction == 10:
                    reject = True
                    break
                preaction = list(self.position)
                print preaction
                if allowPert:
                    if direction == 8:
                        pert = self.up(perturbation)
                        action = 2
                    if direction == 2:
                        pert = self.down(perturbation)
                        action=3
                    if direction == 4:
                        pert = self.left(perturbation)
                        action=0
                    if direction == 6:
                        pert = self.right(perturbation)
                        action = 1
                    if direction == 5:
                        self.finish()
                        action = 4
                    record_actions[action] += 1
                    if last_action != action:
                        n_changes += 1
                        last_action = action
                    trajectory.append(self.feature(preaction,pert,action,t, record_actions, n_changes))
                    
                else:
                    action = 0
                    if direction == 8:
                        self.moveUp()
                        action = 2
                    if direction == 2:
                        self.moveDown()
                        action = 3
                    if direction == 4:
                        self.moveLeft()
                        action = 0
                    if direction == 6:
                        self.moveRight()
                        action = 1
                    if direction == 5:
                        self.finish()
                        action = 4
                    print preaction
                    record_actions[action] += 1
                    if last_action != action:
                        n_changes += 1
                        last_action = action
                    trajectory.append(list(self.feature(pos = preaction,errp = 0,
                                                        action = action,time_steps = t,
                                                        record_actions = record_actions,
                                                        n_changes = n_changes)))
                    
                postrajectory.append(preaction)
                t = t+1
                print('Position: '+str(self.position)+', perturbation: '+str(pert))
            self.goInitial()
            if not reject:
                trajectories.append(trajectory)
                postrajectories.append(postrajectory)
            return trajectories, postrajectories

    def convergence_criteria(self, it, scores10, criteria = 0):
        if criteria == 0:
            return (scores10.std() <= 0.5 and it >= 9 and abs(scores10.mean()) > 0)
        if criteria == 1:
            return  (scores10[1]-1 <= scores10[0] <= scores10[1]+1 and it >= 1 and abs(scores10.mean())>0)
        if criteria == 2:
            return it >= 0 #and abs(scores10.mean()) > 0



def main(modeGW = "continuous"):
    n,m,final = (5,6,(0,5))
    IRL_loop = gridworld(n,m,final_point = final, mode = modeGW)
    if IRL_loop.GWmode == "TID":
        (wsss, wslist, IRLmean, IRLstd, countsmean,
         countsstd, mu_save, mu_bar_2_save,
         qtable_save, t_i, postraj_train) = IRL_loop.IRL_iteration(uncertainerrp = IRL_loop.uncertainerrp_offline,
                                                                 chosen_trajectory = IRL_loop.chosen_trajectory_offline,
                                            track_incorrectness = IRL_loop.track_incorrectness_offline,
                                                                 save_data = IRL_loop.save_data_offline,
                                                                 IRLepsilon = IRL_loop.IRLepsilon_offline,
                                                                 gamma = IRL_loop.gamma_offline
                                                                 , n_iterations = IRL_loop.n_iterations_offline
                                                                 ,criteria = IRL_loop.criteria_offline
                                                                 ,plot = IRL_loop.plot_offline
                                                                 ,training = IRL_loop.training_offline
                                                                 ,epsilon = IRL_loop.epsilon_offline
                                                                 ,alpha = IRL_loop.alpha_offline
                                                                 ,postrajectories = IRL_loop.postrajectories_offline
                                                                 ,mode = IRL_loop.mode_offline
        )
        
        initialization1 = [np.array(mu_save), np.array(mu_bar_2_save), qtable_save]
        #######
        #a = raw_input('press ENTER')
        
        (wsss, wslist, IRLmean, IRLstd, countsmean,
         countsstd, mu_save, mu_bar_2_save,
         qtable_save, counts) = IRL_loop.IRL_iteration(uncertainerrp = IRL_loop.uncertainerrp_online,
                                                                                 chosen_trajectory = IRL_loop.chosen_trajectory_online,
                                                            track_incorrectness = IRL_loop.track_incorrectness_online,
                                                                                 save_data = IRL_loop.save_data_online,
                                                                                 limit = IRL_loop.limit_online,
                                                                                 IRLepsilon = IRL_loop.IRLepsilon_online,
                                                                                 gamma = IRL_loop.gamma_online
                                                                                 , n_iterations = IRL_loop.n_iterations_online
                                                                                 ,criteria = IRL_loop.criteria_online
                                                                                 ,initialization = initialization1
                                                                                 ,plot = IRL_loop.plot_online
                                                                                 ,epsilon = IRL_loop.epsilon_online
                                                                                 ,postrajectories = IRL_loop.postrajectories_online
                                                                                 ,mode = IRL_loop.mode_online
        )
        print postraj_train
        print t_i
        
    else:
        ##############################################SCRIPTING###############################################
        #obstacleList1 = [(-1,2,2,2),(-2,4,0,4)]
        #postraj1 = ['']*2
        #postraj1[0] = [[[0,0],[1,0],[1,1],[0,1],[-1,1],[-2,1],[-2,2],[-2,3],[-1,3],[0,3],[1,3],[1,4],[1,5],[0,5]]]
        #postraj1[1] = [[[0,0],[-1,0],[-2,0],[-2,1],[-2,2],[-2,3],[-1,3],[0,3],[1,3],[1,4],[1,5],[0,5]]]
        #
        #obstacleList2 = [(-2,1,1,1),(1,4,2,4)]
        #postraj2 = ['']*2
        #postraj2[0] = [[[0,0],[1,0],[1,1],[0,1],[-1,1],[-2,1],[-2,2],[-2,3],[-1,3],[0,3],[1,3],[1,4],[1,5],[0,5]]]
        #postraj2[1] = [[[0,0],[-1,0],[-2,0],[-2,1],[-2,2],[-2,3],[-1,3],[0,3],[1,3],[1,4],[1,5],[0,5]]]
        #
        #obstacleList3 = [(-1,3,1,3),(1,1,1,2)]
        obstacleList3 = [(-1,3,-1,3),(0,3,0,3),(1,3,1,3),(1,2,1,2),(1,1,1,1)]
        postraj3 = ['']*2
        #postraj3[0] = [[[0,0],[1,0],[2,0],[2,1],[2,2],[2,3],[2,4],[2,5],[1,5],[0,5]]]
        postraj3[0] = [[[0,0],[-1,0],[-2,0],[-2,1],[-2,2],[-2,3],[-2,4],[-2,5],[-1,5],[0,5]]]
        postraj3[1] = [[[0,0],[0,1],[0,2],[-1,2],[-2,2],[-2,3],[-2,4],[-1,4],[0,4],[0,5]]]
        
        #obstacleList4 = [(-1,4,-1,4),(0,1,1,1),(0,2,0,2),(1,4,2,4)]
        #postraj4 = ['']*2
        #postraj4[0] = [[[0,0],[1,0],[1,1],[0,1],[-1,1],[-2,1],[-2,2],[-2,3],[-1,3],[0,3],[1,3],[1,4],[1,5],[0,5]]]
        #postraj4[1] = [[[0,0],[-1,0],[-2,0],[-2,1],[-2,2],[-2,3],[-1,3],[0,3],[1,3],[1,4],[1,5],[0,5]]]
        #
        IRL_loop.defineObstacles(obstacleList3)
        postraj = postraj3
        #IRL_loop.qtableObj()
        
        track_incorrectness = True
        save_data = False
        uncertainerrp = -1
        chosen_trajectory = -1
        limit = np.inf
        IRLepsilon = 0.0
        #gamma = 0.90 #77
        gamma = 0.80 #91
        #gamma = 0.70 #82
        n_iterations = 10
        criteria = 2
        t_i = 0
        auxiliar = True
        mode1 = "continuous"
        #mode2 = "manual"
        mode2 = IRL_loop.GWmode
        
        #ATTEMPT 3
        while t_i <= IRLepsilon and auxiliar == True:
            auxiliar = False
            (wsss, wslist, IRLmean, IRLstd, countsmean,
             countsstd, mu_save, mu_bar_2_save,
             qtable_save, t_i, postraj_train) = IRL_loop.IRL_iteration(uncertainerrp = uncertainerrp,
                                                             chosen_trajectory = chosen_trajectory,
                                        track_incorrectness = track_incorrectness,
                                                             save_data = save_data,
                                                             IRLepsilon = 0.01,
                                                             gamma = gamma
                                                             , n_iterations = 1
                                                             ,criteria = 1
                                                             ,plot = False
                                                             ,training = True
                                                             ,epsilon = 0.05
                                                             ,alpha = 0.5
                                                             ,postrajectories = postraj[0]
                                                             ,mode = mode1
        )
        
        initialization1 = [np.array(mu_save), np.array(mu_bar_2_save), qtable_save]
        #######
        #a = raw_input('press ENTER')
        
        (wsss, wslist, IRLmean, IRLstd, countsmean,
        countsstd, mu_save, mu_bar_2_save,
        qtable_save, counts) = IRL_loop.IRL_iteration(uncertainerrp = uncertainerrp,
                                                         chosen_trajectory = chosen_trajectory,
                                    track_incorrectness = track_incorrectness,
                                                         save_data = save_data,
                                                         limit = limit,
                                                         IRLepsilon = IRLepsilon,
                                                         gamma = gamma
                                                         , n_iterations = n_iterations
                                                         ,criteria = criteria
                                                         ,initialization = initialization1
                                                         ,plot = False
                                                         ,epsilon = 0
                                                         ,postrajectories = postraj[1]
                                                         ,mode = mode2
        )
        
        #print postraj_train
        print t_i
        
        #w = wslist[-1]
        #mu_aux, score, t, postraject, traject = Qgw.episode(uncertainerrp = uncertainerrp, weights=w,Etrajectpos=postraj, alpha = 0.0); print postraject
        #mu_aux, score, t, postraject, traject = Qgw.episode(uncertainerrp = uncertainerrp, weights=w,Etrajectpos=postraj, alpha = 0.0); print postraject
        #mu_aux, score, t, postraject, traject = Qgw.episode(uncertainerrp = 0.8, weights=w,Etrajectpos=postraj, alpha = 0.0); print postraject
        #mu_aux, score, t, postraject, traject = Qgw.episode(uncertainerrp = 0.8, weights=w,Etrajectpos=postraj, alpha = 0.0); print postraject
        #mu_aux, score, t, postraject, traject = Qgw.episode(uncertainerrp = 0.8, weights=w,Etrajectpos=postraj, alpha = 0.0); print postraject
        
        """
        traj , postraj = Qgw.load_trajectory(chosen_trajectory = 1);w = take_sample(wslist);mu, count, postraject, traject, timesteps = Qgw.QLearning(criteria = 1, uncertainerrp = 0.8, alpha = 0, Etrajectpos = postraj, w_i = w, limit = 30, continued = True);print timesteps
        mu, count, postraject, traject, timesteps = Qgw.continued_QLearning(uncertainerrp = 0.8, Etrajectpos = postraj, w_i = w, limit = 30, alpha = 0.0);print timesteps; print len(postraject)
        mu_aux, score, t, postraject, traject = Qgw.episode(uncertainerrp = 0.8, weights=w,Etrajectpos=postraj,limit = 30, alpha = 0.0); print t
        
        """
if __name__ == '__main__':
    main(modeGW = "TID")


