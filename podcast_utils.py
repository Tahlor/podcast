import datetime
import time
from email import utils
import pytz

timezone = pytz.timezone("America/Denver")

def get_date(offset=0):
    """ Offset in years
    """
    #nowdt = datetime.datetime.now()
    nowdt = datetime.datetime(2021,1,6)
    d_aware = timezone.localize(nowdt)
    return d_aware - datetime.timedelta(days=int(365.25*offset))
    # utils.format_datetime(


import logging
logger = logging.getLogger("root")

def error_wrapper(g):
    while True:
        try:
            yield next(g)
        except StopIteration:
            logger.warning("Stop Iteration")
            input()
            break
        except OSError as e:
            # log error
            continue

