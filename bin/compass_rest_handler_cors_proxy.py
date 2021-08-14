## system-level libs
import ctypes, logging, os, re, sys
from types import FunctionType, TracebackType

## normalize py2 and py3 urllib to same namespace
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

## libs that come with Splunk
import httplib2

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
        }
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


## Shamelessly plucked from the bowels of Jinja2
##
## In PY2, there's no way to easily change a traceback's tb_next. This functionality
## wasn't added until PY3 where you can dynamically create type.TracebackType
## objects.
def _init_ugly_crap():
    if sys.version_info[0] == 2:
        # figure out size of _Py_ssize_t for Python 2
        if hasattr(ctypes.pythonapi, 'Py_InitModule4_64'):
            _Py_ssize_t = ctypes.c_int64
        else:
            _Py_ssize_t = ctypes.c_int
    else:
        # platform ssize_t on Python 3
        _Py_ssize_t = ctypes.c_ssize_t


    # regular python
    class _PyObject(ctypes.Structure):
        pass
    _PyObject._fields_ = [
        ('ob_refcnt', _Py_ssize_t),
        ('ob_type', ctypes.POINTER(_PyObject))
    ]

    # python with trace
    if hasattr(sys, 'getobjects'):
        class _PyObject(ctypes.Structure):
            pass
        _PyObject._fields_ = [
            ('_ob_next', ctypes.POINTER(_PyObject)),
            ('_ob_prev', ctypes.POINTER(_PyObject)),
            ('ob_refcnt', _Py_ssize_t),
            ('ob_type', ctypes.POINTER(_PyObject))
        ]

    class _Traceback(_PyObject):
        pass
    _Traceback._fields_ = [
        ('tb_next', ctypes.POINTER(_Traceback)),
        ('tb_frame', ctypes.POINTER(_PyObject)),
        ('tb_lasti', ctypes.c_int),
        ('tb_lineno', ctypes.c_int)
    ]

    ## set the tb_next attribute of a traceback object.
    def tb_set_next(tb, next_tb):
        if not (isinstance(tb, TracebackType) and
                (next_tb is None or isinstance(next_tb, TracebackType))):
            raise TypeError('tb_set_next arguments must be traceback objects')

        obj = _Traceback.from_address(id(tb))

        if tb.tb_next is not None:
            old = _Traceback.from_address(id(tb.tb_next))
            old.ob_refcnt -= 1

        if next_tb is None:
            obj.tb_next = ctypes.POINTER(_Traceback)()
        else:
            next_tb = _Traceback.from_address(id(next_tb))
            next_tb.ob_refcnt += 1
            obj.tb_next = ctypes.pointer(next_tb)

    return tb_set_next

## save function reference and remove the above function
tb_set_next = None
try:
    tb_set_next = _init_ugly_crap()
except:
    pass
del _init_ugly_crap


## removes our Attribute error from tracebacks
def excepthook(typ, value, tb):
    ## find the traceback object just before our AttributeError
    curr_tb = tb
    next_tb = curr_tb.tb_next

    while next_tb is not None:
        next_tb = curr_tb.tb_next
        if next_tb is not None and next_tb.tb_next is None: break
        curr_tb = next_tb

    ## if this fails, the original traceback is just forwarded to sys.excepthook
    try:
        ## set second to last traceback object tb_next to None to remove our AttributeError
        if tb_set_next is not None:
            tb_set_next(curr_tb, None)
    except:
        pass

    ## pass to original sys.excepthook
    _excepthook(typ, value, tb)

## save original excepthook from sys module
_excepthook = sys.excepthook
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

