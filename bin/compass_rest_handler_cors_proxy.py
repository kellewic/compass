import json, logging, os, re, requests, sys
import splunk
import splunk.entity

import tempfile

app_name = os.path.splitext(os.path.basename(os.path.realpath(__file__)))[0]
logger = logging.getLogger(app_name)

## app-specific libs
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "lib"))
import certifi, rest_handler
import splunklib.client as client

## acts as a simple proxy that retrieves a URL and removes all style, script, and noscript tags;
## comments; and extraneous whitespace. Also, everything except <body>...</body> content is 
## also removed.
class CompassHandlerCorsProxy_v1(rest_handler.RESTHandler):
    app = "compass"

    def __init__(self, command_line, command_arg):
        super(CompassHandlerCorsProxy_v1, self).__init__(command_line, command_arg, logger)


    ## get URL content and return it
    def get_url(self, url, request_info, is_html=True):
        proxy_settings = None

        try:
            ## get Splunk management port and connect to it
            entity = splunk.entity.getEntity('/server', 'settings', namespace=self.app, sessionKey=request_info.session_key, owner='-')

            service = client.connect(
                owner="nobody",
                app=self.app,
                port=entity['mgmtHostPort'],
                token=request_info.session_key
            )

            ## get proxy settings from kvstore
            collection = service.kvstore['kv_compass_configuration']
            record = collection.data.query(query=str('{"sourcetype":"config:proxy"}'))
            data = json.loads(record[0].get('data'))

            ip = data["ip"]
            if ip is not None and len(ip) > 0:
                ## create proxy location from the proxy parts
                if ip.startswith("http"):
                    connect_str = re.sub('^(https?://)(.*$)', r'\1{}:{}@\2:{}'.format(data["user"], data["password"], data["port"]), ip.strip())
                else:
                    connect_str = "http://{}:{}@{}:{}".format(data["user"], data["password"], ip.strip(),  data["port"])

                proxy_settings = {'http': connect_str, 'https': connect_str}

        except Exception as e:
            return {
                 'payload': 'Warn: exception encountered: ' + str(e)
            }

        ## get remote URL data and return to requestor
        try:
            if proxy_settings is not None:
                response = requests.get(url, timeout=5, verify=certifi.where(), proxies=proxy_settings)
            else:
                response = requests.get(url, timeout=5, verify=certifi.where())

            data = response.text

            if is_html == True:
                ## remove HTML we don't need
                data = re.sub('(?:[\r\n\t]+|\\\\[rnt])', "", data)
                data = re.sub('> +<', "><", data)
                data = re.sub('<style[ >].*?</style>', "", data)
                data = re.sub('<script[ >].*?</script>', "", data)
                data = re.sub('<noscript>.*?</noscript>', "", data)
                data = re.sub('<!--.*?-->', "", data)
                data = re.sub('^.*?<body.*?>', "", data)
                data = re.sub('\s*</body>\s*</html>', "", data)
                data = re.sub('<img.*?>', "", data)

            return {
                'payload': data,
                'status': response.status_code
            }

        except Exception as e:
            return {
                 'payload': 'Warn: exception encountered: ' + str(e)
            }


    def get_data_insider(self, request_info, **kwargs):
        #return self.get_url('https://www.splunk.com/en_us/data-insider.html', request_info, False)
        return self.get_url('https://www.splunk.com/en_us/data-insider/jcr:content/root/responsivegrid/customer_apps_filter.data.html', request_info, False)


    def get_blog_devops(self, request_info, **kwargs):
        return self.get_url('https://www.splunk.com/en_us/blog/devops.html', request_info)


    def get_blog_it(self, request_info, **kwargs):
        return self.get_url('https://www.splunk.com/en_us/blog/it.html', request_info)


    def get_blog_security(self, request_info, **kwargs):
        return self.get_url('https://www.splunk.com/en_us/blog/security.html', request_info)


    def get_blog_platform(self, request_info, **kwargs):
        return self.get_url('https://www.splunk.com/en_us/blog/platform.html', request_info)


    def get_blog_tips_and_tricks(self, request_info, **kwargs):
        return self.get_url('https://www.splunk.com/en_us/blog/tips-and-tricks.html', request_info)


    def get_blog_events(self, request_info, **kwargs):
        return self.get_url('https://www.splunk.com/en_us/blog/conf-splunklive.html', request_info)

