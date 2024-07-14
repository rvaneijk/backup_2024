import time

def timer(start_time=None):
    if start_time is None:
        return time.time()
    else:
        elapsed_time = time.time() - start_time
        return time.strftime('%H:%M:%S', time.gmtime(elapsed_time))