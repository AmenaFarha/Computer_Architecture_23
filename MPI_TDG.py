from mpi4py import MPI
import networkx as nx
import subprocess
import test
import time


total_start_time = time.time()
dependency_graph = nx.DiGraph()
fully_independent_transactions = []
dependent_transactions = []
Track = []

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
trans_data = ""

def process_data(data):
    trans_data = ",".join(map(str, data))
    output_file_path = "output.txt"
    with open(output_file_path, "w") as output_file:
        output_file.write(trans_data)

def call_consensus():
    processor_count = 4
    #subprocess.run(["mpiexec", "-n", str(processor_count), "python", "protocol.py", trans_data])
    subprocess.run(["mpiexec", "-n", str(processor_count), "python", "PBFT.py", trans_data])

def calculate_throughput(start_time, end_time, num_transactions):
    total_time = end_time - start_time
    throughput = num_transactions / total_time
    return throughput

if rank == 0:
    for transaction, info in test.transactions.items():
        dependency_graph.add_node(transaction)
        for dependency in info["Dependency"]:
            dependency_graph.add_edge(dependency, transaction)

    if nx.is_directed_acyclic_graph(dependency_graph):
        execution_order = list(nx.topological_sort(dependency_graph))
    else:
        print("The graph contains cycles and cannot be topologically sorted")

    # Independent transactions
    for transaction, info in test.transactions.items():
        if not info["Dependency"]:
            fully_independent_transactions.append(transaction)

    process_data(fully_independent_transactions)
    call_consensus()

    # Dependent transactions
    for transaction, info in test.transactions.items():
        if info["Dependency"]:
            dependent_transactions.append(transaction)

    while dependent_transactions and rank == 0:
        current_group = []
        for transaction in dependent_transactions:
            if set(test.transactions[transaction]["Dependency"]).issubset(fully_independent_transactions):
                current_group.append(transaction)

        process_data(current_group)
        Track.append(current_group)
        fully_independent_transactions.extend(current_group)
        call_consensus()
        dependent_transactions = [t for t in dependent_transactions if t not in current_group]
     #print("Execution order:")
     #for group in Track:
      #print(group)
     #print("Full order:")    
     #print(fully_independent_transactions)
    total_end_time = time.time()
    total_execution_time = total_end_time - total_start_time
    result = f"Total execution time: {total_execution_time} seconds"
    print(result)
    num_transactions_processed = len(fully_independent_transactions)
    throughput = num_transactions_processed / total_execution_time
    print(f"Throughput: {throughput} transactions per second")
