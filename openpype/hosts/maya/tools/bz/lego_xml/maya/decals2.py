import logging

import maya.cmds as mc

from ..node import Node


logger = logging.getLogger('lego-importer')


def getDecalNodes():
    """Get all nodes containing a decal."""
    for node in map(Node, mc.ls('*.LEGO_decal', objectsOnly=True)):
        if node.attrs['LEGO_decal'].value:
            yield node


def assignDecalShaders(shader='DECAL_MAT_SG'):
    """Assign the decal shaders to all decal nodes.
    Requires the node network to have been created first.
    """
    for decal in getDecalNodes():
        decal.shadingEngine = shader


def setupNodeNetwork(doubleSided=True, stickers=True, namespace='shaders'):
    """Create the local decal node network."""
    logger.info('Cleaning existing decal shading nodes...')
    for node in mc.ls(':*DECAL*'):
        logger.info('Deleting %r...', node)
        mc.delete(node)

    logger.info('Creating decal shading nodes...')
    decalSG = Node.create('shadingEngine', renderable=True, noSurfaceShader=True, empty=True, name='DECAL_MAT_SG')

    # Surface shaders
    animDecalMat = Node.create('lambert', name='Anim_DECAL_MAT')
    animDecalMat.attrs['outColor'] >> decalSG.attrs['surfaceShader']

    decalSwitch = Node.create('RedshiftShaderSwitch', name='DECAL_SWITCH')
    decalSwitch.attrs['outColor'] >> decalSG.attrs['rsSurfaceShader']
    namespace + ':rsUserDataInteger_DECAL.out' >> decalSwitch.attrs['selector']

    # Material blender
    decalSingleSided = Node.create('RedshiftMaterialBlender', name='DECAL_SINGLE_SIDED_MAT')
    namespace + ':PLASTIC_CLASS_SWITCH.outColor' >> decalSingleSided.attrs['baseColor']
    decalSingleSided.attrs['outColor'] >> decalSwitch.attrs['shader1']

    # Materials
    decalMat = Node.create('RedshiftMaterial', name='DECAL_MAT')
    decalMat.attrs['outColor'] >> decalSingleSided.attrs['layerColor1']
    namespace + ':DECAL_MAT.refl_color' >> decalMat.attrs['refl_color']
    namespace + ':DECAL_MAT.refl_weight' >> decalMat.attrs['refl_weight']
    namespace + ':DECAL_MAT.refl_brdf' >> decalMat.attrs['refl_brdf']
    namespace + ':DECAL_MAT.refl_ior' >> decalMat.attrs['refl_ior']

    # Shading groups 10-19
    decalColSwitch2 = Node.create('RedshiftShaderSwitch', name='DECAL_COL_SWITCH_10_19')
    decalColSwitch2.attrs['outColor'] >> decalMat.attrs['diffuse_color']
    namespace + ':rsUserDataInteger_DECAL_NUMBER.out' >> decalColSwitch2.attrs['selector']
    decalColSwitch2.attrs['selector_offset'] = 10

    decalMaskSwitch2 = Node.create('RedshiftShaderSwitch', name='DECAL_MASK_SWITCH_10_19')
    decalMaskSwitch2.attrs['outColor'] >> decalSingleSided.attrs['blendColor1']
    namespace + ':rsUserDataInteger_DECAL_NUMBER.out' >> decalMaskSwitch2.attrs['selector']
    decalMaskSwitch2.attrs['selector_offset'] = 10

    # Shading groups 0-9
    decalColSwitch = Node.create('RedshiftShaderSwitch', name='DECAL_COL_SWITCH_00_09')
    decalColSwitch.attrs['outColor'] >> decalColSwitch2.attrs['default_shader']
    namespace + ':rsUserDataInteger_DECAL_NUMBER.out' >> decalColSwitch.attrs['selector']

    decalMaskSwitch = Node.create('RedshiftShaderSwitch', name='DECAL_MASK_SWITCH_00_09')
    decalMaskSwitch.attrs['outColor'] >> decalMaskSwitch2.attrs['default_shader']
    namespace + ':rsUserDataInteger_DECAL_NUMBER.out' >> decalMaskSwitch.attrs['selector']

    # Bump
    bumpBlenderDecal = Node.create('RedshiftBumpBlender', name='BMP_BLENDER_DECAL')
    bumpBlenderDecal.attrs['outColor'] >> decalMat.attrs['bump_input']
    namespace + ':BMP_BASIC_DECAL.out' >> bumpBlenderDecal.attrs['baseInput']
    namespace + ':BMP_BLENDER_DECAL.bumpWeight0' >> bumpBlenderDecal.attrs['bumpWeight0']
    namespace + ':BMP_BLENDER_DECAL.bumpWeight1' >> bumpBlenderDecal.attrs['bumpWeight1']
    bumpBlenderDecal.attrs['additive'] = True

    bumpAlphaDecal = Node.create('RedshiftBumpMap', name='BMP_ALPHA_DECAL')
    bumpAlphaDecal.attrs['out'] >> bumpBlenderDecal.attrs['bumpInput0']
    namespace + ':BMP_ALPHA_DECAL.factorInObjScale' >> bumpAlphaDecal.attrs['factorInObjScale']
    namespace + ':BMP_ALPHA_DECAL.inputType' >> bumpAlphaDecal.attrs['inputType']
    namespace + ':BMP_ALPHA_DECAL.scale' >> bumpAlphaDecal.attrs['scale']
    decalMaskSwitch2.attrs['outColor'] >> bumpAlphaDecal.attrs['input']

    bumpPrintDecal = Node.create('RedshiftBumpMap', name='BMP_PRINT_DECAL')
    bumpPrintDecal.attrs['out'] >> bumpBlenderDecal.attrs['bumpInput1']
    namespace + ':BMP_PRINT_DECAL.factorInObjScale' >> bumpPrintDecal.attrs['factorInObjScale']
    namespace + ':BMP_PRINT_DECAL.inputType' >> bumpPrintDecal.attrs['inputType']
    namespace + ':BMP_PRINT_DECAL.scale' >> bumpPrintDecal.attrs['scale']

    colourCorrectionDecal = Node.create('RedshiftColorCorrection', name='COLOR_CORR_DECAL')
    colourCorrectionDecal.attrs['outColor'] >> bumpPrintDecal.attrs['input']
    decalColSwitch2.attrs['outColor'] >> colourCorrectionDecal.attrs['input']
    namespace + ':COLOR_CORR_DECAL.contrast' >> colourCorrectionDecal.attrs['contrast']

    if doubleSided:
        logger.info('Creating DECAL_DOUBLE_SIDED shading nodes...')
        # Material blender
        decalDoubleSided = Node.create('RedshiftMaterialBlender', name='DECAL_DOUBLE_SIDED_MAT')
        namespace + ':PLASTIC_CLASS_SWITCH.outColor' >> decalDoubleSided.attrs['baseColor']
        decalDoubleSided.attrs['outColor'] >> decalSwitch.attrs['shader2']

        # Materials
        decalMat.attrs['outColor'] >> decalDoubleSided.attrs['layerColor1']
        decalBackMat = Node.create('RedshiftMaterial', name='DECAL_BACK_MAT')
        decalBackMat.attrs['outColor'] >> decalDoubleSided.attrs['layerColor2']
        namespace + ':DECAL_MAT.refl_color' >> decalBackMat.attrs['refl_color']
        namespace + ':DECAL_MAT.refl_weight' >> decalBackMat.attrs['refl_weight']
        namespace + ':DECAL_MAT.refl_brdf' >> decalBackMat.attrs['refl_brdf']
        namespace + ':DECAL_MAT.refl_ior' >> decalBackMat.attrs['refl_ior']

        # Shading groups 10-19
        decalMaskSwitch2.attrs['outColor'] >> decalDoubleSided.attrs['blendColor1']

        decalBackColSwitch2 = Node.create('RedshiftShaderSwitch', name='DECAL_BACK_COL_SWITCH_10_19')
        decalBackColSwitch2.attrs['outColor'] >> decalBackMat.attrs['diffuse_color']
        namespace + ':rsUserDataInteger_DECAL_NUMBER.out' >> decalBackColSwitch2.attrs['selector']
        decalBackColSwitch2.attrs['selector_offset'] = 10

        decalBackMaskSwitch2 = Node.create('RedshiftShaderSwitch', name='DECAL_BACK_MASK_SWITCH_10_19')
        decalBackMaskSwitch2.attrs['outColor'] >> decalDoubleSided.attrs['blendColor2']
        namespace + ':rsUserDataInteger_DECAL_NUMBER.out' >> decalBackMaskSwitch2.attrs['selector']
        decalBackMaskSwitch2.attrs['selector_offset'] = 10

        # Shading groups 0-10
        decalBackColSwitch = Node.create('RedshiftShaderSwitch', name='DECAL_BACK_COL_SWITCH_00_09')
        decalBackColSwitch.attrs['outColor'] >> decalBackColSwitch2.attrs['default_shader']
        namespace + ':rsUserDataInteger_DECAL_NUMBER.out' >> decalBackColSwitch.attrs['selector']

        decalBackMaskSwitch = Node.create('RedshiftShaderSwitch', name='DECAL_BACK_MASK_SWITCH_00_09')
        decalBackMaskSwitch.attrs['outColor'] >> decalBackMaskSwitch2.attrs['default_shader']
        namespace + ':rsUserDataInteger_DECAL_NUMBER.out' >> decalBackMaskSwitch.attrs['selector']

        # Bump
        bumpBlenderBackDecal = Node.create('RedshiftBumpBlender', name='BMP_BLENDER_BACK_DECAL')
        bumpBlenderBackDecal.attrs['outColor'] >> decalBackMat.attrs['bump_input']
        namespace + ':BMP_BASIC_DECAL.out' >> bumpBlenderBackDecal.attrs['baseInput']
        namespace + ':BMP_BLENDER_DECAL.bumpWeight0' >> bumpBlenderBackDecal.attrs['bumpWeight0']
        namespace + ':BMP_BLENDER_DECAL.bumpWeight1' >> bumpBlenderBackDecal.attrs['bumpWeight1']
        bumpBlenderBackDecal.attrs['additive'] = True

        bumpAlphaBackDecal = Node.create('RedshiftBumpMap', name='BMP_ALPHA_BACK_DECAL')
        bumpAlphaBackDecal.attrs['out'] >> bumpBlenderBackDecal.attrs['bumpInput0']
        namespace + ':BMP_ALPHA_BACK_DECAL.factorInObjScale' >> bumpAlphaBackDecal.attrs['factorInObjScale']
        namespace + ':BMP_ALPHA_BACK_DECAL.inputType' >> bumpAlphaBackDecal.attrs['inputType']
        namespace + ':BMP_ALPHA_BACK_DECAL.scale' >> bumpAlphaBackDecal.attrs['scale']
        decalBackMaskSwitch2.attrs['outColor'] >> bumpAlphaBackDecal.attrs['input']

        bumpPrintBackDecal = Node.create('RedshiftBumpMap', name='BMP_PRINT_BACK_DECAL')
        bumpPrintBackDecal.attrs['out'] >> bumpBlenderBackDecal.attrs['bumpInput1']
        namespace + ':BMP_PRINT_DECAL.factorInObjScale' >> bumpPrintBackDecal.attrs['factorInObjScale']
        namespace + ':BMP_PRINT_DECAL.inputType' >> bumpPrintBackDecal.attrs['inputType']
        namespace + ':BMP_PRINT_DECAL.scale' >> bumpPrintBackDecal.attrs['scale']

        colourCorrectionBackDecal = Node.create('RedshiftColorCorrection', name='COLOR_CORR_BACK_DECAL')
        colourCorrectionBackDecal.attrs['outColor'] >> bumpPrintDecal.attrs['input']
        decalBackColSwitch2.attrs['outColor'] >> colourCorrectionBackDecal.attrs['input']
        namespace + ':COLOR_CORR_DECAL.contrast' >> colourCorrectionBackDecal.attrs['contrast']

    if stickers:
        logger.info('Creating DECAL_STICKER nodes...')
        # Materials
        decalStickerMat = Node.create('RedshiftMaterial', name='DECAL_STICKER_MAT')
        decalStickerMat.attrs['outColor'] >> decalSwitch.attrs['shader3']
        namespace + ':BMP_STICKER.out' >> decalStickerMat.attrs['bump_input']
        namespace + ':RGH_LAYER_STICKER.outColorR' >> decalStickerMat.attrs['refl_roughness']
        namespace + ':DECAL_STICKER_MAT.refl_color' >> decalStickerMat.attrs['refl_color']
        namespace + ':DECAL_STICKER_MAT.refl_weight' >> decalStickerMat.attrs['refl_weight']
        namespace + ':DECAL_STICKER_MAT.refl_brdf' >> decalStickerMat.attrs['refl_brdf']
        namespace + ':DECAL_STICKER_MAT.refl_ior' >> decalStickerMat.attrs['refl_ior']

        # Attach to the highest col switch (change this if dynamically generating them)
        decalColSwitch2.attrs['outColor'] >> decalStickerMat.attrs['diffuse_color']

    logger.info('Created decal shading node network')
