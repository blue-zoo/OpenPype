"""Copy the UV sets from the MiniFig model to the currently loaded asset.

1. Reference MiniFig
2. Delete existing asset UV sets
3. Transfer UV sets from MiniFig to asset
4. Delete history
6. Unreference MiniFig
"""

import maya.cmds as mc

MINIFIG = r'Y:\LEGO\1880s_LegoCity2025\Libraries\Assets\Characters\CHR_MiniFig\work\Modelling\Export\CHR_uvs\CHR_Minifig.ma'

GEO = [
    'C_torsoA_PLY',
    'C_torsoB_PLY',
    'C_groin_PLY',
    'R_legA_PLY',
    'R_legB_PLY',
    'R_legC_PLY',
    'L_legA_PLY',
    'L_legB_PLY',
    'L_legC_PLY',
    'L_arm_PLY',
    'R_arm_PLY',
    'L_hand_PLY',
    'R_hand_PLY',
    'C_head_PLY',
]


def main():
    print('Referencing {}...'.format(MINIFIG))
    minifig = mc.file(MINIFIG, reference=True, namespace='Minifig')

    # Delete UV sets
    print('Deleting existing UV sets...')
    for node in GEO:
        uvSets = mc.polyUVSet(node, query=True, allUVSets=True)
        for uvSet in uvSets[1:]:  # Can't delete the default one
            mc.polyUVSet(node, delete=True, uvSet=uvSet)

    # Copy UV sets
    print('Copying UV sets from minifig...')
    for geo in GEO:
        source = 'Minifig:' + geo
        print('Transfer from {} to {}'.format(source, geo))
        mc.transferAttributes(source, geo, transferUVs=2, sampleSpace=4)
        mc.delete(geo, constructionHistory=True)

    print('Removing minifig reference')
    mc.file(minifig, removeReference=True)

    print('Done')


if __name__ == '__main__':
    main()
