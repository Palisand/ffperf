import sys
import time
from multiprocessing import Pool
from transcoder import Transcoder


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: TODO")

    t = Transcoder(sys.argv[1])
    transsize_args = (720, 16/9)

    start = time.time()
    t.transsize(*transsize_args)
    print("Transsize time, no chunking: {:0.2f}".format(time.time() - start))

    # workers = 5  # TODO: sys.arg --workers -w
    # start = time.time()
    # t.split(workers)
    # with Pool(processes=workers) as pool:
    #     pool.starmap(t.transsize, [(*transsize_args, f) for f in t.chunk_files])
    # t.stitch()
    # print("Transsize time with chunking: {:0.2f}".format(time.time() - start))

    workers = 5
    # Split
    start = time.time()  # TODO: decorate methods
    t.split(workers)
    split_time = time.time() - start
    # Scale
    transsize_time_worst_case = 0
    for chunk_file in t.chunk_files:
        start = time.time()
        t.transsize(*transsize_args, chunk_file)
        transsize_time_worst_case = max(time.time() - start, transsize_time_worst_case)
    # Stitch
    start = time.time()
    t.stitch()
    stitch_time = time.time() - start
    print("Transsize time with chunking: {:0.2f}".format(split_time + transsize_time_worst_case + stitch_time))
