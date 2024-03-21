import maya.cmds as cmds
import os


def executeScriptOnFiles():
    files = cmds.fileDialog2(fileFilter='*.ma *.mb', dialogStyle=2, caption='Select Maya Files', fileMode=4)
    if not files:
        return

    scriptFiles = cmds.fileDialog2(fileFilter='*.py', dialogStyle=2, caption='Select Python Script', fileMode=1)
    if not scriptFiles:
        return

    print(f'Iterating through {len(files)} files...')
    for filePath in files:
        print(f'Loading {filePath}...')
        try:
            cmds.file(filePath, open=True, force=True)
        except RuntimeError as e:
            raise IOError(f'failed to open "{os.path.basename(filePath)}" (reason: "{e}"')

        print(f'Executing {scriptFiles[0]}...')
        with open(scriptFiles[0], 'r') as file:
            script = file.read()
            exec(script)

    cmds.confirmDialog(title='Complete', message=f'Script run on {len(files)} files', button=['Ok'], defaultButton='Ok')


if __name__ == '__main__':
    executeScriptOnFiles()
