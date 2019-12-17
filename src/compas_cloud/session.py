import time
import os
import sys
from multiprocessing import Process, Queue, current_process
from contextlib import contextmanager
from capturer import CaptureOutput
import traceback
import logging
from capture import captured
from threading import Thread


TASK_FINISHED = "____FINISHED____"


class Pool():
    def __init__(self, log_path=None):
        self.counter = 0
        self.tasks = {}
        self.waiting = Queue()
        self.messages = Queue()
        self.create_workers()
        self.log_path = log_path

    def add_task(self, func, *args, **kwargs):
        task = {"func": func, "args": args, "kwargs": kwargs, "status": "waiting"}
        _id = len(self.tasks)
        if self.log_path is not None:
            task["log_path"] = os.path.join(self.log_path, "task-{}.log".format(_id))
        else:
            task["log_path"] = None
        self.tasks[_id] = task
        self.waiting.put(_id)

    def create_workers(self):

        def worker(waiting, messages, tasks):
            pid = os.getpid()
            messages.put(("messege", "worker {} started".format(pid)))
            while not waiting.empty():
                task_id = waiting.get()
                task = tasks[task_id]
                messages.put(("task_running", task_id))
                with captured(task_id, log_path=task["log_path"]) as c:
                    def output_reader(proc):
                        if proc.log_path:
                            messages.put(("massage", "task-{}: streaming log to {}".format(proc.name, proc.log_path)))
                            return
                        out = proc.outfile
                        lastpos = 0
                        while True:
                            if out.tell() != lastpos:
                                out.seek(lastpos)
                                line = out.read()
                                if line[-16:] == TASK_FINISHED:
                                    break
                                messages.put(("task_log", "task-{}: {}".format(proc.name, line)))
                                lastpos = out.tell()
                            time.sleep(0.05)

                    t = Thread(target=output_reader, args=(c,))
                    t.start()

                    try:
                        task["func"](*task["args"], **task["kwargs"])
                        print(TASK_FINISHED, end="")
                        t.join()
                        messages.put(("task_finished", task_id))
                        c.finished = True
                    except Exception:
                        traceback.print_exc()
                        print(TASK_FINISHED, end="")
                        t.join()
                        messages.put(("task_failed", task_id))

            messages.put(("messege", "worker {} terminated".format(pid)))

        self.workers = [Process(target=worker, args=(self.waiting, self.messages, self.tasks)) for i in range(4)]

    def process_message(self):

        msg_type, content = self.messages.get()

        if msg_type == "task_running":
            key = content
            self.tasks[key]["status"] = "running"
            print("task id:", key, "started")
            print(self.status)

        elif msg_type == "task_finished":
            key = content
            self.tasks[key]["status"] = "finished"
            print("task id:", key, "finished")

        elif msg_type == "task_failed":
            key = content
            self.tasks[key]["status"] = "failed"
            print("task id:", key, "failed")
        elif msg_type == "task_log":
            print(content, end="")
        else:
            print(content)


    def start(self):

        print("starting with tasks:", self.status)
        for worker in self.workers:
            worker.start()

    def listen(self):
        while not self.all_finished() or not self.messages.empty():
            self.process_message()
        print("all tasks finished: ", self.status)

    @property
    def status(self):
        s = {"waiting": 0, "running": 0, "failed": 0, "finished": 0, "total": len(self.tasks)}
        for k in self.tasks:
            for key in s:
                if self.tasks[k]['status'] == key:
                    s[key] += 1
        return s

    def all_finished(self):
        return self.status["finished"] + self.status["failed"] == self.status["total"]

    def terminate(self):
        for w in self.workers:
            w.terminate()

    def summary(self):
        pass


if __name__ == '__main__':

    def func(a):
        for i in range(a):
            time.sleep(1)
            print('sleeped ', i, 's')

        raise RuntimeError('error example')
        return a

    p = Pool(log_path="temp")
    # p = Pool()

    p.add_task(func, 1)
    p.add_task(func, 2)
    p.add_task(func, 3)
    p.add_task(func, 4)
    p.add_task(func, 5)


    p.start()
    p.listen()
