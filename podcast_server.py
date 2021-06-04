import http.server
from collections import OrderedDict
from urllib.parse import unquote
from pathlib import Path
import yaml
from easydict import EasyDict as edict
import os
import signal
import subprocess
from time import sleep


def kill_process_by_port(port):
    pid_command = f"lsof -i :{port}" + "| awk 'NR==2{print $2}'"
    print(pid_command)
    kill(pid_command)

def kill_process(names=["podcast_server.py"], port=False):
    # PID = "ps aux | grep podcast |  grep 'server.py' | awk '{print $2}'"
    pid_command = "ps aux "
    for name in names:
        pid_command += f"| grep {name}"
    pid_command += "| grep -v grep | awk '{print $2}'"
    print(pid_command)
    kill(pid_command)

def kill(command):
    """ Enter a Linux command that will return the PID to kill
    """
    process = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE, 
    stderr=subprocess.PIPE)
    my_pid, err = process.communicate()
    if my_pid:
        try:
            print("PID", my_pid)
            my_pid = int(my_pid.strip())
            print(my_pid)
            os.kill(my_pid, signal.SIGTERM) #or signal.SIGKILL 
            sleep(5)
        except:
            print(f"Could not terminate {my_pid}")


with open("config.yaml") as f:
    c = edict(yaml.load(f.read(), Loader=yaml.SafeLoader))

server_address = ("", c.PORT)
REDIRECTS = OrderedDict({c.URL_DATA_PATH:c.LOCAL_DATA_PATH,
                         c.URL_DATA_PATH2:c.LOCAL_DATA_PATH,
                        c.WAN_PODCAST_URL_PATH:c.WAN_PODCAST_LOCAL_PATH,
                        c.LAN_PODCAST_URL_PATH:c.LAN_PODCAST_LOCAL_PATH,
                        })

kill_process_by_port(c.PORT)

# REDIRECTS = OrderedDict({r"/podcasts/data":f"/home/{USER}/public_html_data/podcasts",
#                         r"/podcasts":f"/home/{USER}/public_html/podcasts",
#                         r"/podcastsl":f"/home/{USER}/public_html/podcastsl",
#                         })

for path in REDIRECTS.values():
    Path(path).mkdir(exist_ok=True, parents=True)

# TO RUN restricted port:
# use "sudo bash"
# then open environment
# then run server

# TO DO:
    # generate podcast index
    # make sure XML files are using the right address location...

# Make sure REDIRECTS is sorted longest to shortest, check for the longest matching path first
REDIRECTS = OrderedDict(sorted(REDIRECTS.items(), key=lambda x: -len(x[0])))

# taylorarchibald.com/podcasts => "/media/taylor/Flash128/Podcasts"
# taylorarchibald.com/podcasts/data/this_podcast => "/media/taylor/Flash128/Downloads/this_podcasts"

# /home/taylor/public_html

class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        print("Raw path", path)
        path = unquote(path)
        print("Translated", path)
        path = path.replace("podcastl.xml", "podcast.xml") # no longer hosting podcastl
        for prefix in REDIRECTS.keys():
            if self.path.startswith(prefix):
                if self.path == prefix or self.path == prefix + '/':
                    output = REDIRECTS[prefix] + '/index.html'
                else:
                    output = REDIRECTS[prefix] + path[len(prefix):]
                print("Redirect to ", output)
                return output
        return http.server.SimpleHTTPRequestHandler.translate_path(self, path)

if __name__=='__main__':
    httpd = http.server.ThreadingHTTPServer(server_address, MyRequestHandler)
    print(f"LINK: 127.0.0.1:{c.PORT}")
    print(REDIRECTS)
    print(c.PORT)
    httpd.serve_forever()
