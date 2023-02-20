import subprocess
import shutil

from hop import Stream
from hop.auth import load_auth
from hop.models import VOEvent


def postAlertGCN(filename):
    cmd = ['/home/ubuntu/Software/miniconda3/bin/comet-sendvo','-f',filename]
    subprocess.check_call(cmd)

def postAlertHop(filename,channel='amon.test'):
    voevent = VOEvent.load_file(filename)
    hop_publisher = Stream(auth=load_auth())
    with hop_publisher.open("kafka://kafka.scimma.org/{}".format(channel),"w") as s:
        s.write(voevent)
