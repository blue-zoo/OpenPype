"""Check if any scenes are open by the user."""

import logging
import os
import arrow
import requests
from getpass import getuser

import maya.api.OpenMaya as om2
import maya.cmds as mc

from .. import URL


logger = logging.getLogger(__name__)


def getSceneOpenData(scene):
    """Get data on the open scenes."""
    logger.info('Checking for open scenes...')
    scene = scene.strip()

    if not scene:
        logger.info('Scene does not exist.')
        return

    if os.environ.get('BZ_OPEN_SCENE_CHECK', '')[:1].lower() in ('0', 'f'):
        logger.info('Check is disabled.')
        return

    if scene[:2].lower() == 'c:':
        logger.info('Scene is local.')
        return

    url = URL + '/reports/maya/open-scenes?tz=utc&sort=date&scene=' + scene
    logger.debug('Sending request to {!r}...'.format(url))
    try:
        response = requests.get(url, timeout=2)

    except requests.exceptions.ConnectTimeout:
        logger.error('Request timeout.')
        return

    except requests.exceptions.ConnectionError:
        logger.error('Connection error.')
        return

    except requests.exceptions.ReadTimeout:
        logger.error('Read timeout.')
        return

    except Exception as e:
        logger.exception(e)
        return

    if not response:
        logger.error('Request failed.')
        return

    data = response.json()['data']
    if not data:
        logger.info('No open scenes found.')
        return

    for open_scene in data:
        open_scene['date'] = arrow.get(open_scene['date'], tzinfo='utc').to('local')
        logger.info(
            'Found an open scene (%s, %s)', open_scene['username'],
            open_scene['date'].format('YYYY-MM-DD HH:mm'),
        )
        if open_scene['username'] not in (getuser(), 'peterh'):
            yield open_scene


def generateText(scene):
    """Generate text for the popup.
    Returns:
        str: Message for user
            If empty, then it means no scenes are open.
    """
    text = ['"{scene}" is currently loaded elsewhere in the studio.', '']

    midnight = arrow.now().replace(hour=0, minute=0, second=0)
    for data in getSceneOpenData(scene):
        if data['date'] < midnight:
            dateFormat = data['date'].format('YYYY-MM-DD HH:mm')
        else:
            dateFormat = data['date'].format('HH:mm')
        text.append('{user} has had it open on {computer} since {date} ({ago}).'.format(
            user=data['username'],
            computer=data['computer_name'],
            date=dateFormat,
            ago=data['date'].humanize(),
        ))

    # If no scenes are open, then don't generate text
    if len(text) == 2:
        return ''
    return '\n'.join(text).format(scene=scene)


def beforeOpen(fileObj, clientData=None):
    """Check the scene for other sessions before opening."""
    scene = fileObj.resolvedFullName().replace('\\', '/')
    popupText = generateText(scene)
    if not popupText:
        return True

    action = mc.confirmDialog(
        title='Scene is Open',
        icn='critical',
        message=popupText + '\n\nWould you like to continue?',
        button=['Yes', 'No'],
        defaultButton='Yes',
        cancelButton='No',
        dismissString='No',
    )
    return action == 'Yes'


def beforeSave(clientData=None):
    """Check the scene for other sessions before opening."""
    scene = mc.file(query=True, sceneName=True).replace('\\', '/')
    popupText = generateText(scene)
    if not popupText:
        return

    action = mc.confirmDialog(
        title='Scene is Open',
        icn='critical',
        message=popupText + '\n\nWould you like to create a backup of the file before overwriting?',
        button=['Yes', 'No'],
        defaultButton='No',
        cancelButton='No',
        dismissString='No'
    )
    if action == 'Yes':
        logger.info('Creating backup of %r...', scene)
        scene, ext = os.path.splitext(scene)
        new = scene + '_conflict_backup' + ext
        mc.file(rename=new)
        mc.file(save=True, force=True)
        mc.file(rename=scene)
        logger.info('Created backup: %r', new)
        mc.confirmDialog(
            title='Scene Backup',
            icn='warning',
            message="Backup location:\n\n'{}'.".format(new)
        )


def afterLoad():
    """Check the scene for other sessions before opening."""
    scene = mc.file(query=True, sceneName=True).replace('\\', '/')
    popupText = generateText(scene)
    if not popupText:
        return True

    action = mc.confirmDialog(
        title='Scene is Open',
        icn='critical',
        message=popupText,
        button=['Ok'],
        defaultButton='Ok',
        cancelButton='Ok',
        dismissString='Ok',
    )
    return action == 'Ok'


def register_callbacks():
    """Register the before open and before save callbacks.

    If deferring this, then run `afterLoad()` since a scene will be
    loaded by the time this runs.
    """
    if mc.about(batch=True):
        return
    logger.info('Registering callbacks...')
    om2.MSceneMessage.addCheckFileCallback(om2.MSceneMessage.kBeforeOpenCheck, beforeOpen)
    om2.MSceneMessage.addCallback(om2.MSceneMessage.kBeforeSave, beforeSave)
