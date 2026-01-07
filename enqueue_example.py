import os
from redis import Redis
from rq import Queue
from worker import example_task

VERSION = os.getenv("WORKER_VERSION", "dev")

if __name__ == "__main__":
    print(f"Enqueuer version: {VERSION}")
    conn = Redis.from_url("redis://localhost:6379/0")
    q = Queue('default', connection=conn)
    job = q.enqueue(example_task, "Hello from RQ script!")
    print(f"Enqueued job: {job.id}")
