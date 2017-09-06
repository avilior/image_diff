import logging
import os
import sys
import time
import uuid

from aiohttp import web
from aiohttp_session import get_session

from bokeh.layouts import gridplot
from bokeh.plotting import figure
from bokeh.embed import components

import image_ops

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

import aiohttp_jinja2

ROOT_PATH = os.path.dirname(sys.modules['__main__'].__file__)

async def index(request):

    session = await get_session(request)
    session['last_access'] = time.time()
    logging.debug(F"{session.identity}:{session}")

    return web.Response(text="This is AIO-HTTP\n")


async def upload_image_handler(request):

    session = await get_session(request)
    session['last_access'] = time.time()
    logging.debug(F"{session.identity}:{session}")

    if "session_data" not in session:
        session["session_data"] = {}

    reader = await request.multipart()

    # /!\ Don't forget to validate your inputs /!\

    part = await reader.next()

    if part.name == "left_image":
        session['session_data']["left_image"] = None
    elif part.name =="right_image":
        session['session_data']["right_image"] = None
    else:
        return web.Response(status=500, text=F"Internal error. part.name {part.name} expect right_image or left_image")


    filename = part.filename

    # check that filename is not empty
    if filename is None or len(filename) == 0:
        return web.Response(status=400, text="Missing Filename.")

    # users upload directory
    upload_dir_path = os.path.join(request.app["upload_dir"],session['uid'])

    # check if there is a directory for the user session in uploads
    if not os.path.exists(upload_dir_path):
        os.makedirs(upload_dir_path)

    # You cannot rely on Content-Length if transfer is chunked.
    size = 0

    with open(os.path.join(upload_dir_path, filename), 'wb') as f:
        while True:
            chunk = await part.read_chunk()  # 8192 bytes by default.
            if not chunk:
                break
            size += len(chunk)
            f.write(chunk)

    if part.name == "left_image":
        session['session_data']["left_image"] = {"filename":filename}
    elif part.name =="right_image":
        session['session_data']["right_image"] = {"filename": filename}

    session.changed()

    return web.HTTPFound('/diff')


def render_sideby_side2(left_image_name,right_image_name, upload_resource, uid):
    left_url = None
    right_url = None
    if left_image_name:
        left_url = str(upload_resource.url_for(filename=uid + "/" + left_image_name))
    if right_image_name:
        right_url = str(upload_resource.url_for(filename=uid+"/"+right_image_name))


    # compute the max width and height

    # crete two plots linked to each other
    p1 = figure(x_range=(0, 4727), y_range=(0, 2950), title=left_image_name,responsive=True)
    p2 = figure(plot_width=p1.plot_width, plot_height=p1.plot_height, x_range=p1.x_range, y_range=p1.y_range, title=right_image_name, responsive=True)

    p1.image_url([left_url],
                 x=[0], y=[2950], w=[4727], h=[2950])
    p2.image_url([right_url],
                 x=[0], y=[2950], w=[4727], h=[2950])


    p = gridplot([[p1, p2]])

    scripts, div = components(p)
    return 0, {"script":scripts, "div":div}  # return script, div



def render_sideby_side(uid, upload_resource, session_data):

    left_image_name = None
    if "left_image" in session_data and "filename" in session_data["left_image"]:
        left_image_name = session_data["left_image"]["filename"]
    right_image_name = None
    if "right_image" in session_data and "filename" in session_data["right_image"]:
        right_image_name = session_data["right_image"]["filename"]

    # todo need to get the dimensions of the image
    left_url = None
    right_url = None
    if left_image_name:
        left_url = str(upload_resource.url_for(filename=uid + "/" + left_image_name))
    if right_image_name:
        right_url = str(upload_resource.url_for(filename=uid+"/"+right_image_name))


    # compute the max width and height

    # crete two plots linked to each other
    p1 = figure(x_range=(0, 4727), y_range=(0, 2950), title=left_image_name,responsive=True)
    p2 = figure(plot_width=p1.plot_width, plot_height=p1.plot_height, x_range=p1.x_range, y_range=p1.y_range, title=right_image_name, responsive=True)

    p1.image_url([left_url],
                 x=[0], y=[2950], w=[4727], h=[2950])
    p2.image_url([right_url],
                 x=[0], y=[2950], w=[4727], h=[2950])


    p = gridplot([[p1, p2]])

    scripts, div = components(p)
    return 0, {"script":scripts, "div":div}  # return script, div


async def image_diff(request):
    session = await get_session(request)

    if session.new:
        # create an identity for this user.
        uid = uuid.uuid4()
        session["uid"] = str(uid)
    else:
        # TODO if there are files associated with the session, check to make sure they exist
        # Need this when we have bugs. alternatively invalidate the cookie and cause a new one to be generated
        if "uid" not in session:
            uid = uuid.uuid4()
            session["uid"] = str(uid)


    session['last_access'] = time.time()
    logging.debug(F"{session.identity}:{session}")

    if "session_data" not in session:
        session["session_data"] = {}


    # users upload directory
    upload_dir_path = os.path.join(request.app["upload_dir"], session['uid'])

    session_data = session["session_data"]

    # validate the session
    # if the upload directory does not exists then remove the left and right image from session data
    if not os.path.exists(upload_dir_path):
        if "left_image" in session_data:
            del session_data["left_image"]
            session.changed()
        if "right_image" in session_data:
            del session_data["right_image"]
            session.changed()
    else:
        # check to make sure that if there are files in the session then they physically exist
        if "left_image" in session_data and "filename" in session_data["left_image"]:
            if not os.path.isfile(os.path.join(upload_dir_path,session_data["left_image"]["filename"])):
                del session_data["left_image"]
                session.changed()
        if "right_image" in session_data and "filename" in session_data["right_image"]:
            if not os.path.isfile(os.path.join(upload_dir_path,session_data["right_image"]["filename"])):
                del session_data["right_image"]
                session.changed()


    template_context = {}
    uid = session['uid']

    upload_resource = request.app.router['uploads']

    code, script_and_div = render_sideby_side(uid, upload_resource, session["session_data"])
    if code == 0:
        template_context["image_display"] = script_and_div


    template_context["data"] = session["session_data"]
    response = aiohttp_jinja2.render_template('base_html.jinja2',request,template_context)
    return response

async def do_diff_computation(request):
    """
    Given a left and a right image
    compute:
    get size of the images
    compute shift
    compute ssim
    compute mse
    detect differences
    """
    session = await get_session(request)

    # users upload directory
    upload_dir_path = os.path.join(request.app["upload_dir"], session['uid'])

    template_context = {}
    template_context["data"] = session["session_data"]
    upload_resource = request.app.router['uploads']

    # get both files - and if both dont exists then we are done
    try:
        # take care of the left and right images
        code, script_and_div = render_sideby_side(session['uid'], upload_resource, session["session_data"])
        if code !=  0:
            # cant render plots for side by side image
            return web.HTTPFound('/diff') # go back to diff

        # add the side by side images plots to the context
        template_context["image_display"] = script_and_div

        # ####################################################
        # now let compute the differences between those images

        left_image = os.path.join(upload_dir_path,session['session_data']["left_image"]["filename"] )
        right_image = os.path.join(upload_dir_path, session['session_data']["right_image"]["filename"])

        # TODO: this can take a long time so we should allocate the work to a seperate thread
        code, result = image_ops.workon_images(left_image, right_image, upload_dir_path)
        if code == 0:
            # TODO add the result to the data session and render the page

            """
            {   "ssim_score":
                "diff":    <diff image name> optional 
                "thresh"   <thresh image name> optional
                "marked_l" <marked left image name> optional
                "marked_r"  <marked right iamge name> optional
                "histogram" <dual histogram plot {"div","script"} for left image and right image>
                "diff_histogram" {"div","script"} <single histogram plot 
            } 
            """
            # create a diffresult
            diff_result = {}
            template_context["diff_result"] = diff_result

            # populate it
            if "histogram" in result:
                diff_result["histogram"] = result["histogram"]
            if "diff_histogram" in result:
                diff_result["diff_histogram"] = result["diff_histogram"]


            if "marked_l" in result and "marked_r" in result:
                code, script_and_div = render_sideby_side2(result["marked_l"],result["marked_r"], upload_resource, session['uid'])
                if code == 0:
                    diff_result["diff_image_display"] = script_and_div


            response = aiohttp_jinja2.render_template('base_html.jinja2', request, template_context)
            return response

        else:
            # we had an error
            return web.HTTPFound('/diff')

    except KeyError:
        logging.debug("Both files don't exists - we shouldnt get here")
        return web.HTTPFound('/diff')

    return web.HTTPFound('/diff')


