import importlib
import os
from openpype.lib import vendor_bin_utils
from openpype.hosts.maya.tools.bz.playblast.core import subprocess

importlib.reload(subprocess)

# Add the file path for the icon
_currentFile = __file__
_currentDir = os.path.dirname(_currentFile)
iconFilePath = os.path.join( _currentDir, "bz_logo_small.png" )
iconFilePath = iconFilePath.replace("\\","/")

cmd = '''
"{ffmpeg}"
 -i "{input}" -i "{icn}"
 -vcodec mjpeg -pix_fmt yuvj420p
 -filter_complex "  [1:v]scale=100:69 [ovrl], [0:v][ovrl ]  overlay=(main_w-overlay_w)v/2:(main_h-overlay_h)/2   :x=5  :y=-19
, drawtext=text=%{{eif\\\\\:n+{offset}  \\\\\:d}} \[ %{{eif\\\\\:n+1  \\\\\:d}} \\\: "{dur}" \]  : x=w-130: y= h-((2*lh)-10): fontcolor=white: fontsize=18: box=1: boxcolor=0x00000099 :fontfile='C\\:\\\\Windows\\\\Fonts\\\\ebrima.ttf'
, drawtext=text={date}  : x=w-180: y= (lh/2): fontcolor=white: fontsize=18: box=1: boxcolor=0x00000099 :fontfile='C\\:\\\\Windows\\\\Fonts\\\\ebrima.ttf'
, drawtext=text={user}  : x=((w-tw)/2)+120: y= 5: fontcolor=white: fontsize=18: box=1: boxcolor=0x00000099 :fontfile='C\\:\\\\Windows\\\\Fonts\\\\ebrima.ttf'
, drawtext=text={focal} : x=(w-tw)/2 :  y= 5 : fontcolor=white: fontsize=18: box=1: boxcolor=0x00000099 :fontfile='C\\:\\\\Windows\\\\Fonts\\\\ebrima.ttf'
, drawtext=text={comment} : x=10 :  y= h-((2*lh)-10) : fontcolor=white: fontsize=18: box=1: boxcolor=0x00000099 :fontfile='C\\:\\\\Windows\\\\Fonts\\\\ebrima.ttf' "
 -q:v 0
 -acodec pcm_s16le
 -timecode {timecode}
 -y  "{output}"
'''

def getffmpegLocation():
    ffmpeg = vendor_bin_utils.get_ffmpeg_tool_path("ffmpeg")
    ffprobe = vendor_bin_utils.get_ffmpeg_tool_path("ffprobe")
    return ffmpeg



def convert(
    inputFile = None,
    outputFile = None,
    timecode = None,
    offset = 0,
    duration = 0,
    focalLength = None,
    user = None,
    datetime = None,
    comment = None
    ):
    print(cmd)


    # Generate Command
    _cmd = cmd.format(
        ffmpeg = getffmpegLocation(),
        input = inputFile,
        date = datetime,
        user = user,
        focal = focalLength,
        offset = offset,
        dur=duration,
        timecode = timecode,
        output = outputFile,
        comment = comment,
        icn = iconFilePath
    )
    print(_cmd)
    _convertCommand = _cmd.replace("\n","")

    for line in subprocess.execute(_convertCommand):
        print(line)
    import os
    result = os.startfile(outputFile, 'open')

    return outputFile
