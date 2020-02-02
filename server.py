import http.server
from collections import OrderedDict
from urllib.parse import unquote
from pathlib import Path
PORT = 58372
server_address = ("", 58372)
USER = "pi"
REDIRECTS = OrderedDict({r"/podcasts/data":f"/home/{USER}/public_html_data/podcasts",
                        r"/podcasts":f"/home/{USER}/public_html/podcasts",
                        })

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
    print(f"LINK: 127.0.0.1:{PORT}")
    httpd.serve_forever()
