# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 10:37:37 2019

@author: SARA
"""
import random
from random import random as unif
from scipy.stats import  powerlaw, expon,lognorm
import math
import time
#import pdb

###########################################################
random.seed(10)
output=open("syndata10006.txt","w+")
S = range(4)                     # list of stages
S_label = [ 'breeding', 'fattening','trader', 'slaughter']  # or whatever 'piglet production',
#ns = [45426, 34518, 15631, 2333]                        # number of barns of every stage
ns =[ 455, 345, 156, 44 ] #[80,40,20,10]#[ 220, 170, 70, 40 ]
theta = [lambda: expon.rvs(scale = 1 / 0.013),            #lambda=0.013
         lambda: 2*lognorm.rvs(s = 1.27, scale  = math.exp(3.62)), 
         lambda: 3.1*lognorm.rvs( s = 1.06 , scale  = math.exp(4.3079 )), 
         lambda: 30*100*powerlaw.rvs(a = 1.42)]              #alpha=1.42
birth_rate =  [1.81,0.2,0.0,0.0]
mortal_rate = [0.0042,0.0008,0.0001,1]             

# T is a set of possible transactions
T = {(0,1,60,1,0.6),(1,2,120,1,0.6),(2,3,0,1,0.7)}
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
        Dlist shows a queue inside each barn
        each barn has a gis for keeping gis (the id of last barn which sent a batch ) 
        """
        
        self.Barn_id = Barn_id  
        self.stage_type = stage_type
        self.capacity = capacity
        self.destination = destination
        self.Dlist = Dlist
        self.gis = gis
        if(birth_rate[self.stage_type] != 0):     
            # for breeding and fattening time at t=0 add animals
            self.add_newborn()
       
    def create_Dlist(self):      
        """
        create a zero Dlist at first for every successor stage
        T is a set of successor stages for current stage s
        """
        for transition in T:
            if transition[0] == self.stage_type:           # transition[0] is the index of source stage
                self.destination = transition
                self.gis = random.choice(range(barn_index[transition[1]][0],barn_index[transition[1]][1]+1))   #transition[1]: index of next stage ;#choose randomly one from all barns in the next stage as default gis for each queue in current barn
        self.capacity = int((theta[self.stage_type]()))
                                   
    def compute_free_capacity(self):
        """
        compute the current free size of barn j 
        """
        return self.capacity - len(self.Dlist)
   
    def update_after_transition(self, j, x):
        """
        update Dlist of the current barn after moving a batch of 
        animal from barn i to barn j,remove x enteries from queue in
        the current barn 
        """
        self.Dlist = self.Dlist[x:]  
        #if mortal_rate[self.stage_type] < 1:                  #check if moral_rate<1
        for xi in range(x):
            j.Dlist.append(0)

               
    def transfertoj(self, target, x, time):
        """
        moving x animals from barn i to barn j  at time t   
        """
          
        if random.random() < self.destination[4] and barnlist[self.gis].compute_free_capacity() >= x:
            # send all x to last destination due to loyalty:
            j = barnlist[self.gis]
            y = x
        else:
            # check if any potential destination has free capacity >= x:
            potential_destinations = barnlist[barn_index[target][0]:barn_index[target][1]+1]
            potential_js = [i for i in potential_destinations if i.compute_free_capacity() >= x]
            if len(potential_js) > 0:
                # send all x to a random destination with enough free capacity:
                j = random.choice(potential_js)
                y = x
            else:
                # check if any potential destination has free capacity >= qss':
                q = self.destination[3]
                potential_js = [i for i in potential_destinations if i.compute_free_capacity() >= q]
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
            print(self.stage_type,j.stage_type)
        else:
            #pass
            print("no transfer is possible from barn",self.Barn_id," at time: ",time)            
        
    def compute_X(self):
        """
        compute the value x of animals with the age>dss'in queue i of current barn
        """
        return len([age for age in self.Dlist if age >= self.destination[2]])
    

    def add_newborn(self):
        """
        add k newborn to queue i of current barn
        """
        k = 0
        free_capacity = self.compute_free_capacity()
        if(free_capacity > 0):
            #if(birth_rate[self.stage_type] != 0):           #check birth_rate for current barn
                k0 = 1 + int(-math.log(unif()) * (birth_rate[self.stage_type] - 1) + 0.5)
               #k=min(poisson.rvs(birth_rate[self.stage_type]),free_capacity)
                k = min( k0 , free_capacity )
                self.Dlist = self.Dlist + [0] * k           #add k newborn to queue i
                
    def die_animal(self):
         """
         removing animals from queues with ms probability
         """
         for animal in self.Dlist:             #for every animal in  queue i of the current barn
             if random.random() < mortal_rate[self.stage_type]:                  
                self.Dlist.remove(animal)  
           
          
    def process_barn(self, time):
        """
        process current barn, means process all queue inside  
        """
        x = 0
#        if time==5 :#,some pigs may die and other remaining's age increased by 1
#          pdb.set_trace()
        self.die_animal()
        self.Dlist = [age + 1 for age in self.Dlist]
#       if(birth_rate[self.stage_type] != 0):    # check the birth rate before function call to  speedup
        self.add_newborn()               
        #distination is a  tuple with the format(src,target,min_age,min_bch_size,loyal_rate)
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
            if barnlist[i].stage_type == 3:     # for slaughters only empty the queue 
               barnlist[i].Dlist = []                  
            else:
                #for trader barns, check posiible animal movements                      
                if barnlist[i].stage_type == 2: 
                    if len(barnlist[i].Dlist)>0:
                        barnlist[i].die_animal()
                        barnlist[i].transfertoj(barnlist[i].destination[1], len(barnlist[i].Dlist),t)
                else:
                    # for Breeding and Fattenig barns 
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
                                 0,
                                   (0,0,0,0,0), 0, []))
            Bid += 1
    compute_indexRange()
    #pdb.set_trace()
    
    # process all barns at time 0:
    for i in range(len(barnlist)):
        barnlist[i].create_Dlist()
    print("the capacity of barn 0: ",barnlist[0].capacity,"\n the capacity of barn 2: ",
          barnlist[2].capacity,"\nthe capacity of barn10: ",
          barnlist[10].capacity,"\nthe capacity of barn 458: ",barnlist[458].capacity,
          "\nthe capacity of barn 460: ",barnlist[460].capacity,
          "\nthe capacity of barn 465: ",barnlist[465].capacity,"\nthe capacity of barn 810: ",
          barnlist[810].capacity,"\nthe capacity of barn 900: ",barnlist[900].capacity,
          "\nthe capacity of barn 970: ",barnlist[970].capacity,"\nthe capacity of barn 980: ",
          barnlist[980].capacity)
    # process all barns at time t > 0:
    capacityB = sum([barn.capacity for barn in barnlist[barn_index[0][0]:barn_index [0][1]+1]] )
    capacityF = sum([barn.capacity for barn in barnlist[barn_index[1][0]:barn_index [1][1]+1]] )
    capacityT = sum( [barn.capacity for barn in barnlist[barn_index[2][0]:barn_index [2][1]+1]] )
    capacityS = sum([barn.capacity for barn in barnlist[barn_index[3][0]:barn_index [3][1]+1]] )
    print (capacityB," ",capacityF," ",capacityT, " ",capacityS," ")
    assert capacityB<=capacityF<=capacityT 
    assert capacityT<=capacityS
    
    time_limit = 2190  #1460    #2190    # observation period set to 6 years
    proceed_over_time(time_limit) 
    output.close()
    finish = time.time() 
    print("the execution time is: ",finish - start)
if __name__ == "__main__":
    main()
