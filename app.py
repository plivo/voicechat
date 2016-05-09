# -*- coding: utf-8 -*-
"""
    Implements ad-hoc conferences using Plivo.

    The MIT License (MIT)
    Copyright (c) 2014 Plivo Inc

"""

import os
from flask import Flask, render_template, request, url_for, make_response, jsonify
import plivo
import config
from utils import get_redis_connection, get_plivo_connection, tinyid

app = Flask(__name__)

@app.route("/")
def index():
    """
    Returns the landing page.
    """
    return render_template('home.html')


@app.route("/create/")
def create():
    """
    Creates a conference room and redirects to the page.
    """
    return render_template('create.html')


@app.route('/response/conf/music/', methods=['GET', 'POST'])
def conf_music():
    """
    Renders the XML to be used for hold music in the conference.
    This XML will be executed by Plivo when there is only 1
    participant in the conference. The URL to this XML is
    passed to the Conference XML under the parameter 'waitSound'.
    """

    plivo_response = plivo.XML.Response()
    plivo_response.addSpeak(config.CONFERENCE_WAIT_ANNOUNCEMENT)
    plivo_response.addPlay(config.HOLD_MUSIC, loop=1)
    response = make_response(render_template('response_template.xml', response=plivo_response))
    response.headers['content-type'] = 'text/xml'
    return response


@app.route('/response/conf/<conference_name>/', methods=['GET', 'POST'])
def conf(conference_name):
    """
    Renders the XML to start a conference based on the conference name
    it receives. It checks if the conference exists in our memory (to make
    sure it hasn't expired).

    This URL is passed as the Answer URL to Plivo. When the call gets
    answered, the call will be put into a conference.
    """

    redis_conn = get_redis_connection()
    room_exists = redis_conn.exists(conference_name)
    plivo_response = plivo.XML.Response()

    if not room_exists:
        plivo_response.addHangup(reason="invalid conference")
        response = make_response(render_template('response_template.xml', response=plivo_response))
        response.headers['content-type'] = 'text/xml'
        return response

    plivo_response.addWait(length=2)
    plivo_response.addSpeak(config.CONFERENCE_ANNOUNCEMENT)
    wait_sound_url = url_for('conf_music', _external=True)

    plivo_response.addConference(conference_name,
                        enterSound="beep:1",
                        exitSound="beep:2",
                        waitSound=wait_sound_url,
                        )
    response = make_response(render_template('response_template.xml', response=plivo_response))
    response.headers['content-type'] = 'text/xml'
    return response


@app.route('/<conference_name>/', methods=['GET'])
def conference(conference_name):
    """
    Returns the HTML page for a particular conference name. The HTML page
    uses the Plivo WebSDK to register to Plivo and make calls.
    """

    if conference_exists(conference_name):
        redis_conn = get_redis_connection()
        endpoint_username = redis_conn.hget(conference_name, 'username')
        endpoint_password = redis_conn.hget(conference_name, 'password')
        inbound_did = redis_conn.hget(conference_name, 'inbound_did')

        conference_url = url_for('conference', _external=True, conference_name=conference_name)

        data = {
                'endpoint_username': endpoint_username,
                'endpoint_password': endpoint_password,
                'inbound_did': inbound_did,
                'conference_name': conference_name,
                'conference_url': conference_url,
                }

        if request.query_string == 'share':
            template_name = 'conference_share.html'
        else:
            template_name = 'conference.html'

        response = make_response(render_template(template_name, response=data))
        return response
    return render_template('404.html')


@app.route('/api/v1/conference/', methods=['POST'])
def conference_api():
    """
    1. Create a conference name
    2. Create an endpoint and store in redis with conference name
    3. Attach the above application to it
    4. Return endpoint username/password to template
    """
    conference_name = 'p%s' % (tinyid(8))
    app_id = create_plivo_application(conference_name)
    endpoint_username = create_plivo_endpoint(conference_name, app_id)
    inbound_did = attach_inbound_did(app_id)
    link_conference(conference_name, endpoint_username, conference_name, inbound_did)

    conference_url = url_for('conference', _external=True, conference_name=conference_name)
    return jsonify(conference_url = conference_url, conference_name = conference_name)


@app.route('/api/v1/conference/<conference_name>/', methods=['POST'])
def conference_call_api(conference_name):
    """
    Parameters -
    to : The number to be called.
    clid : The caller id to be used when making the call.

    1. Make an outbound call
    2. Put the call in the conference
    """
    if not config.ALLOW_OUTBOUND_PSTN:
        return jsonify(success=False, message='Calls are disabled')

    if conference_exists(conference_name):
        to_number = request.form.get('to', None)
        clid = request.form.get('clid', config.PLIVO_CALLER_ID)
        answer_url = url_for('conf', _external=True, conference_name=conference_name)
        plivo_conn = get_plivo_connection()
        status, _ = plivo_conn.make_call({'to': to_number, 'from': clid, 'answer_url': answer_url, 'answer_method': 'POST'})
        if status == 201:
            return jsonify(success=True, message='Call has been queued')
    return jsonify(success=False, message='Call could not be made')


@app.context_processor
def inject_config():
    return dict(outbound_pstn=config.ALLOW_OUTBOUND_PSTN)


def conference_exists(conference_name):
    """
    Checks if the conference has been created and exists in memory

    Returns True/False
    """

    redis_conn = get_redis_connection()
    return redis_conn.exists(conference_name)


def create_plivo_endpoint(conference_name, app_id):
    """
    Create a Plivo endpoint and attach the application
    to it. This endpoint is used to register to Plivo
    using WebRTC or SIP.

    Returns the endpoint username created on Plivo.
    """

    plivo_conn = get_plivo_connection()
    _, response = plivo_conn.create_endpoint({'username': conference_name, 'password': conference_name, 'alias': conference_name, 'app_id': app_id})
    print "Status: %s\nResponse: %s" % (_, response)
    endpoint_username = response['username']
    return endpoint_username


def link_conference(conference_name, endpoint_username, endpoint_password, inbound_did=None):
    """
    Store the conference name in memory along with
    endpoint username and password associated with it.
    """

    redis_conn = get_redis_connection()
    redis_conn.hmset(conference_name, {'username': endpoint_username, 'password': endpoint_password, 'inbound_did': inbound_did})
    if config.EXPIRE_CONFERENCE:
        redis_conn.expire(conference_name, 24*60*60)


def create_plivo_application(conference_name):
    """
    Create a Plivo application and set the answer URL to the conference URL.
    This makes sure that when the call is answered the Conference XML will be
    executed by Plivo.

    Returns the id of the application created on Plivo.
    """

    answer_url = url_for('conf', _external=True, conference_name=conference_name)
    plivo_conn = get_plivo_connection()
    _, response = plivo_conn.create_application({'app_name': conference_name, 'answer_url': answer_url, 'answer_method': 'POST'})
    print "Status: %s\nResponse: %s" % (_, response)
    app_id = response['app_id']
    return app_id


def attach_inbound_did(app_id):
    """
    Rent a Plivo US DID and attach it the conference application.
    """
    if not config.ALLOW_INBOUND_DID:
        return None

    plivo_conn = get_plivo_connection()
    status, response = plivo_conn.get_number_group({'country_iso': 'US'})
    try:
        group_id = response['objects'][0]['group_id']
        status, response = plivo_conn.rent_from_number_group({'group_id': group_id, 'quantity': 1, 'app_id': app_id})
        number_rented = response['numbers'][0]['number']
        return number_rented
    except Exception as e:
        return None


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


