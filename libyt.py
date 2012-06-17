import urllib2, re, time, random, pickle, threading
DATA_CACHE_FILE = "/tmp/libyt_data_cache.pickle"
cache_lock = threading.Lock()
annotation_cache = {}
description_cache = {}
try:
  data = pickle.load(open(DATA_CACHE_FILE, "rb"))
  annotation_cache = data['annotation_cache']
  description_cache = data['description_cache']
except (IOError, AttributeError, KeyError, EOFError):
  pass

def api_cool_off(limit_reached):
  if limit_reached:
    time.sleep(30 + random.randint(0, 30))
  else:
    time.sleep(0.5 + random.randint(0, 2))

def save_cache():
  cache_lock.acquire()
  try:
    pickle.dump({'annotation_cache': annotation_cache,
                 'description_cache': description_cache},
                 open(DATA_CACHE_FILE, "wb"))
  except IOError:
    pass
  cache_lock.release()

def check_cache(cache, key):
  cache_lock.acquire()
  data = cache.get(key, False)
  cache_lock.release()
  return data

def add_to_cache(cache, key, value):
  cache_lock.acquire()
  cache[key] = value
  cache_lock.release()
  save_cache()

def retrieve_annotations(video_id):
  annotation_url = "http://www.youtube.com/annotations_iv/read2?feat=TCS&video_id=%s"
  data = check_cache(annotation_cache, video_id)
  if data:
    return data

  try:
    data = urllib2.urlopen(annotation_url % video_id).read()
    add_to_cache(annotation_cache, video_id, data)
  except urllib2.HTTPError as e:
    return (e.code, "too_many_recent_calls" in e.read())
  api_cool_off(False)
  return data

def retrieve_video(video_id):
  description_url = "http://gdata.youtube.com/feeds/api/videos/%s"
  data = check_cache(description_cache, video_id)
  if data:
    return data

  try:
    data = urllib2.urlopen(description_url % video_id).read()
    add_to_cache(description_cache, video_id, data)
  except urllib2.HTTPError as e:
    return (e.code, "too_many_recent_calls" in e.read())
  api_cool_off(False)
  return data

def retrieve_user_videos(username):
  userfeed_url = "http://gdata.youtube.com/feeds/api/users/%s/uploads"
  try:
    data = urllib2.urlopen(userfeed_url % username).read()
  except urllib2.HTTPError as e:
    return (e.code, "too_many_recent_calls" in e.read())
  api_cool_off(False)
  return data

def find_all_videos(data):
  id_regex = '/watch.v=([0-9a-zA-Z_-]+)[&\'"]'
  return set(re.findall(id_regex, data))

def find_all_users(data):
  user_regex = 'www.youtube.com/user/([0-9a-zA-Z]+)[/?\'"]'
  return set([x.lower() for x in re.findall(user_regex, data)])

def process_video(data):
  views_regex = " viewCount='(\d+)'/>"
  title_regex = "<title type='text'>(.*)</title>"
  author_regex = "<name>(.*)</name>"
  description_regex = "description type='plain'>(.*)</media:description"

  output = {}
  output['view_count'] = int(re.search(views_regex, data).group(1))
  output['title'] = re.search(title_regex, data).group(1)
  output['author'] = re.search(author_regex, data).group(1)
  try:
    output['description'] = re.search(description_regex, data, re.DOTALL).group(1)
  except AttributeError:
    output['description'] = ''
  return output
