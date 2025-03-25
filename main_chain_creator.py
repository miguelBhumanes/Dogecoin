##############################################################
### MAIN CHAIN CREATOR 
##############################################################

# Note for myself: download "cursor" IDE

'''
This code reads the blk files and generates a list of the blocks that are part of the main chain.

Note: the main chain is the sequence of blocks that is valid. Some blk files correspond to blocks that are
not part of the main chain. Rev files reverse the transactions in these blk files. 
'''

# STEP 1: IMPORT PACKAGES AND CREATE BASIC ASSETS

# Import packages
import struct
import hashlib
from pathlib import Path

# Identifier code with which all blocks of the blockchain begin
MAGIC = b'\xc0\xc0\xc0\xc0'

# Metadata of the block corresponds to the first 80 bytes of info
BLOCK_HEADER_SIZE = 80

# SHA 256 Hashing function 
def double_sha256(b):
    return hashlib.sha256(hashlib.sha256(b).digest()).digest()

# Function to compute the amount of work (1to1 relationship with bits info extracted from blocks)
def compute_work(bits):
    exponent = bits >> 24
    mantissa = bits & 0xffffff
    target = mantissa * (1 << (8 * (exponent - 3)))
    if target == 0:
        return 0
    return (1 << 256) // (target + 1)


# STEP 2: FUNCTION TO CREATE DICTIONARY: BLOCK -> {PREVIOUS BLOCK, AMOUNT OF WORK}

def read_blocks_from_dir(path):

    # Initialize dictionary for blocks (the output you want to return)
    blocks = {}

    # Path object is a directory. Glob is a generator. A list that only loads one item at a time 
    # (to avoid loading so much data on memory). It sorts the list. (glob is like a list in essence)
    # Just that when it is executed it doesnt load all elements, just one at a time. 
    blk_files = sorted(Path(path).glob("blk*.dat"))

    # Track
    counter = 0

    # Loop through files
    ### ATTENTION. REMOVE LIMIT
    for file in blk_files[0:10]:

        # Each blk file has several blocks
        with open(file, "rb") as f:
            while True:

                # First check: the magic coincides with the mainnet magic. Else, transaction for sure is
                # not of the mainnet. 
                magic = f.read(4)
                if magic != MAGIC:
                    break

                # Check the blk file has at least 4 bytes. Else, its just useless dirty data
                # Caution: every time you do f.read you are reading the next 4 bytes. 
                size_bytes = f.read(4)
                if len(size_bytes) < 4:
                    break

                # Parsing the block size (from bytes to an actual integer number)
                block_size = struct.unpack("<I", size_bytes)[0]

                # Knowing the block size, read the next block size bytes. 
                # This is because in each blk file there are several blocks. 
                # So you are storing all the block info in block_data
                block_data = f.read(block_size)

                # The block header should be at least block header size long
                # Then, select the first block_header_size bytes, which is the header
                if len(block_data) < BLOCK_HEADER_SIZE:
                    break
                header = block_data[:BLOCK_HEADER_SIZE]

                # From here, just parse useful info from the header
                block_hash = double_sha256(header)[::-1].hex()
                prev_hash = header[4:36][::-1].hex()
                bits = struct.unpack("<I", header[72:76])[0]
                work = compute_work(bits)

                # Write on the dictionary
                blocks[block_hash] = {
                    "prev": prev_hash,
                    "work": work,
                }
        
        # Tracking
        counter += 1
        print(f'processed blk file {counter}')

    # Return the dictionary
    counter = 0
    return blocks



# STEP 3: SELECTS THE HEAVIEST CHAIN OUT OF ALL THE POSSIBLE ONES
# (Which is the one the blockchain nodes automatically select)
def build_chain(blocks):

    # Dictionaries for the tips (all the possible previous blocks for a given block)
    # and the cumulative work at each node (work at that node and all preceding blockchain)
    tips = {}
    cumulative = {}

    # blocks.items is the iterator of key value pairs for the dictionary created with function in Step 2
    # bhash is the block identifier (hash) and the data was previous block hash and amount of work
    for bhash, data in blocks.items():
        prev = data["prev"]
        work = data["work"]

        # Add the block to the dictionary storing cumulative work for each node
        if prev in cumulative:
            cumulative[bhash] = cumulative[prev] + work
        else:
            cumulative[bhash] = work
        tips[bhash] = prev

    # Choose to go back with the tip that has the most cumulative work
    best_tip = max(cumulative, key=cumulative.get)
    chain = []
    while best_tip in tips:
        chain.append(best_tip)
        best_tip = tips[best_tip]

    # Reverse chain so that first element is genesis block
    chain.reverse()
    return chain



# STEP 4: EXECUTE

# Path
blocks_path = r"D:\DogecoinData\blocks"

# Creating blocks dict
blocks = read_blocks_from_dir(blocks_path)

# Obtaining main net
main_chain = build_chain(blocks)


'''
DESCRIPTION OF OUTPUT:

The list 'main_chain' is the output. The first element is the genesis block of the mainnet. 
Then, every element is the blocks of the mainnet in order. The last element is the last block that
the blockchain had recorded at the time we downloaded it. 
'''