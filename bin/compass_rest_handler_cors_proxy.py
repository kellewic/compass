import ctypes, logging, os, re, sys, traceback
from http.client import HTTPSConnection
from urllib.parse import urlparse
from types import FunctionType, TracebackType

app_name = os.path.splitext(os.path.basename(os.path.realpath(__file__)))[0]
logger = logging.getLogger(app_name)

## app-specific libs
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "lib"))
import rest_handler

## acts as a simple proxy that retrieves a URL and removes all style, script, and noscript tags;
## comments; and extraneous whitespace. Also, everything except <body>...</body> content is 
## also removed.
class CompassHandlerCorsProxy_v1(rest_handler.RESTHandler):
    ## only create one instance
    _instance = None

    ## name of most recent non-existent attribute accessed - used in exception formatting
    _last_attr = None

    ## Config relating names to URLs. In JS code, names are used rather than URLs.
    ## Internally, we expect a method named get_<<name>>(request_info, **kwargs) to be
    ## called from rest_handler.RESTHandler.handle() method.
    url_maps = {
        "data_insider": {
            "url": "https://www.splunk.com/en_us/data-insider.html"
        },
        "blog_devops": {
            "url": "https://www.splunk.com/en_us/blog/devops.html"
        },
        "blog_it": {
            "url": "https://www.splunk.com/en_us/blog/it.html"
        },
        "blog_security": {
            "url": "https://www.splunk.com/en_us/blog/security.html"
        },
        "blog_platform": {
            "url": "https://www.splunk.com/en_us/blog/platform.html"
        },
        "blog_tips_and_tricks": {
            "url": "https://www.splunk.com/en_us/blog/tips-and-tricks.html"
        },
        "blog_events": {
            "url": "https://www.splunk.com/en_us/blog/conf-splunklive.html"
        },
    }


    def __new__(cls, *args, **kwargs):
        if cls._instance is not None:
            return cls._instance

        ## iterate config and create class methods for each
        for name, attrs in cls.url_maps.items():
            ## class method string to turn into a function
            func_str = "@classmethod\ndef {}(cls, request_info, **kwargs): return cls.get_url('{}')".format(name, attrs["url"])

            ## add dynamically created function to the class
            setattr(cls, name, FunctionType(
                ## compile class method string to function
                compile(func_str, "<string>", "exec").co_consts[0],
                ## don't need globals; pass empty dict
                {}
            ))

        cls._instance = rest_handler.RESTHandler.__new__(cls)
        return cls._instance


    def __init__(self, command_line, command_arg):
        super(CompassHandlerCorsProxy_v1, self).__init__(command_line, command_arg, logger)


    ## get URL content and return it
    @staticmethod
    def get_url(url):
        parsed_url = urlparse(url, allow_fragments=True)
        conn = HTTPSConnection(parsed_url.netloc, port=443, timeout=5)
        conn.request("GET", parsed_url.path)
        response = conn.getresponse()
        data = response.read()
        data = data.decode("utf-8", "replace")

        data = re.sub('(?:[\r\n\t]+|\\\\[rnt])', "", data)
        data = re.sub('> +<', "><", data)
        data = re.sub('<style[ >].*?</style>', "", data)
        data = re.sub('<script[ >].*?</script>', "", data)
        data = re.sub('<noscript>.*?</noscript>', "", data)
        data = re.sub('<!--.*?-->', "", data)
        data = re.sub('^.*?<body.*?>', "", data)
        data = re.sub('\s*</body>\s*</html>', "", data)
        data = re.sub('<img.*?>', "", data)

        response.close()
        conn.close()

        return {
            'payload': data,
            'status': response.status
        }

    ## fallback for weirdness. Used when a dynamic class method should exist but doesn't
    @classmethod
    def not_implemented(cls, *args, **kwargs):
        ## format like a normal Python AttributeError
        raise AttributeError("'{}' object has no attribute '{}'".format(cls.__name__, cls._last_attr))


    ## since our REST handler calls methods as <<method>>_<<endpoint>>(RequestInfo, **kwargs), we
    ## map that call to our internal, dynamic class methods created in __new__. This only occurs
    ## once per call as we set the alias via setattr()
    def __getattr__(self, name):
        cls = self.__class__
        cls._last_attr = name
        internal_name = name.replace("get_", "")

        if name == internal_name:
            ## happens if the rest_handler was called with a non-GET request or
            ## if we were called outside the rest_handler improperly.
            internal_func = getattr(self, 'not_implemented')
        else:
            internal_func = getattr(self, internal_name, 'not_implemented')

        setattr(self, name, internal_func)
        return internal_func


## removes our not_implemented() Attribute error from tracebacks
def excepthook(typ, value, tb):
    ## find the traceback object just before our AttributeError
    tb_chain = []
    curr_tb = tb

    while curr_tb.tb_next is not None:
        tb_chain.append(curr_tb)
        curr_tb = curr_tb.tb_next

    new_tb = None

    for curr_tb in reversed(tb_chain):
        new_tb = TracebackType(new_tb, curr_tb.tb_frame, curr_tb.tb_lasti, curr_tb.tb_lineno)

    ## send exception to user and exit
    traceback.print_exception(typ, value, new_tb)
    sys.exit()

## inject our excepthook to sys module
sys.excepthook = excepthook


## NOTE: FOR TESTING
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
## NOTE: END TESTING

