import consul
import logging
import getpass
from blessings import Terminal
import sys
import atexit

session_id = None
client = None

logger = 'requests.packages.urllib3.connectionpool'
logging.getLogger(logger).setLevel(logging.WARNING)


def init(config):
    global client
    client = consul.Consul(**config)


def lock():
    if not client:
        return
    global session_id
    if session_id:
        print 'what are you doing we are already locked jerk'
        sys.exit(1)

    session_id = client.session.create(name=getpass.getuser(), lock_delay=0)
    aquired_lock = client.kv.put('terraform', None, acquire=session_id)
    if not aquired_lock:
        lockers_session = client.kv.get('terraform')[1]['Session']
        user = client.session.info(lockers_session)[1]['Name']
        message = '{t.red}{}{t.normal} is using Terraform'
        print message.format(user, t=Terminal())
        sys.exit(1)


def unlock():
    if not client:
        return

    global session_id
    if session_id:
        client.session.destroy(session_id)
        session_id = None

atexit.register(unlock)
