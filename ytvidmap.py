#!/usr/bin/env python
# Map the links between youtube videos
import threading
import Queue
import sys
import time

from libgraph import *
from libyt import *

class State:
  def __init__(self):
    self.video_queue = Queue.Queue()
    self.video_map = {}
    self.video_list = {}
    self.lock = threading.Lock()

max_nodes = 1000
time_limit = 60 * 60 # 1 hour

def video_link(name):
  return "http://youtu.be/%s" % name

def video_size(name):
  try:
    maximum = max([state.video_list[x]['view_count'] for x in state.video_list])
    size = int(30 * (float(state.video_list[name]['view_count']) / maximum))
    return str(max(8, size))
  except KeyError:
    return "8"

def video_name(name):
  try:
    n = state.video_list[name]['title']
  except KeyError:
    n = name
  return n

class VideoSpiderTask(threading.Thread):
  def __init__(self, state):
    threading.Thread.__init__(self)
    self.state = state

  def run(self):
    try:
      while True:
        print "Count: %d | Queue: %d" % (len(self.state.video_list), self.state.video_queue.qsize())
        video_id = self.state.video_queue.get(True, 5)
        if video_id in self.state.video_list:
            continue
        video_data = retrieve_annotations(video_id)
        if video_data[0] == 403 or video_data[0] == 404:
          if video_data[1]:
            self.state.video_queue.put(video_id)
            api_cool_off(True)
          continue
        video_desc = retrieve_video(video_id)
        if video_desc[0] == 403 or video_desc[0] == 404:
          if video_desc[1]:
            self.state.video_queue.put(video_id)
            api_cool_off(True)
          continue
        print "Processing: %s" % video_id
        self.state.lock.acquire()
        self.state.video_list[video_id] = process_video(video_desc)

        videos = find_all_videos(video_data)
        for v in videos:
          if v not in self.state.video_list and v not in self.state.video_queue.queue:
            if len(self.state.video_map) < max_nodes and time.time() - start_time < time_limit:
              self.state.video_queue.put(v)
          if v not in self.state.video_map:
            self.state.video_map[v] = set()
          self.state.video_map[video_id].add(v)
        
        self.state.lock.release()

    except Queue.Empty:
      print "Thread empty"

state = State()
start_time = time.time()

for x in sys.argv[2:]:
  state.video_queue.put(x)
  state.video_map[x] = set()

tasks = [VideoSpiderTask(state) for i in xrange(0, 4)]
for t in tasks:
  t.start()
  time.sleep(1)
for i, t in enumerate(tasks):
  t.join()  # In reality we'll block for one thread and then shortly finish up
  print "Thread: %d finished" % i

print "...FINISHED..."

G = generate_graph(state.video_map, video_name, video_link, video_size, sys.argv[2:])
write_graph(G, sys.argv[1])

print "Victorious!"
