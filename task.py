__author__ = 'andy'
import time

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
        self.waiting_tasks=[]

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

class NewTask(SystemCall):
    def __init__(self, sub_routine):
        self.sub_routine=sub_routine

    def handle(self):
        sub_task = Task(self.sub_routine)
        sub_task.parent_id=self.task.pid
        self.task.value=sub_task.pid
        self.scheduler.schedule(sub_task)

class KillTask(SystemCall):
    def __init__(self, kill_task_id):
        self.kill_task_id=kill_task_id

    def handle(self):
        self.scheduler.kill(self.kill_task_id)

class WaitTask(SystemCall):
    def __init__(self,waited_task_id):
        self.waited_task_id=waited_task_id

    def handle(self):
        self.scheduler.wait(self.task, self.waited_task_id)

@coroutine
def tick():
    yield
    pid=yield GetPid()
    for i in xrange(5):
        yield
        time.sleep(1)
        print "[{}]tick".format(pid), i

@coroutine
def tock():
    yield   #this yield is required, because when we start a coroutine in Task, next() is executed. this "yield" is for the "next()" call to consume.
    pid=yield GetPid()
    for i in xrange(5):
        yield
        print "[{}]tock".format(pid), i

@coroutine
def forker():
    yield
    sub_task_id=yield NewTask(tick())
    print "created a new task, wait it to finish",sub_task_id
    yield WaitTask(sub_task_id)
    print "the waited sub task finished",sub_task_id
    # yield
    # yield KillTask(sub_task_id)
    # print "killed my sub task",sub_task_id

class Scheduler:
    def __init__(self):
        self.ready_tasks=[]
        self.killed_tasks={}
        self.finished_tasks={}
        self.read_wait_tasks=[]
        self.write_wait_tasks=[]
        self.wait_other_tasks={}
        self.task_map={}

    def has_tasks(self):
        return len(self.ready_tasks)>0

    def fetch(self):
        return self.ready_tasks.pop(0)

    def schedule(self, task):
        self.ready_tasks.append(task)
        self.task_map[task.pid]=task

    def wait(self,waiting_task,waited_task_id):
        self.wait_other_tasks[waited_task_id]=self.wait_other_tasks.get(waited_task_id,[])
        self.wait_other_tasks[waited_task_id].append(waiting_task)
        self.ready_tasks.remove(waiting_task)

    def kill(self, task_id):
        task=self.task_map[task_id]
        self.ready_tasks.remove(task)
        self.killed_tasks[task_id]= task
        if task is not None:
            print "[scheduler] remove task ", task_id

    def stop(self,task):
        try:
            self.ready_tasks.remove(task)
        except ValueError as e:
            pass
        print "task [{}] ended".format(task.pid)
        self.finished_tasks[task.pid]=task


    def schedule_waiting_tasks(self,task):
        for waiting_task in self.wait_other_tasks.get(task.pid,[]):
            self.schedule(waiting_task)

    def loop(self):
        while True:
            if not self.has_tasks():
                print "no ready task, sleeping 10s......"
                time.sleep(10)
                continue
            self.run_once()

    def run_once(self):
        try:
            task = self.fetch()
            request = task.resume()
            self.schedule(task)
            if isinstance(request, SystemCall):
                request.task = task
                request.scheduler=self
                request.handle()
        except StopIteration as e:
            self.stop(task)
            self.schedule_waiting_tasks(task)

    def has_waiting_task(self, task):
        pass

if __name__ == "__main__":
    scheduler = Scheduler()
    scheduler.schedule(Task(tick()))
    scheduler.schedule(Task(tock()))
    scheduler.schedule(Task(forker()))
    scheduler.loop()
