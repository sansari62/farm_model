# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 12:21:53 2019

@author: ansari
"""
import random
from scipy.stats import  powerlaw, expon,lognorm,poisson
import math
import time
#import pdb

###########################################################
output=open("syndata.txt","w+")
S = range(4)                     # list of stages
S_label = [ 'breeding', 'fattening','trader', 'slaughter']  # or whatever 'piglet production',
ns = [45426, 34518, 15631, 2333]                        # number of barns of every stage 
theta = [expon.rvs(scale = 1 / 0.013),            #lambda=0.013
         lognorm.rvs(s = 1.27, scale  = math.exp(3.62)), 
         lognorm.rvs( s = 1.06 , scale  = math.exp(4.3079 )), 
         100*powerlaw.rvs(a = 1.42)]              #alpha=1.42
birth_rate =  [1.81,0.09,0.0,0.0]
mortal_rate = [0.00042,0.08,0.01,1]             

# T is a set of possible transactions
T = {(0,1,60,1,0.6),(1,2,120,1,0.6),(2,3,1,1,0.7)}
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
       
    def create_Dlist(self):      
        """
        create a zero Dlist at first for every successor stage
        T is a set of successor stages for current stage s
        """
        for transition in T:
            if transition[0] == self.stage_type:           # transition[0] is the index of source stage
                self.destination = transition
                self.gis = random.choice(barn_index[transition[1]])   #transition[1]: index of next stage ;#choose randomly one from all barns in the next stage as default gis for each queue in current barn
                                   
    def compute_free_capacity(self):
        """
        compute the current free size of barn j 
        """
        return self.capacity - sum(self.Dlist)
   
    def update_after_transition(self, j, x):
        """
        update Dlist of the current barn after moving a batch of 
        animal from barn i to barn j,remove x enteries from queue in
        the current barn 
        """
        self.Dlist = self.Dlist[x:]  
        if mortal_rate[self.stage_type] < 1:                  #check if moral_rate<1
                for xi in range(x):
                    j.Dlist.append(0)

               
    def transfertoj(self, target, x, time):
        """
        moving x animals from barn i to barn j  at time t   
        """
          
        if random.random() < self.destination[3] and barnlist[self.gis].compute_free_capacity() >= x:
            # send all x to last destination due to loyalty:
            j = barnlist[self.gis]
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
                q = self.destination[3]
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
            self.update_after_transition(j, y)
        else:
            print("no transfer is possible from barn",self.Barn_id," at time: ",time)            
        
    def compute_X(self):
        """
        compute the value x of animalswith the age>dss'in queue i of current barn
        """
        return len([age for age in self.Dlist if age >= self.destination[2]])
    

    def add_newborn(self):
        """
        add k newborn to queue i of current barn
        """
        k = 0
        free_capacity = self.compute_free_capacity()
        if(free_capacity > 0):
            if(birth_rate[self.stage_type] != 0):           #check birth_rate for current barn
               k=min(poisson.rvs(birth_rate[self.stage_type]),free_capacity)
               self.Dlist = self.Dlist + [0] * k           #add k newborn to queue i
                
    def die_animal(self):
         """
         removing animals from queues with ms probability
         """
         for animal in self.Dlist:             #for every animal in  queue i of the current barn
            x=random.random()
            if x < mortal_rate[self.stage_type]:                  
               self.Dlist.remove(animal)  
           
          
    def process_barn(self, time):
        """
        process current barn, means process all queue inside  
        """
        x = 0
        if time == 1:                   #for the first day just add  k new born to Dlist 
            self.add_newborn()               
        else:                 #if time>1,some pigs may die and other remaining's age increased by 1
            self.die_animal()
            self.Dlist = [age + 1 for age in self.Dlist]
            self.add_newborn()               
            #distination is a  tuple with the format(s,s',qss',lss')
            target = self.destination[1]                       
            if len(self.Dlist) > self.destination[3]:  
                #check to see if size of current queue is at least as q 
                    if self.Dlist[self.destination[3] - 1] >= self.destination[2] :     
                        #check if in barni at stage s we reached to minimum batch size
                        x = self.compute_X()                                          
                        self.transfertoj(target, x, time)
                         
                         
                 
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
   
    start = time.time()
    Bid = 0           #barn ID
    for stage in S: 
        for j in range(ns[stage]):           #create ns Barn for each stage in S
            barnlist.append(Barn(Bid, stage,
                                 int(round(theta[stage])),
                                   (0,0,0,0), 0, []))
            Bid += 1
    compute_indexRange()
    #pdb.set_trace()
    # process all barns at time 0:
    for i in range(len(barnlist)):
        barnlist[i].create_Dlist()
    # process all barns at time t > 0:
    time_limit = 400
    proceed_over_time(time_limit) 
    output.close()
    finish = time.time() 
    print("the execution time is: ",finish - start)
if __name__ == "__main__":
    main()
