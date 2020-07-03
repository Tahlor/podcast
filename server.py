import http.server
from collections import OrderedDict
from urllib.parse import unquote
from pathlib import Path
import yaml
from easydict import EasyDict as edict

with open("config.yaml") as f:
    c = edict(yaml.load(f.read(), Loader=yaml.SafeLoader))

server_address = ("", c.PORT)
REDIRECTS = OrderedDict({c.URL_DATA_PATH:c.LOCAL_DATA_PATH,
                        c.WAN_PODCAST_URL_PATH:c.WAN_PODCAST_LOCAL_PATH,
                        c.LAN_PODCAST_URL_PATH:c.LAN_PODCAST_LOCAL_PATH,
                        })

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

# Make sure REDIRECTS is sorted
OrderedDict(sorted(REDIRECTS.items(), key=lambda x: len(x[0])))

# taylorarchibald.com/podcasts => "/media/taylor/Flash128/Podcasts"
# taylorarchibald.com/podcasts/data/this_podcast => "/media/taylor/Flash128/Downloads/this_podcasts"

# /home/taylor/public_html

class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        print(path)
        path = unquote(path)
        print(path)
        for prefix in REDIRECTS.keys():
            if self.path.startswith(prefix):
                if self.path == prefix or self.path == prefix + '/':
                    output = REDIRECTS[prefix] + '/index.html'
                    print("Redirect to", output)
                    return output
                else:
                    return REDIRECTS[prefix] + path[len(prefix):]
        return http.server.SimpleHTTPRequestHandler.translate_path(self, path)

if __name__=='__main__':
    httpd = http.server.HTTPServer(server_address, MyRequestHandler)
    print(f"LINK: 127.0.0.1:{c.PORT}")
    httpd.serve_forever()
