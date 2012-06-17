#!/usr/bin/env python
# Map the links between youtube users
import threading
import Queue
import sys
import time

from libgraph import *
from libyt import *

class State:
  def __init__(self):
    self.video_queue = Queue.Queue()
    self.user_queue = Queue.Queue()
    self.user_map = {}
    self.user_list = {}
    self.video_list = {}
    self.lock = threading.Lock()

max_nodes = 12
time_limit = 60 * 60 # 1 hour

def user_link(name):
  return "http://www.youtube.com/user/%s" % name

def user_size(name):
  maximum_connections = max([len(x) for x in state.user_map])
  size = int(30 * (float(len(state.user_map[name])) / maximum_connections))
  return str(max(8, size))

def user_name(name):
  return name

class VideoSpiderTask(threading.Thread):
  def __init__(self, state):
    threading.Thread.__init__(self)
    self.state = state

  def run(self):
    try:
      while True:
        video_id, username = self.state.video_queue.get(True, 5)
        if video_id in self.state.video_list:
            continue
        video_data = retrieve_annotations(video_id)
        if video_data[0] == 403 or video_data[0] == 404:
          if video_data[1]:
            self.state.video_queue.put(video_id)
            api_cool_off(True)
          continue
        print "Processing: %s" % video_id
        self.state.lock.acquire()
        self.state.video_list[video_id] = True

        users = find_all_users(video_data)
        for u in users:
          if u not in self.state.user_list and u not in self.state.user_queue.queue:
            if len(self.state.user_map) < max_nodes and time.time() - start_time < time_limit:
              self.state.user_queue.put(u)
          if u not in self.state.user_map:
            self.state.user_map[u] = set()
          self.state.user_map[username].add(u)
        
        self.state.lock.release()

    except Queue.Empty:
      if self.state.user_queue.qsize() > 0:
        self.run()
      else:
        print "User Thread empty"

class UserSpiderTask(threading.Thread):
  def __init__(self, state):
    threading.Thread.__init__(self)
    self.state = state

  def run(self):
    try:
      while True:
        print "Users: %d\t Videos: %d" % (len(self.state.user_list), len(self.state.video_list))
        print "UQueue: %d\t VQueue: %d" % (self.state.user_queue.qsize(), self.state.video_queue.qsize())
        username = self.state.user_queue.get(True, 5)
        if username in self.state.user_list:
            continue
        video_data = retrieve_user_videos(username)
        if video_data[0] == 403 or video_data[0] == 404:
          if video_data[1]:
            self.state.video_queue.put(username)
            api_cool_off(True)
          continue
        print "Processing: %s" % username

        self.state.lock.acquire()
        if username not in self.state.user_list:
          self.state.user_list[username] = set()
        video_list = find_all_videos(video_data)
        self.state.user_list[username] = len(video_list)
        for v in video_list:
          if v not in self.state.video_list and (v, username) not in self.state.video_queue.queue:
            self.state.video_queue.put((v, username))
        
        self.state.lock.release()
            
    except Queue.Empty:
      if self.state.video_queue.qsize() > 0:
        self.run()
      else:
        print "User Thread empty"

state = State()
start_time = time.time()

for x in sys.argv[2:]:
  state.user_queue.put(x.lower())
  state.user_map[x] = set()

tasks = [UserSpiderTask(state) for i in xrange(0, 4)] + [VideoSpiderTask(state) for i in xrange(0, 4)]
for t in tasks:
  t.start()
  time.sleep(1)
for i, t in enumerate(tasks):
  t.join()  # In reality we'll block for one thread and then shortly finish up
  print "Thread: %d finished" % i

print "...FINISHED..."

G = generate_graph(state.user_map, user_name, user_link, user_size, sys.argv[2:])
write_graph(G, sys.argv[1])

print "Victorious!"
