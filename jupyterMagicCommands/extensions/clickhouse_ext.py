import argparse
import requests
import pandas as pd
from io import StringIO
from IPython.display import Pretty

class FormatHandlerFactory:

    handlers = {}
    
    @classmethod
    def create(cls, format, *args, **kwargs):
        return cls.handlers.get(format, "JSON")(*args, **kwargs)
    
    @classmethod
    def register(cls, handlerClass):
        cls.handlers[handlerClass.format] = handlerClass
        return handlerClass

class FormatHandler:
    format = ""
    
    def printHeader(self, r, args):
        for k, v in r.headers.items():
            print("{}: {}".format(k, v))
    
    def handle(self, r, args):
        pass

@FormatHandlerFactory.register
class JSONFormatHandler(FormatHandler):
    format = "JSON"
    
    def printTime(self, r): 
        print(f"Elapsed: {r.json()['statistics']['elapsed']} sec, read {r.json()['statistics']['rows_read']} rows, {r.json()['statistics']['bytes_read']} bytes.")
    
    def handle(self, r, args):
        ret = ""
        if args.verbose: self.printHeader(r, args)
        if r.ok:
            self.printTime(r)
            ret = pd.DataFrame(r.json()['data'])     
        else:
            print("Bad Request: {}".format(r.text))
        return ret
    

@FormatHandlerFactory.register
class VerticalFormatHandler(FormatHandler):
    format = "Vertical"
        
    def handle(self, r, args):
        ret = ""
        if args.verbose: self.printHeader(r, args)
        if r.ok:
            ret = Pretty(r.text)
        else:
            print("Bad Request: {}".format(r.text))
        return ret
        
        
@FormatHandlerFactory.register
class PrettyFormatHandler(VerticalFormatHandler):
    format = "Pretty"
    
    
@FormatHandlerFactory.register
class PrettyCompactFormatHandler(VerticalFormatHandler):
    format = "PrettyCompact"
    

def ck(line, cell):
    parser = getParser()
    inArgs = line.strip().split(' ')
    if inArgs == ['']:
        inArgs = []
    args = parser.parse_args(inArgs)
    url = args.url

    sio = StringIO(cell)
    query = sio.read()

    ret = queryClickHousePlayGround(query, url, args)
    return ret

def queryClickHousePlayGround(query: str, url: str, args: argparse.Namespace):
    data = {
        'query':  query,
        'user': 'play',
        'password': '',
        'default_format': args.format
    }
    try: 
        r = requests.get(url, params=data)
    except Exception as e:
        print(e)
    
    handler = FormatHandlerFactory.create(args.format)
    ret = handler.handle(r, args)
    if args.output is not None:
        if args.format not in {"JSON"}:
            ret.to_csv(args.outputFile, index=False)
        else:
            print("Only format JSON supports output!")
    return ret

def load_ipython_extension(ipython):
    ipython.register_magic_function(ck, 'cell')

def parseDataset(dataset: str) -> str:
    defaultUrl = "https://play.clickhouse.com:443"
    return {"ontime": "https://gh-api.clickhouse.com/play"}.get(dataset, defaultUrl)

def getParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', dest='url', type=parseDataset, default=parseDataset('default'))
    parser.add_argument('--verbose', action='store_true', default=False)
    parser.add_argument('--format', type=str, default='PrettyCompact', choices=list(FormatHandlerFactory.handlers.keys()))
    parser.add_argument('--output', type=str)
    return parser
