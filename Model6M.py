# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 09:53:21 2020

@author: ansari
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Dec 25 13:45:15 2019

@author: ansari
"""
import random
from random import random as unif
from scipy.stats import  powerlaw, expon, lognorm, beta
import math
import time
from numpy import random as np
import pdb

###########################################################
random.seed(10)
output=open("syndata10M.txt","w+")
S = range(4)                     # list of stages
S_label = [ 'breeding', 'fattening','trader', 'slaughter']  # or whatever 'piglet production',
                       # number of barns of every stage
ns=[4500,3000,1000,1500]
#ns=[360,340,120,180]
theta = [lambda: expon.rvs(scale = 1 / 0.013),            #lambda=0.013
        lambda: 2 * lognorm.rvs(s = 1.27, scale  = math.exp(3.62)),
        lambda: 5 * lognorm.rvs(scale = 23.97,s = 1.83,loc = 1), 
        lambda: 2 * lognorm.rvs(s = 1.32, scale = math.exp(4.54))]
                     
birth_rate =  [ 0.037, 0, 0, 0]      #change values 
mortal_rate = [ 0.0042, 0.0008, 0.000, 1]  

min_bch_size = [lambda: lognorm.rvs(s=1.44,scale=math.exp(3.23)), 
                lambda: lognorm.rvs(s=0.89,scale=math.exp(4.07)),
                lambda: expon.rvs(scale =1/0.0078 ) ]  
  
loyalty = [lambda: beta.rvs(0.83, 0.7),
           lambda: beta.rvs(1.54, 0.67),
           lambda: powerlaw.rvs(0.54)]       

# T is a set of possible transactions
T = [(0,1,80,0.5),(1,2,100,0.7),(2,3,0,1)]
barnlist = []
l = [0] * ns[0]
barn_index = {}  # dict of pairs (start_index, end_index) giving the index ranges of barns of each type


"""
A = birth_rate * capacity
p = 1 / (1 + A) # the parameter p in the geometeic distrib.
l[barn id] = log(1 - p)

then when drawing k0, do:

k0 = int(log(rand()) / l[barn id])
"""
class Barn:
    """
    describe the attributes and methods for each barn
    """

    def __init__(self, Barn_id, stage_type, capacity, gis, Dlist): 
        """
        initializing each barn with attributes like id,type and capacity
        Dlist shows a queue inside each barn
        each barn has a gis for keeping gis (the id of last barn which sent a batch ) 
        """
        
        self.Barn_id = Barn_id  
        self.stage_type = stage_type
        self.capacity = capacity
        self.Dlist = Dlist
        self.gis = gis
        
       
       
    def create_Dlist(self):      
        """
        create a zero Dlist at first for every successor stage in every barn
        based on barn type
        T is a set of successor stages for current stage s
        """
        #for gis choose randomly one from all barns in the next stage as default gis for each queue in 
        #current barn
        self.capacity = int((theta[self.stage_type]()))+1
        stage = self.stage_type
        if(birth_rate[self.stage_type] != 0):     
            # only for breeding barns at t=0 add animals
            A = birth_rate[self.stage_type] * self.capacity
            p = 1 / (1 + A)          # the parameter p in the geometeic distrib.  
            print("the value is:", 1-p)
            l[self.Barn_id] = math.log(1 - p)  
            
        if stage < 2:   
            #initialization for breeding and fattening farms
            self.gis[stage+1] =  random.choice(range(barn_index[stage+1][0],barn_index[stage+1][1]+1)) 
            self.gis[stage+2] =  random.choice(range(barn_index[stage+2][0],barn_index[stage+2][1]+1)) 
            self.Dlist[0] = []
            
        else:
            if stage == 2:    #initialization for trader farm
                     self.gis[1] = random.choice(range(barn_index[1][0],barn_index[1][1]+1))
                     self.gis[3] = random.choice(range(barn_index[3][0],barn_index[3][1]+1))
                     self.Dlist[1] = []
                     self.Dlist[3] = []
            else:
                self.Dlist[0] = []    #initialization for slauhter farm

                                   
    def compute_free_capacity(self):
        """
        compute the current free size of barn j 
        """
        return self.capacity -  sum([len(self.Dlist[d]) for d in self.Dlist])
   
    def update_after_transition(self, queue,next_stage, j, x):
        """
        update Dlist of the current barn after moving a batch of 
        animal from barn i to barn j,remove x enteries from queue in
        the current barn 
        """
        self.Dlist[queue] = self.Dlist[queue][x:]  
        #if moving pigs to traders check for sender:                  
        if next_stage == 2:
            #for pigs sent by breeding farms put them in the first queue of trader
            if self.stage_type== 0:
                for xi in range(x):
                    j.Dlist[1].append(0)
            else:
                #for those pigs sent by fattening farms put them in the second queue of trader
                for xi in range(x):
                    j.Dlist[3].append(0)
        else:
            #for sending to other types just put them in their queue
            for xi in range(x):
                j.Dlist[0].append(0)
            
                   
               
    def transfertoj(self, queue, next_stage, x, time, q):
        """
        moving x animals from barn i to barn j  at time t   
        """
          
        if random.random() < loyalty[self.stage_type]() and barnlist[self.gis[next_stage]].compute_free_capacity() >= x:
            # send all x to last destination due to loyalty:
            j = barnlist[self.gis[next_stage]]
            y = x
        else:
            # check if any potential destination has free capacity >= x:
            potential_destinations = barnlist[barn_index[next_stage][0]:barn_index[next_stage][1]+1]
            potential_js = [i for i in potential_destinations if i.compute_free_capacity() >= x]
            if len(potential_js) > 0:
                # send all x to a random destination with enough free capacity:
                j = random.choice(potential_js)
                y = x
            else:
                # check if any potential destination has free capacity >= qss':
                #q = self.destination[3]
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
            self.update_after_transition(queue, next_stage, j, y)
            print(self.stage_type,j.stage_type)
        else:
            #pass
            print("no transfer is possible from barn",self.Barn_id," at time: ",time)            
        
    def compute_X(self, queue):
        """
        compute the value x of animals with the age>dss'in queue i of current barn
        """
        return len([age for age in self.Dlist[queue] if age >= T[self.stage_type][2]])
    

    def add_newborn(self):
        """
        add k newborn to queue i of current barn
        """
        k = 0
        free_capacity = self.compute_free_capacity()
        if(free_capacity > 0):
            #if(birth_rate[self.stage_type] != 0):           #check birth_rate for current barn
                #k0 = 1 + int(-math.log(unif()) * (birth_rate[self.stage_type] - 1) + 0.5)
               #k=min(poisson.rvs(birth_rate[self.stage_type]),free_capacity)
                k0 = int(math.log(np.rand()) / l[self.Barn_id])
                k = min( k0 , free_capacity )
                self.Dlist[0] = self.Dlist[0] + [0] * k           #add k newborn to queue i
                
    def die_animal(self, queue):
         """
         removing animals from queues with ms probability
         """
         for animal in self.Dlist[queue]:             #for every animal in  queue i of the current barn
             if random.random() < mortal_rate[self.stage_type]:                  
                self.Dlist[queue].remove(animal)  
           
          
    def process_barn(self, time):
        """
        process current barn(just for breeding and fattening), means process all queue inside  
        """
        x = 0
        #if time==5 :#,some pigs may die and other remaining's age increased by 1
#          pdb.set_trace()
        queue = 0    # only one queue is available in breeding and fatteing farms
        self.die_animal(queue)
        self.Dlist[queue] = [age + 1 for age in self.Dlist[queue]]
        if(birth_rate[self.stage_type] != 0):    # check the birth rate before function call to  speedup
           self.add_newborn()               
        #distination is a  tuple with the format(src,target,min_age,min_bch_size,loyal_rate)
        q = int(min_bch_size[self.stage_type]())           
        if len(self.Dlist[queue]) > q :  
            #check to see if size of current queue is at least as q 
                if self.Dlist[queue][q - 1] >= T[self.stage_type][2] :     
                    #check if in barni at stage s we reached to minimum batch size
                    x = self.compute_X(queue)  # compute batch_size to move
                    if self.stage_type == 0:
                        # breeding farm with 60% probabality send to trader and with the 40% 
                        #probability send to fatttening
                        if random.random()< 0.4 :
                            next_stage = 1
                        else:
                            next_stage = 2
                    else:
                        #for fattening barns with 30% probability send to slaughter
                        #and  with 70% probablity send to trader
                        if random.random() < 0.3:
                            next_stage = 3
                        else:
                            next_stage = 2                            
                    self.transfertoj(queue,next_stage, x, time, q)
                         
       
                 
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
               barnlist[i].Dlist[0] = []                  
            else:
                #for trader barns, check posiible animal movements                      
                if barnlist[i].stage_type == 2: 
                    for queue in barnlist[i].Dlist :
                        if len(barnlist[i].Dlist[queue])>0:
                            barnlist[i].die_animal(queue)
                            q = int(min_bch_size[barnlist[i].stage_type]()) 
                            next_stage = queue
                            barnlist[i].transfertoj(queue, next_stage, len(barnlist[i].Dlist[queue]),t,q)
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
        for j in range(ns[stage]):         #create ns Barn for each stage in S
            barnlist.append(Barn(Bid, stage,
                                 0,
                                   {}, {}))
            Bid += 1
    compute_indexRange()
    
    #pdb.set_trace()
    # process all barns at time 0:
    for i in range(len(barnlist)):
        barnlist[i].create_Dlist()
#    print("the capacity of barn 0: ",barnlist[0].capacity,"\n the capacity of barn 2: ",
#          barnlist[2].capacity,"\nthe capacity of barn10: ",
#          barnlist[10].capacity,"\nthe capacity of barn 458: ",barnlist[458].capacity,
#          "\nthe capacity of barn 460: ",barnlist[460].capacity,
#          "\nthe capacity of barn 465: ",barnlist[465].capacity,"\nthe capacity of barn 810: ",
#          barnlist[810].capacity,"\nthe capacity of barn 900: ",barnlist[900].capacity,
#          "\nthe capacity of barn 970: ",barnlist[970].capacity,"\nthe capacity of barn 980: ",
#          barnlist[980].capacity)
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
