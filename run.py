import sys
import time
from multiprocessing import Pool
from transcoder import Transcoder


def transsize(transcoder, height, aspect_ratio):
    start = time.time()
    transcoder.transsize(height, aspect_ratio)
    print("Transsize time, no chunking: {:0.2f}".format(time.time() - start))


def chunked_transsize(transcoder, height, aspect_ratio, workers):
    # Split
    start = time.time()  # TODO: decorate methods with timer
    transcoder.split(workers)
    split_time = time.time() - start
    # Scale
    transsize_time_worst_case = 0
    for chunk_file in t.chunk_files:
        start = time.time()
        transcoder.transsize(height, aspect_ratio, chunk_file)
        transsize_time_worst_case = max(time.time() - start, transsize_time_worst_case)
    # Stitch
    start = time.time()
    transcoder.stitch()
    stitch_time = time.time() - start
    print("Transsize time with chunking: {:0.2f}".format(split_time + transsize_time_worst_case + stitch_time))


def parallel_chunked_transsize(transcoder, height, aspect_ratio, workers):
    """
    Will not work as a method for estimating distributed transcode time.
    """
    start = time.time()
    transcoder.split(workers)
    with Pool(processes=workers) as pool:
        pool.starmap(transcoder.transsize, [(height, aspect_ratio, f) for f in t.chunk_files])
    transcoder.stitch()
    print("Transsize time with chunking: {:0.2f}".format(time.time() - start))


def seek_split(transcoder, workers):
    start = time.time()
    chunk_time = transcoder.get_chunk_time(workers)
    for i in range(workers):
        transcoder.seek_split(i, chunk_time)
    print("Split time: {:0.2f}".format(time.time() - start))


def parallel_seek_split(transcoder, workers):
    """
    Offers a marginal increase in speed.
    """
    start = time.time()
    chunk_time = transcoder.get_chunk_time(workers)
    with Pool(processes=workers) as pool:
        pool.starmap(transcoder.seek_split, [(i, chunk_time) for i in range(workers)])
    print("Split time: {:0.2f}".format(time.time() - start))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: TODO")
        sys.exit(1)

    t = Transcoder(sys.argv[1])
    transsize_args = (720, 16 / 9)

    workers = 5  # TODO: sys.arg --workers -w

    # transsize(t, *transsize_args)

    # chunked_transsize(t, *transsize_args, workers)

    # seek_split(t, workers)
    # parallel_seek_split(t, workers)
