import subprocess
import shutil

from hop import stream as hop_publisher
from hop.models import VOEvent


def postAlertGCN(filename):
    try:
         cmd = ['/home/ubuntu/Software/miniconda3/bin/comet-sendvo','-f',filename]
         subprocess.check_call(cmd)

    except subprocess.CalledProcessError as e:
        print("Send alert failed")
        #logger.error("comet-sendvo failed")
        #logger.error("File: {}".format(filename))
        raise e

def postAlertHop(filename,channel='amon.test'):
    voevent = VOEvent(filename)
    with hop_publisher.open("kafka://kafka.scimma.org/{}".format(channel),"w") as s:
        s.write(voevent)
