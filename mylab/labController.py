import time

from flask import Blueprint, url_for, render_template, jsonify, session, current_app, request

from mylab import weblab
from mylab.labHardware import program_device, is_light_on, is_interruptor_on, press_pulsador, get_microcontroller_state, switch_light, switch_interruptor,change_slider, slider_value, loadGit, LIGHTS

from weblablib import requires_active, requires_login, weblab_user, logout

from werkzeug.utils import secure_filename

import os


main_blueprint = Blueprint('main', __name__)

@weblab.initial_url
def initial_url():
    """
    Where do we send the user when a new user comes?
    """
    return url_for('main.index')



@main_blueprint.route('/')
@requires_login
def index():
    # This method generates a random identifier and stores it in Flask's session object
    # For any request coming from the client, we'll check it. This way, we avoid
    # CSRF attacks (check https://en.wikipedia.org/wiki/Cross-site_request_forgery )
    session['csrf'] = weblab.create_token()

    return render_template("index.html")

@main_blueprint.route('/status')
@requires_active
def status():
    "Return the status of the board"
    lights = {}
    microcontroller = {}
    interruptors = {}
    sliders = {}

    for light in range(LIGHTS):
        lights['light-{}'.format(light + 1)] = is_light_on(light)

    for interruptor in range(8):
        interruptors['interruptor-{}'.format(interruptor + 1)] = is_interruptor_on(interruptor)

    for slider in range(2):
        sliders['slider-{}'.format(slider + 1)] = slider_value(slider)

    microcontroller = get_microcontroller_state()

    task = weblab.get_task(program_device)
    if task:
        current_app.logger.debug("Current programming task status: %s (error: %s; result: %s)", task.status, task.error, task.result)

    return jsonify(error=False, lights=lights, interruptors=interruptors, sliders=sliders, microcontroller=microcontroller, time_left=weblab_user.time_left)

@main_blueprint.route('/logout', methods=['POST'])
@requires_login
def logout_view():
    if not _check_csrf():
        return jsonify(error=True, message="Invalid JSON")

    if weblab_user.active:
        logout()

    return jsonify(error=False)

@main_blueprint.route('/button/<int:number>', methods=['POST'])
@requires_active
def light(number):
    # light number is 1..10
    internal_number = number - 1

    # Check that number is valid
    if internal_number not in range(LIGHTS):
        return jsonify(error=True, message="Invalid light number")

    if not _check_csrf():
        return jsonify(error=True, message="Invalid CSRF")

    # Turn on light
    switch_light(internal_number, request.values.get('state', 'false') == 'true')
    return status()

@main_blueprint.route('/interruptor/<int:number>', methods=['POST'])
@requires_active
def interruptor(number):
    # light number is 1..10
    internal_number = number - 1  

    # Check that number is valid
    if internal_number not in range(8):
        return jsonify(error=True, message="Invalid light number")

    if not _check_csrf():
        return jsonify(error=True, message="Invalid CSRF")

    # Turn on light
    switch_interruptor(internal_number, request.values.get('state', 'false') == 'true')
    return status()

@main_blueprint.route('/slider/<int:number>', methods=['POST'])
@requires_active
def slider(number):
    # light number is 1..10
    internal_number = number - 1  

    # Check that number is valid
    if internal_number not in range(2):
        return jsonify(error=True, message="Invalid light number")

    if not _check_csrf():
        return jsonify(error=True, message="Invalid CSRF")

    # Turn on light
    change_slider(internal_number, request.values.get('value'))
    return status()

@main_blueprint.route('/pulsador/<int:number>', methods=['POST'])
@requires_active
def pulsador(number):
    # light number is 1..10
    internal_number = number - 1  

    # Check that number is valid
    if internal_number not in range(6):
        return jsonify(error=True, message="Invalid light number")

    if not _check_csrf():
        return jsonify(error=True, message="Invalid CSRF")

    # Turn on light
    press_pulsador(internal_number)

    return status()

@main_blueprint.route('/microcontroller', methods=['POST'])
@requires_active
def microcontroller():
    if not _check_csrf():
        return jsonify(error=True, message="Invalid CSRF")

    code = request.values.get('code') or "code"

    # If there are running tasks, don't let them send the program
    if len(weblab.running_tasks):
        return jsonify(error=True, message="Other tasks being run")

    task = program_device.delay(code)

    # Playing with a task:
    current_app.logger.debug("New task! {}".format(task.task_id))
    current_app.logger.debug(" - Name: {}".format(task.name))
    current_app.logger.debug(" - Status: {}".format(task.status))

    # Result and error will be None unless status is 'done' or 'failed'
    current_app.logger.debug(" - Result: {}".format(task.result))
    current_app.logger.debug(" - Error: {}".format(task.error))

    return status()

@main_blueprint.route('/upload', methods=['POST'])
@requires_active
def upload():
    if 'file' not in request.files:
        return jsonify(error=True, message="No file part")

    file = request.files['file']

    if file.filename == '':
        return jsonify(error=True, message="No selected file")

    if not allowed_file(file.filename):
        return jsonify(error=True, message="Invalid file type. Only .git files are allowed")

    filename = secure_filename(file.filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    process_git_file(file_path)

    loadGit(file)

    return jsonify(error=False, message="File uploaded successfully")



#######################################################
#
#   Other functions
#

def _check_csrf():
    expected = session.get('csrf')
    if not expected:
        current_app.logger.warning("No CSRF in session. Calling method before loading index?")
        return False

    obtained = request.values.get('csrf')
    if not obtained:
        # No CSRF passed.
        current_app.logger.warning("Missing CSRF in provided data")
        return False

    return expected == obtained

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'bit'

def process_git_file(file_path):
    print(f"Archivo .git procesado: {file_path}")
    pass