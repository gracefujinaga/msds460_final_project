'''
Dr. Miller's Coffee Shop Simulation Code used

Need to adjust and make more tweaks
'''

'''
Imports
'''

import numpy as np # for random number distributions
import pandas as pd # for event_log data frame
pd.set_option('display.max_rows', 20)
pd.set_option('display.max_columns', 10)
import queue # add FIFO queue data structure
from functools import partial, wraps
import simpy # discrete event simulation environment
import random

'''
Problem Set Up
'''

## set up for queue 1
num_sp = 3  # number of call center service providers
min_service_time_1 = 2 # minutes (60 seconds)
mean_service_time_1 = 5 # minutes (120 seconds)
max_service_time_1 = 25 # minutes (300 seconds)
mean_iat_1= 2 # vary from 1 to 10 minutes (60 to 600 seconds)
reneg_queue_length_1 = 10

## set up for queue 2
num_managers = 2
min_service_time_2 = 10 # minutes  - this is in ADDITION to previous service time, not total
mean_service_time_2 = 20 
max_service_time_2 = 45 
reneg_queue_length_2 = 3

# reproducible flag
obtain_reproducible_results = True

# time setup
simulation_hours = 10
fixed_simulation_time =  simulation_hours*60*60   

parameter_string_list = [str(simulation_hours),'hours',
              str(num_sp),str(min_service_time_1),
              str(mean_service_time_1),str(max_service_time_1),
              str(mean_iat_1),str(reneg_queue_length_1)]
separator = '-'        
simulation_file_identifier = separator.join(parameter_string_list)

print(simulation_file_identifier)

def random_service_time(minimum_service_time, mean_service_time, maximum_service_time) :
    try_service_time = np.random.exponential(scale = mean_service_time)
    if (try_service_time < minimum_service_time):
        return(minimum_service_time)
    if (try_service_time > maximum_service_time):
        return(maximum_service_time)
    if (try_service_time >= minimum_service_time) and (try_service_time <= maximum_service_time):
        return(try_service_time)

'''
Set up helper functions for queue 1
'''
    
def service_process_1(env, caseid_queue, event_log):
    # must have available sp to provide service... freeze until request can be met
    with available_sp.request() as req:
        yield req  # wait until the request can be met.. there must be an available sp
        queue_length_on_entering_service = caseid_queue.qsize()
        caseid = caseid_queue.get()
        print("Begin_service caseid =",caseid,'time = ',env.now,'initial_queue_length =',queue_length_on_entering_service)
        env.process(event_log_append(env, caseid, env.now, 'begin_service', event_log)) 
        # schedule end_service event based on service_time
        service_time = round(60*random_service_time(min_service_time_1,mean_service_time_1,max_service_time_1))   
        yield env.timeout(service_time)  # sets begin_service as generator function
        queue_length_on_leaving_service = caseid_queue.qsize()
        print("End_service caseid =",caseid,'time = ',env.now,'initial_queue_length =',queue_length_on_leaving_service)
        env.process(event_log_append(env, caseid, env.now, 'end_service', event_log))

'''
Helpers for part 2 of the queue
'''
    
def service_process_2(env, caseid_queue, event_log):
    # must have available manager to provide service
    with available_managers.request() as req_2:
        yield req_2  # wait until the request can be met
        queue_length_on_entering_service = caseid_queue.qsize()
        caseid = caseid_queue.get()

        print("Begin_elevated_service caseid =",caseid,'time = ',env.now,'elevated_queue_length =',queue_length_on_entering_service)
        env.process(event_log_append(env, caseid, env.now, 'begin_elevated_service', event_log)) 

        # schedule end_service event based on service_time
        service_time = round(60*random_service_time(min_service_time_2,mean_service_time_2,max_service_time_2))   
        yield env.timeout(service_time)  # sets begin_service as generator function

        queue_length_on_leaving_service = caseid_queue.qsize()

        print("End_elevated_service caseid =",caseid,'time = ',env.now,'elevated_queue_length =',queue_length_on_leaving_service)
        env.process(event_log_append(env, caseid, env.now, 'end_elevated_service', event_log))
    

def reneg(caseid, id, queue) :
    if id == 2:
        print_string = "Customer reneg frome elevated service caseid="
    else : 
        print_string = "Customer reneg caseid="
    print(print_string,caseid,'time = ',env.now,'queue_length =',queue.qsize()) 
    env.process(event_log_append(env, caseid, env.now, 'reneg', event_log)) 

'''
Starting function for the simulation
'''
def initial_call(env, caseid, caseid_queue_1, caseid_queue_2, event_log):
    # generates new customers... arrivals
    caseid = 0
    while True:  # infinite loop for generating arrivals
        # get the service process started
        # must have waiting customers to begin service
    
        # schedule the time of next customer arrival       
        # by waiting until the next arrival time from now
        # when the process yields an event, the process gets suspended
        inter_arrival_time = round(60*np.random.exponential(scale = mean_iat_1))
        print("NEXT ARRIVAL TIME: ", env.now + inter_arrival_time)

        yield env.timeout(inter_arrival_time)  # generator function waits

        # env.timeout does not advance the clock. when an event/process calls env.timeout, 
        # that process waits until the clock gets to that time, it does not block 
        # other agents from doing stuff. Other processes can still do stuff 
        # while the first process is waiting for env.timeout to finish.
        caseid += 1
        time = env.now
        activity = 'arrival'
        env.process(event_log_append(env, caseid, time, activity, event_log)) 
        yield env.timeout(0) 

        # TODO: we would change right here
        if caseid_queue_1.qsize() < reneg_queue_length_1:
            caseid_queue_1.put(caseid)   

            print("Customer joins queue caseid =",caseid,'time = ',env.now,'initial_queue_length =',caseid_queue_1.qsize())

            time = env.now
            activity = 'join_queue'
            env.process(event_log_append(env, caseid, time, activity, event_log)) 
            env.process(service_process_1(env,  caseid_queue_1, event_log))   

            if random.random() < 0.15:
                caseid_queue_2.put(caseid)   
                activity = 'service request elevated'
                if caseid_queue_2.qsize() < reneg_queue_length_2:
                    env.process(event_log_append(env, caseid, time, activity, event_log)) 
                    env.process(service_process_2(env,  caseid_queue_2, event_log))
                else :
                    reneg(caseid, 2, caseid_queue_2)

        else:
            reneg(caseid, 0, caseid_queue_1)


'''        
---------------------------------------------------------
set up event tracing of all simulation program events 
controlled by the simulation environment
that is, all timeout and process events that begin with "env."
documentation at:
  https://simpy.readthedocs.io/en/latest/topical_guides/monitoring.html#event-tracing
  https://docs.python.org/3/library/functools.html#functools.partial
'''
def trace(env, callback):
     """Replace the ``step()`` method of *env* with a tracing function
     that calls *callbacks* with an events time, priority, ID and its
     instance just before it is processed.
     note: "event" here refers to simulaiton program events
     """

     def get_wrapper(env_step, callback):
         """Generate the wrapper for env.step()."""
         @wraps(env_step)
         def tracing_step():
             """Call *callback* for the next event if one exist before
             calling ``env.step()``."""
             if len(env._queue):
                 t, prio, eid, event = env._queue[0]
                 callback(t, prio, eid, event)
             return env_step()
         return tracing_step

     env.step = get_wrapper(env.step, callback)

def trace_monitor(data, t, prio, eid, event):
     data.append((t, eid, type(event)))

def test_process(env):
     yield env.timeout(1)


'''
---------------------------------------------------------
set up an event log for recording events
as defined for the discrete event simulation
we use a list of tuples for the event log
documentation at:
  https://simpy.readthedocs.io/en/latest/topical_guides/monitoring.html#event-tracing
'''     
def event_log_append(env, caseid, time, activity, event_log):
    event_log.append((caseid, time, activity))
    yield env.timeout(0)


'''
---------------------------------------
set up the SimPy simulation environment
and run the simulation with monitoring
---------------------------------------
'''
if obtain_reproducible_results: 
    np.random.seed(9999)

# set up simulation trace monitoring for the simulation
data = []

# bind *data* as first argument to monitor()
this_trace_monitor = partial(trace_monitor, data)

env = simpy.Environment()
trace(env, this_trace_monitor)

env.process(test_process(env))

# implement FIFO queue to hold caseid values
caseid_queue_1 = queue.Queue()
caseid_queue_2 = queue.Queue()

# set up limited sp resource
available_sp = simpy.Resource(env, capacity = num_sp)
available_managers = simpy.Resource(env, capacity = num_managers)

# dummy caseid values - will be omitted from the event_log
# prior to analyzing simulation results
caseid = -1  

# beginning record in event_log list of tuples of the form
# form of the event_log tuple item: (caseid, time, activity)
event_log = [(caseid,0,'null_start_simulation')]

env.process(event_log_append(env, caseid, env.now, 'start_simulation', event_log))
 
# call customer arrival process/generator to begin the simulation
env.process(initial_call(env, caseid, caseid_queue_1, caseid_queue_2, event_log))  

env.run(until = fixed_simulation_time)  # start simulation with monitoring and fixed end-time

'''
-----------------------------------------------------------------
report simulation program results to data frame and files

the SimPy simulation trace file provides a trace of events 
that is saved to a text file in the form
  (simulation time, index number of event, <class 'type of event'>)
this can be useful in debugging simulation program logic

the event_log list of tuples is saved to a text file of the form
  (caseid, time, 'activity')
the event_log list of tuples is also unpacked and saved as a
pandas data frame and saved to a comma-delimited text file 

-----------------------------------------------------------------
'''
simulation_trace_file_name = '/Users/gracefujinaga/Documents/Northwestern/MSDS_460/msds460_final_project/results/simulation-program-trace-' + simulation_file_identifier + '.txt'
with open(simulation_trace_file_name, 'wt') as ftrace:
    for d in data:
        print(str(d), file = ftrace)
print()        
print('simulation program trace written to file:',simulation_trace_file_name)

# convert list of tuples to list of lists
event_log_list = [list(element) for element in event_log]

# convert to pandas data frame
caseid_list = []
time_list = []
activity_list = []
for d in event_log_list:
    if d[0] > 0:
        caseid_list.append(d[0])
        time_list.append(d[1])
        activity_list.append(d[2])
event_log_df = pd.DataFrame({'caseid':caseid_list,
                             'time':time_list,
                             'activity':activity_list})    
print()
print('event log stored as Pandas data frame: event_log_df')

# save event log to comma-delimited text file
event_log_file_name = '/Users/gracefujinaga/Documents/Northwestern/MSDS_460/msds460_final_project/results/simulation-event-log-' + simulation_file_identifier + '.csv'
event_log_df.to_csv(event_log_file_name, index = False)  
print()
print('event log written to file:',event_log_file_name)
