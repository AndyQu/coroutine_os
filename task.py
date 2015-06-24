__author__ = 'andy'

def coroutine(func):
    def start(*args,**kwargs):
        cr = func(*args,**kwargs)
        cr.next()
        return cr
    return start

class Task:
    id = 1

    def __init__(self, routine):
        self.coroutine = routine
        self.value = None
        self.pid = Task.id
        print "new task",self.pid
        Task.id += 1

    def start(self):
        self.coroutine.send(self.value)

    def suspend(self):
        print "suspend has no effect here, because only the task can suspend itself via yield. Task:",self.pid

    def resume(self):
        return self.coroutine.send(self.value)

class SystemCall:
    def __init__(self):
        pass

    def handle(self):
        pass

class GetPid(SystemCall):
    def __init__(self):
        pass

    def handle(self):
        self.task.value = self.task.pid

@coroutine
def tick():
    yield
    for i in xrange(10):
        yield
        print "tick", i
    print "My pid is {}, I am done".format((yield GetPid()))

@coroutine
def tock():
    yield   #this yield is required, because when we start a coroutine in Task, next() is executed. this "yield" is for the "next()" call to consume.
    print "My pid is {}, I am about to run".format((yield GetPid()))
    for i in xrange(10):
        yield
        print "tock", i

import time

if __name__ == "__main__":
    task_list = [
        Task(tick()),
        Task(tock())
    ]
    while True:
        if len(task_list) <= 0:
            print "no ready task, sleeping 10s......"
            time.sleep(10)
            continue
        try:
            task = task_list.pop(0)
            request = task.resume()
            if isinstance(request, GetPid):
                request.task = task
                request.handle()
            task_list.append(task)
        except StopIteration as e:
            print "task ended", task.pid
