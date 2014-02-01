import os

# Plivo Auth ID and Auth Token
PLIVO_AUTH_ID = ''
PLIVO_AUTH_TOKEN = ''

# Plivo Caller ID
PLIVO_CALLER_ID = ''

# Wait announcement music when there is only 1 participant in the conference
HOLD_MUSIC = 'https://s3.amazonaws.com/plivocloud/music.mp3'

# Wait announcement message when there is only 1 participant in the conference
CONFERENCE_WAIT_ANNOUNCEMENT = "You are currently alone in the conference. Please wait. Thank you."

# Announcement message before entering the conference
CONFERENCE_ANNOUNCEMENT = 'Welcome to the conferencing bridge.'

# Enable this to have the ability to add people to a conference by calling a
# PSTN number. 
ALLOW_OUTBOUND_PSTN = False

# Enable this to attach an incoming number to every ad-hoc conference created.
# Be careful with this flag. Turning this to True will result in renting a new number
# with every conference created from this app.
ALLOW_INBOUND_DID = False

# Expire a conference in 24 hours when this flag is enabled.
EXPIRE_CONFERENCE = not ALLOW_INBOUND_DID

# Redis config options
REDIS_URL = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
REDIS_MAX_CONNECTIONS = 10
REDIS_TIMEOUT = 5  # in seconds - in the worst case, will add this much to response time
