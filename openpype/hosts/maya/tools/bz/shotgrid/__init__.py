import shotgun_api3
import os
import importlib
import threading
import zlib
from base64 import urlsafe_b64encode as b64e, urlsafe_b64decode as b64d


def _obscure(data):
    """Encode string with base64

    Args:
        data (:obj:`str`): String to encode

    Returns:
        :obj:`str`: String in Base64
    """
    _data = bytes(data.encode("utf-8"))
    r = b64e(zlib.compress(_data, 9))
    return r

def _unobscure(data):
    """Decode string with base64

    Args:
        data (:obj:`str`): String to dencode

    Returns:
        :obj:`str`: utf-8 string
    """
    _data = zlib.decompress(b64d(data))
    return _data.decode("utf-8")

def getConnection():
    """Create an Shotgrid session.

    This is required as it performs the correct setup for running
    under Cloud Function instances. Note that the API key is stored within the google
    cloud secrets

    Parameters:
        secret (:obj:`str`): Key for the Secret Manager secret.
            Defaults to "ShotGridApiKey".
        username (:obj:`str`): Name of the Script User in Shotgrid to retrieve.
            Defaults to "GoogleCloudAuth".

    Returns:
        session (:obj:`shotgun_api3.shotgun.Shotgun`): Shotgrid session.
    """
    threadId = threading.get_ident()
    _url = _getShotgridServer()
    _key = _getApiKey()
    _user = _getShotgridUser()
    _passLen = len(_key)
    _passSafe = "".join( [_key[x] if x > (_passLen-6) else  '-' for x in range(_passLen)] )

    print('Thread {t} Connecting to Shotgrid site "{url}"'.format(t=threadId,url=_url))
    print('Thread {t} Connecting to Shotgrid with key "{passSafe}"'.format(t=threadId,passSafe=_passSafe))
    session = shotgun_api3.Shotgun(
    "https://blue-zoo.shotgrid.autodesk.com/",
    script_name=_user,
    api_key=_key
    )
    print('Thread {t} Connected to Shotgrid site "{url}"'.format(t=threadId,url=_url))
    session.info()
    return session

def _getApiKey():
    _d = os.environ.get("GRIDKEY",None)
    _k =_unobscure(_d)
    return _k

def _getShotgridServer():
    return os.environ.get("GRIDURL",None)

def _getShotgridUser():
    _d= os.environ.get("GRIDUSER",None)
    _k =_unobscure(_d)
    return _k
