import simpy
import random
import matplotlib.pyplot as plt

# Parameters (can change these however we would like "sensitivity analysis")
CALL_ARRIVAL_RATE = 2  #Increase call frequency
CALL_DURATION = (5, 15)  #Extend call durations to increase resource contention
HOLD_DURATION = (3, 8)  #Hold duration to reflect realistic caller patience
NUM_CSRS = 2  #Decreased available CSRs have more competition


#Metrics
total_wait_time = 0
total_calls = 0
total_dropped_calls = 0
wait_times = []  #Store wait times for visualization
call_states = {"Connected": 0, "Dropped": 0}  #Track call outcomes

#Simulate call
def call_process(env, csr, call_id):
    global total_wait_time, total_calls, total_dropped_calls
    
    arrival_time = env.now
    print(f"Call {call_id} arrived at {arrival_time:.2f}")

    #Request CSR
    with csr.request() as req:
        #Check if CSR is available or call will wait in the hold queue
        wait_result = yield req | env.timeout(random.uniform(*HOLD_DURATION))
        if req in wait_result:
            #CSR became available
            wait_time = env.now - arrival_time
            total_wait_time += wait_time
            wait_times.append(wait_time)
            call_states["Connected"] += 1
            print(f"Call {call_id} connected to CSR after waiting {wait_time:.2f} minutes")
            
            #Call duration while CSR is engaged
            yield env.timeout(random.uniform(*CALL_DURATION))
            print(f"Call {call_id} completed at {env.now:.2f}")
        else:
            #Call dropped if CSR not available within hold time
            total_dropped_calls += 1
            call_states["Dropped"] += 1
            wait_times.append(HOLD_DURATION[1])  #Max hold time as wait time for dropped calls
            print(f"Call {call_id} dropped after waiting on hold")

    total_calls += 1

#Generate calls
def call_generator(env, csr):
    call_id = 0
    while True:
        yield env.timeout(random.expovariate(1.0 / CALL_ARRIVAL_RATE))
        call_id += 1
        env.process(call_process(env, csr, call_id))

#Simulation set up 
env = simpy.Environment()
csr = simpy.Resource(env, capacity=NUM_CSRS)
env.process(call_generator(env, csr))

#Run simulation
SIM_TIME = 100  #Total simulation time in minutes
env.run(until=SIM_TIME)

#Results
average_wait_time = total_wait_time / total_calls if total_calls > 0 else 0
drop_rate = total_dropped_calls / total_calls if total_calls > 0 else 0

print("\nSimulation Results:")
print(f"Total Calls: {total_calls}")
print(f"Average Wait Time: {average_wait_time:.2f} minutes")
print(f"Drop Rate: {drop_rate:.2%}")
print(f"Total Dropped Calls: {total_dropped_calls}")

#Visualization
plt.figure(figsize=(10, 6))

#Wait Time Distribution
plt.hist(wait_times, bins=10, color='skyblue', edgecolor='black', alpha=0.7)
plt.title("Distribution of Wait Times")
plt.xlabel("Wait Time (minutes)")
plt.ylabel("Frequency")
plt.show()

#Call Outcomes
labels = list(call_states.keys())
sizes = list(call_states.values())
plt.figure(figsize=(8, 8))
plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=['lightgreen', 'lightcoral'])
plt.title("Call Outcomes")
plt.show()
