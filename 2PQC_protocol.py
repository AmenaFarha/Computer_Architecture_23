from mpi4py import MPI
import sys
import datetime
import os
import threading
from smart_contract import SimpleBank
import test 

filename = "balan.txt"
simple_bank = SimpleBank(filename)
_debug_ = True

def dc_2pqc(received_txn, output_path, comm, rank, size):
    ##################
    # Phase 1: prepare
    ##################
    request = comm.bcast("prepare", root=0)
    num_of_transactions = len(received_txn)

    if _debug_:
        sys.stdout.write("Rank %d receives request: %s\n" % (rank, request))
        result = process_txn(received_txn)
        print(f"Total successful authentications for Rank-{rank}: {result, num_of_transactions}")

    if result == num_of_transactions:
        ready = 1
    else:
        ready = 0

    reply = comm.gather(ready, root=0)
    comm.Barrier()
    if _debug_:
        if 0 == rank:
            sys.stdout.write("Phase 1 done. Reply: %s (rank %d)\n" % (reply, rank))
    
    #################
    # Phase 2: commit
    #################
    ready_to_commit = 0
    if 0 == rank:
        if sum(reply) >= size / 2.0:
            ready_to_commit = 1

    ready_to_commit = comm.bcast(ready_to_commit, root=0)
    if _debug_ and 0 == rank:
        sys.stdout.write("sum(reply) = %d, ready_to_commit = %d\n" % (sum(reply), ready_to_commit))

    local_commit = 0
    if ready_to_commit:
        for i, transaction_id in enumerate(received_txn):
            if i % size == rank:
                account, action, amount_str, to_account = test.get_transaction_info(transaction_id)
                amount = int(amount_str)
                log_file_path = os.path.join(output_path, f"log{rank}.txt")
                with open(log_file_path, "a+") as fp:
                    simple_bank.committ_transaction(account, action, amount, to_account)
                    fp.write(f"log{rank} at {datetime.datetime.now()}: {transaction_id} - {account} {action} {amount} \n")
            local_commit = 1

    done = comm.gather(local_commit, root=0)

    if 0 == rank:
        if sum(done) >= size / 2.0:
            sys.stdout.write("Transaction committed successfully.\n")
        else:
            sys.stdout.write("Transaction failed to commit.\n")

def submit_txn(txn, comm, rank):
    txn = comm.bcast(txn, root=0)
    return txn

def process_chunk(thread_id, current, num_threads, result):
    i = thread_id
    local_result = 0
    try:
        while i < len(current):
            element = current[i]
            account, action, amount_str, to_account = test.get_transaction_info(element)
            amount = int(amount_str)
            if simple_bank.execute_transaction(account, action, amount, to_account) == True:
                local_result += 1
                print(f"Thread-{thread_id}: Authentication successful for transaction {element}.")
            else:
                print(f"Thread-{thread_id}: Authentication failed for transaction {element}.")
            i += num_threads
    except Exception as e:
        print(f"Thread-{thread_id}: Exception occurred - {e}")

    result[thread_id] = local_result


def process_txn(current):
    num_threads = 5
    threads = []
    result = [0] * num_threads

    for i in range(num_threads):
        thread = threading.Thread(target=lambda i=i: process_chunk(i, current, num_threads, result), name=f"Thread-{i}")
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    total_successful_authentications = sum(result)

    return total_successful_authentications

def commit_txn(received_txn, output_path, comm, rank, size):
    dc_2pqc(received_txn, output_path, comm, rank, size)

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
            txn = [int(x) for x in file.read().split(',')]

    received_txn = submit_txn(txn, comm, rank)

    if _debug_:
        sys.stdout.write("received_txn = %s received at rank %d \n" % (received_txn, rank))

    commit_txn(received_txn, output_path, comm, rank, size)
