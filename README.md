# [VoiceChat](http://voicechatapi.com/)
VoiceChat is a set of APIs to create ad-hoc conferences to be used in the browser. Its built using the [Plivo WebSDK](https://plivo.com/docs/sdk/web/) and APIs.

## Step 1: Get a Plivo account

Note down the Auth ID and the Auth Token


## Step 2: Create a conference room

    $ curl -XPOST -u "<auth_id>:<auth_token>" http://voicechatapi.com/api/v2/conference/
    {
        "conference_name": "prwdbpwrw", 
        "conference_url": "http://secure-sands-4424.herokuapp.com/prwdbpwrw/"
    }

## Step 3: Call out people into the conference

    $ curl -XPOST -u "<auth_id>:<auth_token>" -d "to={1415123####}&clid={1415123####}" http://voicechatapi.com/api/v2/conference/<conference_name>/
    {
        "success": True,
        "message": "Call has been queued"
    }


# Looking to self-host?

## Clone this repo

    $ git clone git@github.com:plivo/voicechat.git

## Configure
Create a Plivo account if you haven't already

## Deploying to Heroku
Create a Heroku account if you haven't.

    $ cd voicechat
    $ heroku create {app_name} -s cedar
    $ git push heroku master
    $ heroku addons:add redistogo:nano --app {app_name}
    $ heroku ps:scale web=1

Add Plivo Auth ID and Auth Token to env from the [dashboard](https://plivo.com/dashboard/).

    $ heroku config:set PLIVO_AUTH_ID={PLIVO_AUTH_ID}
    $ heroku config:set PLIVO_AUTH_TOKEN={PLIVO_AUTH_TOKEN}

## Test your application
Go to {app_name}.herokuapp.com


# API Docs

## Create a conference name

    POST /api/v1/conference/

### Example

    $ curl -XPOST http://voicechatapi.com/api/v1/conference/
    {
        "conference_name": "p12ygdwt1", 
        "conference_url": "http://voicechatapi.com/p12ygdwt1/"
    }

## Call a mobile & landline phone number (PSTN) into the bridge

    POST /api/v1/conference/<conference_name>/

### Parameters

    to - The phone number to be called.
    clid - The caller id which will be used. (The phone number to be shown in the recipient's phone.)


### Example

    $ curl -XPOST -d "to={1415123####}&clid={1415123####}" http://voicechatapi.com/api/v1/conference/<conference_name>/
    {
        "success": True,
        "message": "Call has been queued"
    }

[![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/plivo/voicechat/trend.png)](https://bitdeli.com/free "Bitdeli Badge")
