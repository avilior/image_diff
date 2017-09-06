import asyncio
import logging
import time
import os
import sys
import argparse

import aiohttp
import aiohttp_jinja2
import aiohttp_session
import jinja2
import uvloop
from aiohttp import web

from routes import setup_routes


#logger = logging.getLogger('aiohttp.access')
#logger.setLevel(logging.DEBUG)

async def worker(app):
    try:
        upload_dir = app["upload_dir"]

        while True:

            timenow = time.time()

            for filename in os.listdir(upload_dir):
                info = os.stat(os.path.join(upload_dir, filename))
                delta_time = timenow - info.st_atime
                print(f"{filename} delta: {delta_time}")

            await asyncio.sleep(60)

    except Exception as x:
        print(f"Worker got exception {x}")

async def start_background_tasks(app):
    task = app.loop.create_task(worker(app))
    app['worker'] = task

async def clean_background_tasks(app):
    app['worker'].cancel()
    await app['worker']


def main(host_ip, port, upload_dir):

    print(aiohttp.__version__)

    # make uvloop the default loop in asyncio
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    app = web.Application()

    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(clean_background_tasks)

    # location of static files
    root_path = os.path.dirname(sys.modules['__main__'].__file__)

    # jinja2 template engine setup

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(os.path.join(root_path,'templates')))

    # create if needed an upload dir
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    app["upload_dir"] = upload_dir


    static_dir = os.path.join(root_path, 'static')

    setup_routes(app, upload_dir, static_dir)

    # secret_key must be 32 url-safe base64-encoded bytes
    # fernet_key = fernet.Fernet.generate_key()
    # secret_key = base64.urlsafe_b64decode(fernet_key)
    # aiohttp_session.setup(app, EncryptedCookieStorage(secret_key))
    aiohttp_session.setup(app, aiohttp_session.SimpleCookieStorage())

    web.run_app(app, host=host_ip, port=port)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="KVM Test Station")

    parser.add_argument('--host',   '-i', action='store', dest="host_ip",  default="0.0.0.0", help="ip to listen to",   type=str)
    parser.add_argument('--port',   '-p', action='store', dest="port",     default=80,        help="port to listen on", type=int)
    parser.add_argument('--upload', '-u', action='store', dest="upload_dir", default='/tmp/uploads', help="Location of the upload directory", type=str)

    pargs = parser.parse_args()

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

    sys.exit(main(pargs.host_ip, pargs.port, pargs.upload_dir))





