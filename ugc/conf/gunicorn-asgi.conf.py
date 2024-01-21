bind = "0.0.0.0:8000"
workers = 2

worker_class = "uvicorn.workers.UvicornWorker"

max_requests = 1000
max_requests_jitter = 2
timeout = 30

worker_tmp_dir = "/dev/shm"  # /dev/shm uses the shm filesystem—shared memory, and in-memory filesystem

accesslog = "-"  # log to stdout
