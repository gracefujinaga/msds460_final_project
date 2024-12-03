'''
Dr. Miller's Coffee Shop Simulation Code used for more info
'''

'''
Imports
'''

import numpy as np # for random number distributions
import pandas as pd # for event_log data frame

pd.set_option('display.max_rows', 20)
pd.set_option('display.max_columns', 10)

import queue # add FIFO queue data structure
from collections import deque
from functools import partial, wraps
import simpy # discrete event simulation environment
import random

import matplotlib.pyplot as plt

'''
Problem Set Up, Global Vars
'''
# problem set up 
SIM_TIME = 100
CALL_ARRIVAL_RATE = 2


#Metrics
total_wait_time = 0
total_service_time = 0
total_calls = 0
total_reneged_calls = 0
total_escalated_calls = 0
service_times = []
wait_times = []  
escalated_service_times = []
escalated_wait_times = []

## set up for queue 1
num_sp = 6  # number of call center service providers
min_service_time_1 = 2 # minutes (60 seconds)
mean_service_time_1 = 5 # minutes (120 seconds)
max_service_time_1 = 25 # minutes (300 seconds)
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

parameter_string_list = [str(simulation_hours),'hours', str(num_sp), str(num_managers)]
separator = '-'        
simulation_file_identifier = separator.join(parameter_string_list)
simulation_trace_file_name = '/Users/gracefujinaga/Documents/Northwestern/MSDS_460/msds460_final_project/results/simulation-program-trace-' + simulation_file_identifier + '.txt'
event_log_file_name = '/Users/gracefujinaga/Documents/Northwestern/MSDS_460/msds460_final_project/results/simulation-event-log-' + simulation_file_identifier + '.csv'

'''
Set up helper functions for queue 1
'''
def call_process_1(env, caseid_queue, event_log):
    global total_wait_time, total_calls, total_service_time, service_times, wait_times

    # track total arrival time
    arrival_time = env.now

    # adding renege
    curr_queue_length = len(caseid_queue)
    if (curr_queue_length > reneg_queue_length_1):
        renege(1, caseid_queue)
        return

    # must have available sp to provide service... freeze until request can be met
    with available_sp.request() as req:
        yield req  

        queue_length_on_entering_service = len(caseid_queue)
        caseid = caseid_queue.popleft()

        wait_time = env.now - arrival_time
        total_wait_time += wait_time
        wait_times.append(wait_time / 60)

        # call_states["Connected"] += 1
        begin_service = env.now 
        print("Begin_service caseid =",caseid,'time = ',env.now,'initial_queue_length =',queue_length_on_entering_service)
        env.process(event_log_append(env, caseid, env.now, 'begin_service', event_log)) 

        # schedule end_service event based on normally distributed service_time
        service_time = round(60*random.uniform(min_service_time_1, max_service_time_1))  

        yield env.timeout(service_time)  

        # update metrics
        service_time = env.now - begin_service
        total_service_time += service_time
        service_times.append(service_time / 60)

        queue_len_on_leaving_service = len(caseid_queue)
        print("End_service caseid =",caseid,'time = ',env.now,'curr_queue_length =',queue_len_on_leaving_service)
        env.process(event_log_append(env, caseid, env.now, 'end_service', event_log))

'''
Helpers for part 2 of the queue
'''
def call_process_2(env, caseid_queue, event_log):
    global total_wait_time, total_calls, total_service_time, escalated_service_times, escalated_wait_times

    # track total arrival time
    arrival_time = env.now

    # adding renege
    curr_queue_length = len(caseid_queue)
    if (curr_queue_length > reneg_queue_length_2):
        renege(2, caseid_queue)
        return

    # must have available sp to provide service... freeze until request can be met
    with available_managers.request() as req_2:
        yield req_2  

        queue_length_on_entering_service = len(caseid_queue)
        caseid = caseid_queue.popleft()

        wait_time = env.now - arrival_time
        total_wait_time += wait_time
        escalated_wait_times.append(wait_time / 60)

        # call_states["Connected"] += 1
        print("Begin_escalated_service caseid =",caseid,'time = ',env.now,'escalated_queue_length =',queue_length_on_entering_service)
        begin_service = env.now 
        env.process(event_log_append(env, caseid, env.now, 'begin_escalated_service', event_log))

        # schedule end_service event based on normally distributed service_time
        service_time = round(60*random.uniform(min_service_time_2, max_service_time_2))  
        yield env.timeout(service_time)  

        # update metrics
        service_time = env.now - begin_service
        total_service_time += service_time
        escalated_service_times.append(service_time/ 60)

        queue_len_on_leaving_service = len(caseid_queue)
        print("End_escalated_service caseid =",caseid,'time = ',env.now,'curr_queue_length =',queue_len_on_leaving_service)
        env.process(event_log_append(env, caseid, env.now, 'end_escalated_service', event_log))

# if id is 2, then it is queue 2, if it is 1, queue 1
def renege(id, queue) :
    global total_reneged_calls
    total_reneged_calls += 1

    # removes most recently added - this is a safe assumption
    caseid = queue.popleft()
    if id == 2:
        print_string = "Customer renege frome escalated service caseid="
    else : 
        print_string = "Customer renege caseid="

    print(print_string,caseid,'time = ',env.now,'queue_length =',len(queue) )
    activity = f"renege_queue_{id}"
    env.process(event_log_append(env, caseid, env.now, activity, event_log)) 

# Starting function for the simulation
def initial_call(env, caseid, caseid_queue_1, caseid_queue_2, event_log):
    global total_wait_time, total_calls, total_reneged_calls, total_escalated_calls

    # set up caseid
    caseid = 0

    # infinite loop for continous arrivals for the set time
    while True:  
        inter_arrival_time = round(60*np.random.exponential(scale = CALL_ARRIVAL_RATE))
        print("NEXT ARRIVAL TIME: ", env.now + inter_arrival_time)
        yield env.timeout(inter_arrival_time)  # generator function waits

        total_calls += 1

        caseid += 1
        arrival_time = env.now
        time = arrival_time
        
        activity = 'arrival'
        env.process(event_log_append(env, caseid, time, activity, event_log)) 
        caseid_queue_1.append(caseid)

        yield env.timeout(0) 

        #if len(caseid_queue_1) > 0:
        print("Customer joins queue caseid =",caseid,'time = ',env.now,'initial_queue_length =',len(caseid_queue_1))
        time = env.now
             
        activity = 'join_queue_1'
        env.process(event_log_append(env, caseid, time, activity, event_log)) 
        env.process(call_process_1(env,  caseid_queue_1, event_log))   

        if random.random() < 0.15:
            total_escalated_calls += 1
            caseid_queue_2.append(caseid) 
            activity = 'join_queue_2 - service request escalated'
            env.process(event_log_append(env, caseid, time, activity, event_log)) 
            env.process(call_process_2(env,  caseid_queue_2, event_log))

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
run the simulation with monitoring
'''
if obtain_reproducible_results: 
    np.random.seed(9999)

# set up simulation trace monitoring for the simulation
data = []
curr_trace_monitor = partial(trace_monitor, data)
env = simpy.Environment()
trace(env, curr_trace_monitor)
env.process(test_process(env))

## NOTE THAT THESE are DEQUES: 
# append function puts caseid at the RIGHT of the queue
# popleft function pops caseid from the LEFT of the queue
# ie : FIRST OUT <--------- FIRST IN
caseid_queue_1 = deque()
caseid_queue_2 = deque()

# set up limited sp, manager resource
available_sp = simpy.Resource(env, capacity = num_sp)
available_managers = simpy.Resource(env, capacity = num_managers)

# dummy caseid value to start the simulation
caseid = -1  

# beginning record in event_log list of tuples of the form
# form of the event_log tuple item: (caseid, time, activity)
event_log = [(caseid,0,'null_start_simulation')]

# log events start the simulation
env.process(event_log_append(env, caseid, env.now, 'start_simulation', event_log))
env.process(initial_call(env, caseid, caseid_queue_1, caseid_queue_2, event_log))  

 # start simulation with monitoring and fixed end-time
env.run(until = fixed_simulation_time) 

'''
logging and trace files
'''
# write trace to trace file
with open(simulation_trace_file_name, 'wt') as ftrace:
    for d in data:
        print(str(d), file = ftrace)       
print('\n trace written to file:',simulation_trace_file_name)

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

# convert to df and save to csv
event_log_df = pd.DataFrame({'caseid':caseid_list, 'time':time_list,'activity': activity_list})    
event_log_df.to_csv(event_log_file_name, index = False)  
print('\n event log written to file:',event_log_file_name)


'''
metrics and figures
'''
average_wait_time = total_wait_time / (total_calls * 60) if total_calls > 0 else 0
renege_rate = total_reneged_calls / (total_calls * 60) if total_calls > 0 else 0

print("\nSimulation Results:")
print(f"Total Calls: {total_calls}")
print(f"Average Wait Time: {average_wait_time:.2f} minutes")
print(f"Renege Rate: {renege_rate:.2%}")
print(f"Total Reneged Calls: {total_reneged_calls}")
print(f"Total Escalated Calls: {total_escalated_calls}")

#Visualization
plt.figure(figsize=(10, 6))
plt.hist(wait_times, color='skyblue', edgecolor='black', alpha=0.7)
plt.title("Distribution of Initial Wait Times")
plt.xlabel("Wait Time (minutes)")
plt.ylabel("Frequency")
plt.show()

# Service Time Distribution
plt.figure(figsize=(10, 6))
plt.hist(service_times, color='green', edgecolor='black', alpha=0.7)
plt.title("Distribution of Initial Service Times")
plt.xlabel("Service Time (minutes)")
plt.ylabel("Frequency")
plt.show()

#Wait Time Distribution
plt.figure(figsize=(10, 6))
plt.hist(escalated_wait_times, color='skyblue', edgecolor='black', alpha=0.7)
plt.title("Distribution of Escalated Wait Times")
plt.xlabel("Wait Time (minutes)")
plt.ylabel("Frequency")
plt.show()

# Service Time Distribution
plt.figure(figsize=(10, 6))
plt.hist(escalated_service_times, color='green', edgecolor='black', alpha=0.7)
plt.title("Distribution of Escalated Service Times")
plt.xlabel("Service Time (minutes)")
plt.ylabel("Frequency")
plt.show()


# call statistics
#Call Outcomes
labels = ['resolved', 'reneged']
print(total_calls - total_reneged_calls)
sizes = [total_calls - total_reneged_calls, total_reneged_calls]

plt.figure(figsize=(8, 8))
plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=['lightgreen', 'lightcoral'])
plt.title("Call Outcomes")
plt.show()