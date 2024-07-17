"""Maya specific actions.
These are mostly linked to callbacks, and the register_callbacks()
function only needs to be called once on startup.
"""

import os
import time
from threading import Thread

import maya.cmds as mc
import maya.api.OpenMaya as om2

from .. import add_action_data, log_action, start_session, update_session_activity
from ..utils import normpath


def register_callbacks():
    session_result = start_session()

    # Create the action
    setup_action = log_action('MAYA_SETUP',
        version=mc.about(version=True),
        api_version=mc.about(apiVersion=True),
        batch=mc.about(batch=True),
        operating_system=mc.about(operatingSystem=True),
    )

    # Add extra information to the action
    def after_setup():
        autosave_interval = mc.autoSave(query=True, interval=True) if mc.autoSave(query=True, enable=True) else None
        add_action_data(
            setup_action,
            autosave_interval=autosave_interval,
            evaluation_mode=mc.evaluationManager(query=True, mode=True)[0],
            gpu_override=bool(mc.optionVar(query='gpuOverride')),
        )
    if setup_action is not None and not mc.about(batch=True):
        mc.evalDeferred(after_setup, lowestPriority=True)

    om2.MSceneMessage.addCallback(om2.MSceneMessage.kMayaInitialized, callback_init)
    om2.MSceneMessage.addCallback(om2.MSceneMessage.kMayaExiting, callback_exiting)
    om2.MSceneMessage.addStringArrayCallback(om2.MSceneMessage.kBeforePluginLoad, callback_plugin_before_load)
    om2.MSceneMessage.addStringArrayCallback(om2.MSceneMessage.kAfterPluginLoad, callback_plugin_after_load)
    om2.MSceneMessage.addStringArrayCallback(om2.MSceneMessage.kBeforePluginUnload, callback_plugin_before_unload)
    om2.MSceneMessage.addStringArrayCallback(om2.MSceneMessage.kAfterPluginUnload, callback_plugin_after_unload)
    om2.MSceneMessage.addCallback(om2.MSceneMessage.kBeforeNew, callback_before_new)
    om2.MSceneMessage.addCallback(om2.MSceneMessage.kAfterNew, callback_after_new)
    om2.MSceneMessage.addCallback(om2.MSceneMessage.kBeforeOpen, callback_before_open)
    om2.MSceneMessage.addCallback(om2.MSceneMessage.kAfterOpen, callback_after_open)
    om2.MSceneMessage.addCallback(om2.MSceneMessage.kBeforeSave, callback_before_save)
    om2.MSceneMessage.addCallback(om2.MSceneMessage.kAfterSave, callback_after_save)
    if not mc.about(batch=True):
        if mc.about(version=True) > '2018':
            mc.scriptJob(event=['renderSetupAutoSave', update_session_activity])


    mc.evalDeferred(start_update_thread, lowestPriority=True)
    return session_result[0] if session_result else None


def _size_discretisation(size, bin=1024*128):
    """Adjust the size value into 128kb bins.

    Given a real world example, there are 1.4m discrete values. When
    binned per KB, then it drops to 150k values. Going to MB rounded to
    2 decimal places is 40k, then 1 decimal place is 10k.

    By taking this value and multiplying up again, it is still accurate
    enough, but removes a lot of near-duplicates.
    """
    return int(bin * round(size / bin))


def start_update_thread():
    """Thread to update the session every 5 minutes."""
    def update_timer():
        while True:
            time.sleep(60)
            update_session_activity()
    t = Thread(target=update_timer)
    t.daemon = True
    t.start()
    return t


def callback_init(clientData=None):
    log_action('MAYA_INIT')


def callback_exiting(clientData=None):
    log_action('MAYA_EXIT')


def callback_plugin_before_load(data, clientData=None):
    path = data[0]
    kwargs = dict(path=normpath(path))
    log_action('MAYA_BEFORE_PLUGIN_LOAD', **{k: v for k, v in kwargs.items() if v})


def callback_plugin_after_load(data, clientData=None):
    path, name = data[:2]
    kwargs = dict(path=normpath(path), name=name)
    kwargs = {}
    if path:
        kwargs['path'] = normpath(path)
    if name:
        kwargs['name'] = name

    # Extra plugin data
    if name == 'auto_update_reference':
        try:
            kwargs['active'] = bool(mc.autoUpdate(isActive=True))
        except AttributeError:
            kwargs['active'] = False

    if name == 'redshift4maya':
        rs_to_list = lambda result: [device.split(':')[1] for device in result.split(',')[:-1]]
        kwargs['all_compute_devices'] = rs_to_list(mc.rsPreference(query='AllComputeDevices'))
        kwargs['selected_compute_devices'] = rs_to_list(mc.rsPreference(query='SelectedComputeDevices'))
        if mc.rsPreference(exists='SelectedCudaDevices'):
            kwargs['selected_cuda_devices'] = rs_to_list(mc.rsPreference(query='SelectedCudaDevices'))

    log_action('MAYA_AFTER_PLUGIN_LOAD', **kwargs)


def callback_plugin_before_unload(data, clientData=None):
    name = data[0]
    kwargs = dict(name=name)
    log_action('MAYA_BEFORE_PLUGIN_UNLOAD', **{k: v for k, v in kwargs.items() if v})


def callback_plugin_after_unload(data, clientData=None):
    name, path = data[:2]
    kwargs = dict(name=name, path=normpath(path))
    log_action('MAYA_AFTER_PLUGIN_UNLOAD', **{k: v for k, v in kwargs.items() if v})


def callback_before_new(clientData=None):
    log_action('MAYA_BEFORE_NEW')


def callback_after_new(clientData=None):
    log_action('MAYA_AFTER_NEW')


def callback_before_open(clientData=None):
    log_action('MAYA_BEFORE_OPEN')


def callback_after_open(clientData=None):
    path = mc.file(query=True, sceneName=True)
    data = dict(
        path=normpath(path),
        reference_count=_count_loaded_refs(),
    )
    try:
        data['size'] = _size_discretisation(os.path.getsize(path))
    except OSError:
        pass

    log_action('MAYA_AFTER_OPEN', **data)


def callback_before_save(clientData=None):
    log_action('MAYA_BEFORE_SAVE')


def callback_after_save(clientData=None):
    path = mc.file(query=True, sceneName=True)
    data = dict(
        path=normpath(path),
        reference_count=_count_loaded_refs(),
    )
    try:
        data['size'] = _size_discretisation(os.path.getsize(path))
    except OSError:
        pass

    log_action('MAYA_AFTER_SAVE', **data)


def _count_loaded_refs():
    count = 0
    for ref in mc.ls(references=True):
        try:
            count += mc.referenceQuery(ref, isLoaded=True)
        except RuntimeError:
            pass
    return count
