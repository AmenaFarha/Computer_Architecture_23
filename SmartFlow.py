from mpi4py import MPI
import sys
import datetime
import os
import threading
from smart_contract import SimpleBank
import test_input

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
                account, action, amount_str, to_account = test_input.get_transaction_info(transaction_id)
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

def process_chunk(node_id, transactions, num_nodes, results):
    index = node_id
    local_result = 0
    try:
        # Process every num_nodes-th transaction starting at index specific to this node_id
        while index < len(transactions):
            transaction = transactions[index]
            account, action, amount_str, to_account = test_input.get_transaction_info(transaction)
            amount = int(amount_str)
            # Attempt to execute the transaction
            if simple_bank.execute_transaction(account, action, amount, to_account):
                local_result += 1
                #print(f"Node-{node_id}: Authentication successful for transaction {transaction}.")
            else:
                print(f"Node-{node_id}: Authentication failed for transaction {transaction}.")
            index += num_nodes
    except Exception as e:
        print(f"Node-{node_id}: Exception occurred - {e}")

    results[node_id] = local_result
    
def process_txn(current):
    num_nodes = 5
    results = [0] * num_nodes  # Results array to accumulate results from each virtual node

    # Simulating each node's processing
    for i in range(num_nodes):
        process_chunk(i, current, num_nodes, results)

    total_successful_authentications = sum(results)
    #print(f"Total successful authentications: {total_successful_authentications}")

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

    commit_txn(received_txn, output_path, comm, rank, size)
