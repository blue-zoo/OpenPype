"""Read the LEGO XML data format.

Known version differences:
    6: Bricks have refID and uuid, parts have refID and no uuid
    8: Bricks and parts have uuid and no refID
"""

from __future__ import absolute_import

import re
from collections import namedtuple

try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree as etree


SelectionSet = namedtuple('SelectionSet', ('name', 'bricks'))

Group = namedtuple('Group', ('name', 'bricks'))


class _ElementItem(object):
    def __init__(self, element, version):
        self.element = element
        self.version = version
        if self.version >= 8:
            self.uuid = self['uuid']
        else:
            self.refID = int(self['refID'])

    def __repr__(self):
        return '<{} {}>'.format(
            type(self).__name__,
            ' '.join('{}="{}"'.format(k, v) for k, v in self.element.attrib.items())
        )

    def __getitem__(self, item):
        return self.element.attrib[item]

    def get(self, item, default=None):
        return self.element.attrib.get(item, default)

    def children(self, tag=None):
        for child in self.element:
            if tag is not None and child.tag != tag:
                continue
            yield child

    @property
    def mayaIdentifier(self):
        """Get a unique ID for use in Maya."""
        if self.version >= 8:
            return self.uuid.replace('-', '')
        return str(self.refID)


class Brick(_ElementItem):
    def __init__(self, element, version):
        super(Brick, self).__init__(element, version)
        self.designID = self['designID']
        if self.version < 8:
            self.uuid = self['uuid']

    @property
    def parts(self):
        for part in self.children('Part'):
            if part.attrib['partType'] == 'rigid':
                yield PartRigid(self, part, self.version)
            elif part.attrib['partType'] == 'sticker':
                yield PartSticker(self, part, self.version)
            elif part.attrib['partType'] == 'flex':
                yield PartFlex(self, part, self.version)
            else:
                raise NotImplementedError(part.attrib['partType'])


class _Part(_ElementItem):
    def __init__(self, brick, element, version):
        super(_Part, self).__init__(element, version)
        self.brick = brick
        self.designID = self['designID']
        self.decoration = self.get('decoration')

    @property
    def bones(self):
        for bone in self.children('Bone'):
            yield Bone(self, bone, self.version)


class PartRigid(_Part):
    def __init__(self, brick, element, version):
        super(PartRigid, self).__init__(brick, element, version)
        self.materials = self['materials']

    @property
    def matrix(self):
        for bone in self.bones:
            return bone.matrix


class PartSticker(_Part):
    def __init__(self, brick, element, version):
        super(PartSticker, self).__init__(brick, element, version)
        self.stickerSheetId = self['stickerSheetId']


class PartFlex(_Part):
    def __init__(self, brick, element, version):
        super(PartFlex, self).__init__(brick, element, version)
        self.materials = self['materials']


class Bone(_ElementItem):
    def __init__(self, part, element, version):
        super(Bone, self).__init__(element, version)
        self.part = part
        self.transformation = self['transformation']

    @property
    def matrix(self):
        """Take the transformation string and convert it to a 3D transformation matrix.

        >>> transformation = (
        ...     '-1,0,0,'
        ...     '0,-0.70710677758286,0.70710678479023,'
        ...     '0,0.70710678479023,0.70710677758286,'
        ...     '38.80000001,7.7947740024759,9.8165971105712'
        ... )
        >>> transToMatrix(transformation)
        [-1.0, 0.0, 0.0, 0.0, 0.0, -0.70710677758286, 0.70710678479023, 0.0, 0.0, 0.70710678479023, 0.70710677758286, 0.0, 38.80000001, 7.7947740024759, 9.8165971105712, 1.0]
        """
        matrix = [float(x) for x in self.transformation.split(',')]
        matrix.insert(3, 0.0)
        matrix.insert(7, 0.0)
        matrix.insert(11, 0.0)
        matrix.insert(15, 1.0)
        return matrix


class LXFML(object):
    def __init__(self, path):
        self.path = path
        self.root = etree.parse(path).getroot()
        self.version = int(self.root.attrib['versionMajor'])

    @property
    def bricks(self):
        """Get all the bricks.

        <Bricks>
            <Brick refID="0" designID="87079;G" itemNos="4560183" uuid="10483beb-7087-4c2f-b23f-7535c58cfc83">
                <Part refID="0" designID="87079;G" partType="rigid" materials="194:0">
                    <Bone refID="0" transformation="0,0,1,0,1,0,-1,0,0,-15.6,0,-15.6"/>
                </Part>
            </Brick>
            <Brick refID="1" designID="10202;H" itemNos="6014617" uuid="8736f6e3-83c4-43a7-9318-4e3a37299407">
                <Part refID="1" designID="10202;H" partType="rigid" materials="194:0">
                    <Bone refID="1" transformation="-1,0,0,0,1,0,0,0,-1,-6.8,0,-9.2"/>
                </Part>
            </Brick>
        </Bricks>
        """
        for element in self.root.find('Bricks'):
            if element.tag == 'Brick':
                yield Brick(element, self.version)

    @property
    def selectionSets(self):
        """Get the selection sets.

        Version 6:
            <GroupSystems>
                <BrickGroupSystem name="UserSelectionSets" isHierarchical="0" isUnique="0">
                    <Group refID="0" name="roadIntersectionTT1A" brickRefs="109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188"/>
                    <Group refID="1" name="roadIntersectionDT1A" brickRefs="100,92,91,102,87,101,99,97,96,93,95,90,85,9,7,6,48,49,47,55,54,53,52,25,2,20,65,83,82,11,19,18,13,12,14,24,21,28,27,22,26,23,5,3,62,60,56,63,64,32,39,40,42,43,35,37,30,29,34,57,58,10"/>
                    <Group refID="2" name="roadIntersectionDD1A" brickRefs="76,77,78,79,80,46,104,88,89,103,94,107,105,106,86,98,84,61,15,31,0,33,8,108,41,69,45,67,44,36,72,70,59,71,74,4,1,68,73,17,66,38,16,75,81,50,51"/>
                </BrickGroupSystem>
            </GroupSystems>

        Version 8:
            <GroupSystems>
                <BrickGroupSystem name="UserSelectionSets" isHierarchical="0" isUnique="0">
                    <Group uuid="a814d13b-bee1-44e7-8f78-521c3562367c" name="New Selection Set">
                        <Brick brickRef="ea0b8d6c-fb5f-4e8d-8abd-eb1c9ca71298"/>
                        <Brick brickRef="80c160d3-f71c-4e2e-9eb8-402b26016745"/>
                        <Brick brickRef="5bdf4a69-251e-475a-8cd2-8b43bb753757"/>
                        <Brick brickRef="8d5a5a01-3e23-42ae-9d35-1e2e9d4fcaef"/>
                    </Group>
                </BrickGroupSystem>
            </GroupSystems>
        """
        brickGroups = []
        for groupSystem in self.root.findall('GroupSystems'):
            for brickGroupSystem in groupSystem.findall('BrickGroupSystem[@name="UserSelectionSets"]'):
                brickGroups.extend(brickGroupSystem.findall('Group'))

        if not brickGroups:
            return

        if self.version >= 8:
            allBricks = {brick.uuid: brick for brick in self.bricks}
            for group in brickGroups:
                name = group.attrib['name']
                uuids = [brick.attrib['brickRef'] for brick in group.findall('Brick')]
                bricks = map(allBricks.__getitem__, uuids)
                yield SelectionSet(name, list(bricks))

        else:
            allBricks = {brick.refID: brick for brick in self.bricks}
            for group in brickGroups:
                name = group.attrib['name']
                brickRefs = group.attrib['brickRefs'].split(',')
                bricks = map(allBricks.__getitem__, map(int, brickRefs))
                yield SelectionSet(name, list(bricks))

    @property
    def groups(self):
        """Get the groups.

        <Configurations>
            <Configuration type="design">
                <Build uuid="daa87ad8-6d8d-44a9-b42b-2ac6b6560cbc" name="SteeringWheel" mainCategory="" subCategory="">
                    <Brick brickRef="50bee680-0f8c-4ed0-82bf-52ca14035757"/>
                </Build>
                <Build uuid="0e1dc3a8-cd0c-46ea-9b88-99d262a36107" name="RearLight" mainCategory="" subCategory="">
                    <Brick brickRef="e5b4205e-b701-4671-85b5-77a410aab3d5"/>
                </Build>
                <Build uuid="40632f19-4872-4909-8c2e-920965c1e1f5" name="Roof" mainCategory="" subCategory="">
                    <Brick brickRef="d544baaa-f4dc-4ecc-81cc-8c77dcc6ee11"/>
                    <Brick brickRef="2d2f9750-a4ea-402f-b4de-d62f18c6f469"/>
                    <Brick brickRef="a8296dad-4d5c-438d-b415-7132b7252201"/>
                    <Build uuid="1d5d9acd-43e7-4c26-b22c-d3f25fe8cbc7" name="Flames" mainCategory="" subCategory="">
                        <Brick brickRef="2b78f572-af03-4c0b-b640-c5ef348cf05c"/>
                        <Brick brickRef="8fec6640-3b0e-418a-b592-434a5af8daa4"/>
                    </Build>
                </Build>
            </Configuration>
        </Configurations>
        """
        def processBuild(build, parentName=None):
            name = formatGroupName(build.attrib['name'])
            if parentName is not None:
                name = '{}|{}'.format(parentName, name)

            uuids = [brick.attrib['brickRef'] for brick in build.findall('Brick')]
            bricks = map(allBricks.__getitem__, uuids)
            yield Group(name, list(bricks))

            for child in build.findall('Build'):
                for result in processBuild(child, parentName=name):
                    yield result

        allBricks = {brick.uuid: brick for brick in self.bricks}

        for configurations in self.root.findall('Configurations'):
            for configuration in configurations.findall('Configuration[@type="design"]'):
                for build in configuration.findall('Build'):
                    for result in processBuild(build):
                        yield result


def formatGroupName(name):
    if name in ('_sockets', '_pivot'):
        return name
    match = re.match(r'^(?:C_)?(.*?)(?:_GRP)?$', name)
    assert match is not None
    body = match.group(1)
    stripped = re.sub(r'[^a-zA-Z0-9]', '', body)
    return 'C_{}_GRP'.format(stripped)
