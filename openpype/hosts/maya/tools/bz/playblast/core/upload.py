import os
import subprocess
import copy

UPLOAD_TOOL = r"R:\IT\Pipeline\Applications\shotgridVersionUpload\shotgridUploader.exe"

def launchUploadTool(video, flags={}):

    # Blank out the Maya Env to stop child process complaining and detach from maya.
    _env= copy.copy(os.environ)
    #Clear any unicode from env vars.
    for item in _env.items():
        if type(item[1]) is not str:
            _env[item[0]] = str(_env[item[0]])
    _env['PATH'] = ""
    _env['PYTHONPATH'] = ""
    _env['QT_SCALE_FACTOR']="1"
    _env['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    _env['QT_SCREEN_SCALE_FACTORS'] = '1'

    cmdList =  [UPLOAD_TOOL,"--ui","--file",os.path.abspath(video)]
    for k, v in flags.items():
        cmdList.append(k)
        cmdList.append(v)

    DETACHED_PROCESS = 0x00000008
    cmd = subprocess.list2cmdline(cmdList)
    print(cmd)
    results = subprocess.Popen(cmdList,
                               close_fds=True, creationflags=DETACHED_PROCESS,env=_env)
