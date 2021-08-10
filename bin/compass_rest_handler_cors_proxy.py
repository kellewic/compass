
## System-level libs
import logging
import os
import re
import sys

try:
    import urllib.parse as urlparse
except:
    import urlparse


## NOTE: FOR TESTING
if os.environ.get("HFNILUWALBLQYTOKLGO") is not None:
    if sys.version_info.major >= 3:
        sys.path.append("{}/lib/python3.7/site-packages".format(os.environ.get("SPLUNK_HOME", "/opt/splunk")))
    else:
        sys.path.append("{}/lib/python2.7/site-packages".format(os.environ.get("SPLUNK_HOME", "/opt/splunk")))
## NOTE: END TESTING

## Splunk environment libs
#import splunk
#import splunk.entity
#import splunk.Intersplunk
import httplib2

app_name = os.path.splitext(os.path.basename(os.path.realpath(__file__)))[0]
#app_name="compass_cors_proxy"
logger = logging.getLogger(app_name)

## App-specific libs
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "lib"))
import rest_handler
#import splunklib.client as client

class CompassHandlerCorsProxy_v1(rest_handler.RESTHandler):
    def __init__(self, command_line, command_arg):
        super(CompassHandlerCorsProxy_v1, self).__init__(command_line, command_arg, logger)

        self.data = ""
        self.status = 200


    def _get_url(self, url):
        parsed_url = urlparse.urlparse(url, allow_fragments=True)
        conn = httplib2.HTTPSConnectionWithTimeout(parsed_url.netloc, port=443, timeout=5)
        conn.request("GET", parsed_url.path)
        response = conn.getresponse()
        data = str(response.read())

        data = re.sub('(?:[\r\n\t]+|\\\\[rnt])', "", data)
        data = re.sub('> +<', "><", data)
        data = re.sub('<style[ >].*?</style>', "", data)
        data = re.sub('<script[ >].*?</script>', "", data)
        data = re.sub('<noscript>.*?</noscript>', "", data)
        data = re.sub('<!--.*?-->', "", data)
        data = re.sub('^.*?<body.*?>', "", data)
        data = re.sub('\s*</body>\s*</html>', "", data)
        
        self.data = data
        self.status = response.status

        response.close()
        conn.close()


    def get_data_insider(self, request_info, **kwargs):
        url = "https://www.splunk.com/en_us/data-insider.html"
        self._get_url(url)

        cors_url = request_info.raw_args.get("server", {}).get("rest_uri", "*")
        cors_url = re.sub(':\d+$', "", cors_url)

        return {
            'payload': self.data,
            'status': self.status
        }


if __name__ == "__main__":
    ri = rest_handler.RequestInfo("admin", "SESSION_KEY", "GET", "/path", "", {
	"output_mode": "xml",
	"output_mode_explicit": False,
	"server": {
	    "rest_uri": "https://127.0.0.1:8089",
	    "hostname": "dev",
	    "servername": "dev",
	    "guid": "6954F00C-A372-4B5E-A868-4EFAD67431B2"
	},
	"restmap": {
	    "name": "script:compass_rest_handler_cors_proxy",
	    "conf": {
		"handler": "compass_rest_handler_cors_proxy.CompassHandlerCorsProxy_v1",
		"match": "/compass/v1/cors_proxy",
		"output_modes": "json",
		"passHttpCookies": "true",
		"passHttpHeaders": "true",
		"passPayload": "true",
		"python.version": "python3",
		"requireAuthentication": "true",
		"script": "compass_rest_handler_cors_proxy.py",
		"scripttype": "persist"
	    }
	}
    })

    proxy = CompassHandlerCorsProxy_v1("cmd_line", "cmd_args")
    response = proxy.get_data_insider(ri)
    print(response)

