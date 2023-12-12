from mpi4py import MPI
import os
import datetime
from smart_contract import SimpleBank
import test
import threading
import time

filename = "balan.txt"
output_path = "./output"
simple_bank = SimpleBank(filename)
_debug_ = True

def pre_prepare_phase(comm, rank, size, received_txn):
    comm.barrier()
    message_count = 0
    for dest in range(size):
        if dest != rank:
            message = f"Received Request"
            comm.send(message, dest=dest)

    for source in range(size):
        if source != rank:
            try:
                message = comm.recv(source=source, status=MPI.Status())
                message_count += 1
            except MPI.Exception as e:
                pass

    comm.barrier()

    if message_count >= (size - 1):
        return True
    else:
        return False

def prepare_phase(received_txn, comm, rank, size):
    comm.barrier()
    count = 0
    if process_txn(received_txn):
        for dest in range(size):
            if dest != rank:
                message = f"prepare"
                comm.send(message, dest=dest)

        for source in range(size):
            if source != rank:
                try:
                    message = comm.recv(source=source, status=MPI.Status())
                    count += 1
                except MPI.Exception as e:
                    pass
        comm.barrier()

        if count >= (size - 1):
            return True
        else:
            return False

def commit_phase(received_txn, comm, rank, size):
    comm.barrier()
    ready_commit = 0
    c_message = 0

    for r in range(0, size):
        if rank == r:
            log_entry = f"log{rank} at {datetime.datetime.now()}: {', '.join(map(str, received_txn))}\n"
            with open(os.path.join(output_path, f"log{rank}.txt"), "a+") as fp:
                fp.write(log_entry)
            ready_commit = 1

    if ready_commit == 1:
        for dest in range(size):
            if dest != rank:
                message = f"Ready Commit"
                comm.send(message, dest=dest)

        for source in range(size):
            if source != rank:
                try:
                    message = comm.recv(source=source, status=MPI.Status())
                    c_message += 1
                except MPI.Exception as e:
                    pass

        comm.barrier()

        if c_message >= (size - 1):
            return True
        else:
            return False

def pbft_consensus(comm, rank, size, received_txn):
    if rank == 0:
        if process_txn(received_txn):
            comm.bcast("Pre-prepare", root=0)
        else:
            print("Leader decided not to proceed with Pre-prepare phase.")
            return
    else:
        comm.bcast(None, root=0)

def submit_txn(txn, comm, rank):
    txn = comm.bcast(txn, root=0)
    return txn

def process_chunk(thread_id, chunk):
    local_result = 0
    try:
        for element in chunk:
            account, action, amount_str, to_account = test.get_transaction_info(element)
            amount = int(amount_str)

            # Perform your logic with the transaction data
            if simple_bank.execute_transaction(account, action, amount, to_account):
                local_result += 1
                #print(f"Thread-{thread_id}: Authentication successful for transaction {element}.")
            else:
                pass
                #print(f"Thread-{thread_id}: Authentication failed for transaction {element}.")
    except Exception as e:
        print(f"Thread-{thread_id}: Exception occurred - {e}")

    return local_result

def process_txn(current):
    num_threads = 5
    threads = []
    results = []

    # Ensure there are transactions to process
    if not current:
        return 0

    # Split transactions into chunks
    chunk_size = max(1, len(current) // num_threads)
    chunks = [current[i:i + chunk_size] for i in range(0, len(current), chunk_size)]

    for i in range(min(num_threads, len(chunks))):  # Ensure i is within the valid range
        thread = threading.Thread(target=lambda i=i: results.append(process_chunk(i, chunks[i])), name=f"Thread-{i}")
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Retrieve results from the threads
    total_successful_authentications = sum(results)
    if(total_successful_authentications== len(current)):
        return True
    else:
       return False

if __name__ == '__main__':
    comm = MPI.COMM_WORLD
    size = MPI.COMM_WORLD.Get_size()
    rank = MPI.COMM_WORLD.Get_rank()
    name = MPI.Get_processor_name()

    output_path = "./output"
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    txn = []
    file_path = "output.txt"
    if rank == 0:
        with open(file_path, "r") as file:
            txn = [int(x) for x in file.read().split(',') if x.strip()]

    received_txn = submit_txn(txn, comm, rank)
    pbft_consensus(comm, rank, size, received_txn)
    
    if pre_prepare_phase(comm, rank, size, received_txn):
        print(f"Rank {rank} done with pre_prepare_phase")
        
    comm.barrier()

    if prepare_phase(received_txn, comm, rank, size):
        print(f"Rank {rank} done with prepare_phase")
        
    comm.barrier()

    if commit_phase(received_txn, comm, rank, size):
        print(f"Rank {rank} done with commit_phase")
    comm.barrier()
