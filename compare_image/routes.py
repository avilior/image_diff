import os
import sys

from views import index, image_diff, upload_image_handler, do_diff_computation


def setup_routes(app, uploads_dir, static_dir):

    # static path '/' will serve static files from the root path but will interfere with index
    app.router.add_static('/static/', path=static_dir, name='static')
    app.router.add_static('/uploads/', path=uploads_dir, name='uploads')

    app.router.add_get('/', index)
    app.router.add_get('/diff', image_diff)
    app.router.add_get('/do_diff_computation',do_diff_computation)

    app.router.add_post('/upload/image',upload_image_handler)
