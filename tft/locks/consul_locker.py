import consul
import logging
import getpass
from blessings import Terminal
import sys
import os
import atexit

global session_id
session_id = None

logger = 'requests.packages.urllib3.connectionpool'
logging.getLogger(logger).setLevel(logging.WARNING)

if 'CONSUL_HTTP_ADDR' in os.environ:
    c = consul.Consul()


def lock():
    if not c:
        return
    global session_id
    if session_id:
        print 'what are you doing we are already locked jerk'
        sys.exit(1)
    else:
        session_id = c.session.create(name=getpass.getuser(), lock_delay=0)
        aquired_lock = c.kv.put('terraform', None, acquire=session_id)
        if not aquired_lock:
            lockers_session = c.kv.get('terraform')[1]['Session']
            user = c.session.info(lockers_session)[1]['Name']
            message = '{t.red}{}{t.normal} is using Terraform'
            print message.format(user, t=Terminal())
            sys.exit(1)


def unlock():
    if not c:
        return
    if session_id:
        c.session.destroy(session_id)

atexit.register(unlock)
