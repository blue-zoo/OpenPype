from maya import cmds as mc
import os
import subprocess
import glob
import json
from Qt import QtWidgets, QtGui, QtCore
from functools import partial


from openpype.lib import vendor_bin_utils

ffmpeg = vendor_bin_utils.get_ffmpeg_tool_path("ffmpeg")
ffprobe = vendor_bin_utils.get_ffmpeg_tool_path("ffprobe")


def _executeCmdAndGetStderrAndStdout(cmd):
    """
    Takes in a command as a list of tokens in the style of subprocess
    calls and executes it using `subprocess.check_output`, capturing
    any potential errors.

    :param cmd: a list of tokens making up the command to be called
    :returns: the output of the command
    :raises Subprocess error: 
    """
    # Hide the dreaded prompt popup
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    # check_output doesn't print the received error by default, so
    # the best way to do it is to catch it and grab the stderr output
    # which has been piped to stdout
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT,
            shell=False, startupinfo=startupinfo)
    except Exception as e:
        if hasattr(e, "output"):
            print(" ".join(cmd) + " \n has returned the following error: " + e.output)
        raise e


def findAllImageSequences():
    """
    Finds and returns all image sequence patterns from any `file` nodes
    in the current scene that have image sequences as their loaded image.

    :returns: a list of glob patterns
    """
    patterns = set([])

    # Go through each file node in the scene and check if they have their
    # `imageSequence` checkbox enabled
    for imageSequenceFileNode in [x for x in mc.ls(typ="file")\
                                  if mc.getAttr(x + ".useFrameExtension")]:
        # If so, get the texture path
        texturePath = mc.getAttr(imageSequenceFileNode + ".fileTextureName")

        if not texturePath:
            # Skip any file nodes that don't have a texture loaded
            mc.warning("Skipping file node %s, as it doesn't have a texture loaded" % imageSequenceFileNode)
            continue

        if not os.path.exists(texturePath):
            # Skip any file nodes that point to missing textures
            mc.warning("Skipping file node %s, as it's image doesn't exist" % imageSequenceFileNode)
            continue

        patterns.add(identifyAndPatternizeIndex(texturePath))

    return list(patterns)

def identifyAndPatternizeIndex(texturePath):
    """
    Converts a single image from an image sequence to the glob pattern of
    that image sequence - replacing the last chunk of integers with ?s

    :param texturePath: the path to a single image of an image sequence
    :returns: a glob pattern for the image sequence this image is part of
    """
    # Identify the index token length
    # We go backwards through the name until we hit a non-digit character
    indexTokenLength = 0
    name, ext = texturePath.rsplit(".",1)
    for x in reversed(name):
        if not x.isdigit():
            break
        indexTokenLength += 1

    # Convert the path to a glob pattern
    return name[:-indexTokenLength] + ("?" * indexTokenLength) + "." + ext

def resizeImage(imgPath, resizedImgPath, resizeTo=(128,-1)):
    """
    Resizes an image, using `ffmpeg`.

    :param imgPath: path to the image to resize
    :param resizedImgPath: path to where the new resized image should be created
    :param resizeTo: the size to resize to, where a -1 in on of the dimensions means
        use the other dimension and retain aspect ratio
    :raises Subprocess error: if the `ffmpeg` command fails
    """
    cmd = [ffmpeg, "-y", "-i", imgPath, "-vf", "scale=%i:%i" % resizeTo, resizedImgPath]

    _executeCmdAndGetStderrAndStdout(cmd)

def getImgSize(imgPath):
    """
    Gets the size of an image using `ffprobe`.

    :param imgPath: path to the image to probe
    :returns: the dimensions of the image
    :raises Subprocess error: if the `ffprobe` command files
    """
    cmd = [ffprobe, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", imgPath]

    return [int(x) for x in _executeCmdAndGetStderrAndStdout(cmd).decode().split("x")]

def convertImageSequenceToSpriteSheet(imgSequencePattern, outputPath, rowLength=6):
    """
    Takes in a `glob` pattern of the image sequence and outputs a sprite sheet
    created from that image sequence.

    :param imgSequencePattern: the `glob` pattern for the image sequence
    :param outputPath: the output file to write the sprite sheet to.
        NOTE: A .json version of that file will also be created, containing the
              metadata for the sprite sheet.
    :param rowLength: number of tiles per row
    """
    # Grab all the images matching the blog pattern
    images = [img.replace("\\","/") for img in sorted(glob.glob(imgSequencePattern))]

    # Calculate the number of rows on the sprite sheet
    numRows = (len(images) // rowLength) if len(images) % rowLength == 0\
            else (len(images) // rowLength + 1)

    # Get the image size of the first image, expecting all of them to be the same
    imgSize = getImgSize(images[0])

    # Create padding elements, as we can't leave the empty tiles actually empty
    padding = []
    for i in range(rowLength - len(images) % rowLength):
        padding.append("color=c=black@0.0:s=%ix%i,format=rgba" % (imgSize[0], imgSize[1]))

    # Go through each row and build it using the `hstack` ffmpeg filter
    # `hstack` stacks inputs horizontally, so hstacking `rowLength` elements
    # creates one row
    rows = []
    for i in range(numRows):
        row = ""
        for j in range(rowLength):
            imageId = i*rowLength + j
            row += "[%i:v]" % imageId
        row += "hstack=inputs=%i[row%i]" % (rowLength, i)
        rows.append(row)

    # Build the full filter_complex string
    ## We start by joining all the rows that we've gathered above
    filterComplex = ";".join(rows)

    if len(rows) > 1:
        ## Then if we have more than one row, we use `vstack` to vertically
        ## stack all the rows, ending up with a grid, i.e. sprite sheet
        filterComplex += ";" + "".join([("[row%i]" % i) for i in range(numRows)]) +\
            "vstack=inputs=%i[out]" % numRows
        output = "[out]"
    else:
        ## Otherwise we have a 1x`rowLength` grid, so we just output the row
        output = "[row0]"

    # Prepend all images with the `-i` input flag
    inputs = []
    for img in images:
        inputs.append("-i")
        inputs.append(img)

    # If we need padding build them as inputs as well
    if padding:
        for pad in padding:
            inputs.append("-f")
            inputs.append("lavfi")
            inputs.append("-i")
            inputs.append(pad)

    # Compile and execute the command
    cmd = ["%s" % ffmpeg, "-y"] + inputs + [ 
        "-filter_complex", "%s" % filterComplex, "-frames:v", "1", "-map",
        output, outputPath]

    _executeCmdAndGetStderrAndStdout(cmd)

    # Write out a json metadata file
    # NOTE: This is currently writing way more than we need, so it works with the
    # parser I wrote for the toonboom sprite sheets, but we can massively
    # simplify it later on, as we know all tiles will be ordered perfectly
    # and have a consistent size
    #
    ## Gather all frames in the format [positionX,positionY,width,height,_,_,_]
    ## where the underscores were some weird offset coming out of toonboom
    frames = []
    for i in range(len(images)):
        x = i % rowLength
        y = int(i / rowLength)
        frames.append([x * imgSize[0],y*imgSize[1],imgSize[0],imgSize[1],0,0,0])

    ## Write the file, calculating the full resolution of the sprite sheet
    with open(outputPath.rsplit(".",1)[0] + ".json", "w") as f:
        f.write(json.dumps({
            "resolution":[imgSize[0] * rowLength, imgSize[1] * numRows],
            "frames":frames}))

def processFileNodesInCurrentFile(outputDirectory, temporaryResizedImagesDir=None,
        resizeTo=(128,-1), rowLength=6):
    """
    Finds all the image sequences in the currently opened file and converts them
    to sprite sheets.

    :param outputDirectory: the directory to output the sprite sheets to
    :param temporaryResizedImagesDir: a directory to store the temporary
        resized images, before they are compiled into a sprite sheet.
        If none is provided, the `outputDirectory` will be used.
    :param resizeTo: the size to resize to (look at `resizeImage()`)
    :param rowLength: number of tiles per row (look at `convertImageSequenceToSpriteSheet()`)
    """
    # If there's no provided temporary directory use the output directory
    #
    # That should be fine, since we're going to delete the resized images at the
    # end anyway
    temporaryResizedImagesDir = temporaryResizedImagesDir if temporaryResizedImagesDir\
        else outputDirectory

    # Get all image sequences in the currently opened maya scene
    imgSequencePatterns = findAllImageSequences()

    # Go through each img sequence pattern
    for imgSequencePattern in imgSequencePatterns:
        # Find all images part of that sequence
        imgs = sorted(glob.glob(imgSequencePattern))

        # Resize them down 128px
        for img in imgs:
            resizeImage(img, os.path.join(
                temporaryResizedImagesDir, os.path.split(img)[1]),
                resizeTo=resizeTo)

        # Get the resized images as a pattern
        resizedImagesPattern = os.path.join(
            temporaryResizedImagesDir, os.path.split(imgSequencePattern)[1])

        # Convert the resized images into a sprite sheet
        imgSequencePatternFileName = os.path.split(imgSequencePattern)[1]
        name, extension = imgSequencePatternFileName.rsplit(".", 1)

        # Build the sprite sheets
        convertImageSequenceToSpriteSheet(resizedImagesPattern,
            os.path.join(outputDirectory,
                name.replace("?","") + "-SpriteSheet." + extension),
            rowLength=rowLength)

        # Delete all the resized images
        for resizedImg in glob.glob(resizedImagesPattern):
            os.remove(resizedImg)


class SpriteSheetGeneratorUI(QtWidgets.QWidget):
    """
    A GUI for converting image sequences to sprite sheets.
    """

    instance = None
    """We should only ever have one window, so we store it as a singleton."""

    def __init__(self):
        if SpriteSheetGeneratorUI.instance:
            try:
                SpriteSheetGeneratorUI.instance.deleteLater()
            except:
                mc.warning("Could not delete previous SpriteSheetGenerator instance")
                raise

        SpriteSheetGeneratorUI.instance = self

        super(SpriteSheetGeneratorUI, self).__init__()

        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle("bz Sprite Sheet Generator")

        # Build UI
        layout = QtWidgets.QGridLayout()

        # Input files pattern field
        self.filePatternLineEdit = QtWidgets.QLineEdit()
        self.filePatternBrowse = QtWidgets.QPushButton("Browse")

        def assertImageSequenceAndReturnIt(filePath):
            pattern = identifyAndPatternizeIndex(filePath)
            assert "?" in pattern and len(glob.glob(pattern)) > 1,\
                "The provided file path is not an image sequence - " + filePath
            return pattern

        self.filePatternBrowse.clicked.connect(
            partial(self.getFilePathFromDialog, self.filePatternLineEdit,
                assertImageSequenceAndReturnIt))

        layout.addWidget(QtWidgets.QLabel("Image sequence (select one file):"), 0, 0)
        layout.addWidget(self.filePatternLineEdit, 1, 0)
        layout.addWidget(self.filePatternBrowse, 1, 1)

        # Output path field
        self.outputDirLineEdit = QtWidgets.QLineEdit()
        self.outputDirBrowse = QtWidgets.QPushButton("Browse")

        self.outputDirBrowse.clicked.connect(
            partial(self.getDirectoryPathFromDialog, self.outputDirLineEdit))

        layout.addWidget(QtWidgets.QLabel("Output directory:"), 2, 0)
        layout.addWidget(self.outputDirLineEdit, 3, 0)
        layout.addWidget(self.outputDirBrowse, 3, 1)

        # Optional temporary resized images directory
        self.temporaryResizedImagesDirLineEdit = QtWidgets.QLineEdit()
        self.temporaryResizedImagesDirBrowse = QtWidgets.QPushButton("Browse")

        self.temporaryResizedImagesDirBrowse.clicked.connect(
            partial(self.getDirectoryPathFromDialog, self.temporaryResizedImagesDirLineEdit))

        layout.addWidget(QtWidgets.QLabel("Temporary directory for the resized images (Optional):"), 4, 0)
        layout.addWidget(self.temporaryResizedImagesDirLineEdit, 5, 0)
        layout.addWidget(self.temporaryResizedImagesDirBrowse, 5, 1)

        # Size
        self.sizeLineEdit = QtWidgets.QLineEdit()
        self.sizeLineEdit.setValidator(QtGui.QIntValidator(1,4096))
        self.sizeLineEdit.setMaximumWidth(50)
        self.sizeLineEdit.setText("128")

        layout.addWidget(QtWidgets.QLabel("Tile width (will maintain aspect ratio):"), 6, 0)
        layout.addWidget(self.sizeLineEdit, 6, 1)

        # Num images per row
        self.rowLengthLineEdit = QtWidgets.QLineEdit()
        self.rowLengthLineEdit.setValidator(QtGui.QIntValidator(1,10))
        self.rowLengthLineEdit.setMaximumWidth(50)
        self.rowLengthLineEdit.setText("6")

        layout.addWidget(QtWidgets.QLabel("Number images per row:"), 7, 0)
        layout.addWidget(self.rowLengthLineEdit, 7, 1)

        # Generate button
        generateButton = QtWidgets.QPushButton("Generate")
        generateButton.clicked.connect(self.generate)

        layout.addWidget(generateButton, 8, 0, 1, 2)

        layout.setRowStretch(9,1)

        self.setLayout(layout)

    def _processPath(self, path, lineEdit, optionalProcessor):
        """
        Passes the given path through the `optionalProcessor` function and
        sets the `lineEdit`'s text to the processed path.
        """
        if path:
            try:
                lineEdit.setText(
                    path if not optionalProcessor else optionalProcessor(path))
            except:
                lineEdit.setText("")
                raise

    def getFilePathFromDialog(self, lineEdit, optionalProcessor=None):
        self._processPath(QtWidgets.QFileDialog.getOpenFileName(self, "File path")[0],
            lineEdit, optionalProcessor)

    def getDirectoryPathFromDialog(self, lineEdit, optionalProcessor=None):
        self._processPath(QtWidgets.QFileDialog.getExistingDirectory(self, "Directory path"),
            lineEdit, optionalProcessor)

    def validateInput(self):
        filePattern = self.filePatternLineEdit.text()
        if not glob.glob(filePattern):
            raise RuntimeError("Not a valid image sequence pattern - " + filePattern)

        outputDir = self.outputDirLineEdit.text()
        if not os.path.exists(outputDir):
            raise RuntimeError("Not a valid output directory - " + outputDir)

        temporaryResizedImagesDir = self.temporaryResizedImagesDirLineEdit.text()
        if temporaryResizedImagesDir and not os.path.exists(temporaryResizedImagesDir):
            raise RuntimeError("Not a valid temporary resize directory - " + temporaryResizedImagesDir)

        size = int(self.sizeLineEdit.text())
        if size < 1 or size > 4096:
            raise RuntimeError("Size out of bounds - 1 to 4096")

        rowLength = int(self.rowLengthLineEdit.text())
        if rowLength < 1:
            raise RuntimeError("A minimum of 1 image per row is required")

    def generate(self):
        """
        Using the specified image sequence pattern, output directory and the
        optional sprite sheet generation parameters, converts the image sequence
        to a sprite sheet.
        """
        self.validateInput()

        filePattern = self.filePatternLineEdit.text()
        name, ext = os.path.split(filePattern)[1].rsplit(".",1)
        outputDir = self.outputDirLineEdit.text()
        temporaryResizedImagesDir = self.temporaryResizedImagesDirLineEdit.text()
        temporaryResizedImagesDir = temporaryResizedImagesDir if temporaryResizedImagesDir\
            else outputDir

        print('Generating sprite sheet... (this takes a while)')

        resizedImages = []
        for img in glob.glob(filePattern):
            resizedName = os.path.join(temporaryResizedImagesDir, os.path.split(img)[1])
            resizeImage(img, resizedName, resizeTo=(int(self.sizeLineEdit.text()),-1))
            resizedImages.append(resizedName)

        resizedPattern = os.path.join(temporaryResizedImagesDir, name + "." + ext)

        spriteSheetPath = os.path.join(outputDir, name.replace("?","") + "-SpriteSheet." + ext)

        convertImageSequenceToSpriteSheet(imgSequencePattern=resizedPattern,
            outputPath=spriteSheetPath, rowLength=int(self.rowLengthLineEdit.text()))

        for img in resizedImages:
            os.remove(img)

        print('Sprite sheet generated.')

def runAsGUITool():
    widget = SpriteSheetGeneratorUI()
    widget.show()

if __name__ == "__main__":
    runAsGUITool()

