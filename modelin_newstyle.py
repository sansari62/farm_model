
"""
Created on Tue Oct  1 14:42:42 2019

@author: ansari
"""

##JH Jobst's comments start with ##JH

##JH
# general recommendations:
# - try to conform mostly (but not slavishly) to this style guide: https://www.python.org/dev/peps/pep-0008/
# - in particular:
# - use longer, "speaking" variable names, and avoid using "i" for different things
# - use blank lines to separate main blocks of code (I added some to give an example) 
# - give docstrings for all classes, methods, functions
# - use whitespace next to operators
# - make your editor use spaces instead of tabs and remove trailing whitespace at end of line
# - use 4 spaces for each indentation level

import random
import numpy as np
from scipy.stats import  powerlaw, expon,lognorm
import math
import pdb

###########################################################

output=open("newdata.txt","w+")
S = range(4)                     # list of stages
S_label = [ 'breeding', 'fattening','trader', 'slaughter']  # or whatever 'piglet production',
ns = [20,20,30,40]        # number of barns of every stage                       # 1.06   4.3079    3.01   0.611
theta = [expon.rvs(scale = 1 / 0.013),            #lambda=0.013
         lognorm.rvs(s = 1.27, scale  = math.exp(3.62)), 
         lognorm.rvs( s = 1.06 , scale  = math.exp(4.3079 )), 
         100*powerlaw.rvs(a = 1.42)]     #alpha=1.42
birth_rate = [0.98,0.09,0.0,0.0]
mortal_rate = [0.12,0.08,0.01,1]             # mortality rates

T = {}                 # A Set OF POSSIBLE TRANSITIONS
T = {(0,1,1,60,1,0.6),(1,2,1,120,1,0.6),(2,3,1,1,1,0.7)}#,(2,3,1,1,2,0.3),(3,2,1,2,2,0.8)}
barnlist = []
barn_index = {}  # dict of pairs (start_index, end_index) giving the index ranges of barns of each type
breeding_no=47894
fattening_no=31628
trader_no=15631
slaughterh_no=2755
class Barn:
    """
    describe the attributes and methods for each barn
    """

    def __init__(self, Barn_id, stage_type, capacity, destination, gis, Dlist): 
        """
        initializing each barn with attributes like id,type and capacity
        Dlist shows a list of queues inside each barn
        each barn has a glist for keeping gis (the id of last barn which sent a batch ) 
        """
        
        self.Barn_id = Barn_id  
        self.stage_type = stage_type
        self.capacity = capacity
        self.destination = destination
        self.Dlist = Dlist
        self.gis = gis
       
    def create_Dlist(self, T):      
        """
        create a zero Dlist at first for every successor stage
        T is a set of successor stages for current stage s
        """
        for transition in T:
            if transition[0] == self.stage_type:           #x[0] is the index of source stage
                self.destination[transition[1]] = transition
                self.gis[transition[1]] = random.choice(barn_index[transition[1]])   #x[1]: index of next stage ;#choose randomly one from all barns in the next stage as default gis for each queue in current barn
                self.Dlist[transition[1]] = [] 
                   
    def compute_free_capacity(self):
        """
        compute the current free size of barn j 
        """
        return self.capacity - sum([len(self.Dlist[d]) for d in self.Dlist])
   
    def select_nextstage(self):
        """
        draw a successor stage s" (a queue in the next barn)
        proportional to ps's" to move animal into
        """
        probablity_list = [self.destination[dest][2] for dest in self.destination] 
        next_stage = np.random.choice([nextstage for nextstage in self.Dlist], p=probablity_list)
        return int(next_stage)
        
    
    def update_after_transition(self, i, j, x):
        """
        update Dlist of the current barn after moving a batch of 
        animal from barn i to barn j
        """
         #remove x enteries from qi in current barn 
        self.Dlist[i] = self.Dlist[i][x:]  ##JH changed this
        if mortal_rate[self.stage_type] < 1:                  #check if moral_rate<1
                for xi in range(x):
                    j.Dlist[j.select_nextstage()].append(0)  ##JH changed this

               
    def transfertoj(self, i, target, x, time):
        """
        moving x animals from barn i to barn j  at time t   
        """
          
        if random.random() < self.destination[i][5] and barnlist[self.gis[i]].compute_free_capacity() >= x:
            # send all x to last destination due to loyalty:
            j = barnlist[self.gis[i]]
            y = x
        else:
            # check if any potential destination has free capacity >= x:
            potential_destinations = barnlist[barn_index[target][0]:barn_index[target][1]+1]
            potential_js = [j for j in potential_destinations if j.compute_free_capacity() >= x]
            if len(potential_js) > 0:
                # send all x to a random destination with enough free capacity:
                j = random.choice(potential_js)
                y = x
            else:
                # check if any potential destination has free capacity >= qss':
                q = self.destination[i][4]
                potential_js = [j for j in potential_destinations if j.compute_free_capacity() >= q]
                if len(potential_js) > 0:
                    # send all x to a random destination with enough free capacity:
                    j = random.choice(potential_js)
                    y = j.compute_free_capacity()
                    assert q <= y < x
                else:
                    y = 0
        
        if y > 0:
            output.write(str(self.Barn_id) + "," + str(j.Barn_id) + "," + str(time) + "," + str(y) + "\n")
            self.update_after_transition(i, j, y)
        else:
            print("no transfer is possible from barn",self.Barn_id," at time: ",time)            
        
    def compute_X(self,i):
        """
        compute the value x of animalswith the age>dss'in queue i of current barn
        """
        return len([age for age in self.Dlist[i] if age >= self.destination[i][3]])
    

    def add_newborn(self, i):
        """
        add k newborn to queue i of current barn
        """
        k = 0
        free_capacity = self.compute_free_capacity()
        if(free_capacity > 0):
            if(birth_rate[self.stage_type] != 0):           #check birth_rate for current barn
                p = 1 / (1 + self.destination[i][2] * birth_rate[self.stage_type])  
                 # so that np.random.geometric(p) has mean  1 / p = 1 + pis * bs,
                # hence k has mean  1 / p - 1 = pis * bs  as required
                #SA I removed -1 because every time it produce 0
                k = min(np.random.geometric(p), free_capacity)      #k is drawn from geometric distribution with expected value pis*bs
                self.Dlist[i] = self.Dlist[i] + [0] * k           #add k newborn to queue i
                
    def die_animal(self,i):
         """
         removing animals from queues with ms probability
         """
         for animal in self.Dlist[i]:             #for every animal in  queue i of the current barn
            x=random.random()
            if x < mortal_rate[self.stage_type]:                  
               self.Dlist[i].remove(animal)  
           
          
    def process_barn(self, time):
        """
        process current barn, means process all queue inside  
        """
        for i in self.Dlist:                    #process every queue belong to next stages
            x = 0
            
            if time == 1:                          #for the first day just add  k new born to Dlist 
                self.add_newborn(i)               
            else:                 #if time>1
                #to let animals die before newborn are added:
#                if time == 120:
#                    pdb.set_trace()
                #pdb.set_trace()
                #self.Dlist[i] = [age + 1 for age in self.Dlist[i] if random.random() > mortal_rate[self.stage_type]]
                self.die_animal(i)
                self.Dlist[i] = [age + 1 for age in self.Dlist[i]]
                self.add_newborn(i)               
                #distination is a list of tuples with the format(s,s',pss',qss',lss')
                target = self.destination[i][1]                       
                if len(self.Dlist[i]) > self.destination[i][4]:  
                    #check to see if size of current queue is at least as q 
                        if self.Dlist[i][self.destination[i][4] - 1] >= self.destination[i][3] :     
                            #check if in barni at stage s we reached to minimum batch size
                            x = self.compute_X(i)                                          
                            self.transfertoj(i, target, x, time)
                             
                         
                    
def proceed_over_time(time_limit):
    """
    process barns  in a randomly order over time     
    """
    index_list = []
    for t in range(1, time_limit + 1):
        print("t =", t)
        index_list = random.sample(range(0, len(barnlist)), len(barnlist))      
        for i in index_list:        #process barnlist in a random order
            barnlist[i].process_barn(t)
        
def compute_indexRange():
    """
    compute ranges for accessing list of barns in every stage
    """
    end_index = 0             
    for i in S:
        if i == 0:
            start_index = 0
        else:
            start_index = end_index + 1   
        end_index = start_index +ns[i] - 1
        barn_index[i] = (start_index, end_index)
        
###########################################THE MAIN SECTION START HERE##################################################################

def main():
             
    # initialize data:
    Bid = 0           #barn ID
    for stage in S: 
        for j in range(ns[stage]):           #create ns Barn for each stage in S
            barnlist.append(Barn(Bid, stage,
                                 int(round(theta[stage])),
                                   {}, {}, {}))
            Bid += 1
    compute_indexRange()
    #pdb.set_trace()
    # process all barns at time 0:
    for i in range(len(barnlist)):
        barnlist[i].create_Dlist(T)
             
    # process all barns at time t > 0:
    time_limit = 4000
    proceed_over_time(time_limit) 
    output.close()

if __name__ == "__main__":
    main()
