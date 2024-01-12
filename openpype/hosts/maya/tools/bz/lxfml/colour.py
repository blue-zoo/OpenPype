"""Handle LEGO colours.

Rewrite of classes found here: Y:\LEGO\1686s_LegoCitySeries1\Libraries\Script_Library\LEGOColorPalette\lego_color_palette.py
"""

from __future__ import absolute_import

import json


class ColourSpaceTransform(tuple):
    """Transform colours to a particular colour space.

    Colourspace transformation matrixes can be generated at
    https://www.colour-science.org:8010/apps/rgb_colourspace_transformation_matrix
    """

    TRANSFORMATION_MATRIX = {
        # convert from <key> to <value>
        'srgb': {
            'acescg': [[ 0.612494198536834,  0.338737251923843,  0.048855526064502],
                       [ 0.070594251610915,  0.917671483736251,  0.011704306146428],
                       [ 0.020727335004178,  0.106882231793044,  0.872338062223856]]
        },
        'acescg': {
            'srgb': [[ 1.707062673292185, -0.619959540375688, -0.087259850241725],
                     [-0.130976829484273,  1.139032275243841, -0.007956296823398],
                     [-0.024510601169497, -0.124810931680918,  1.149395970540385]]
        },
    }

    def __new__(cls, colour, colourSpace='srgb'):
        new = super(ColourSpaceTransform, cls).__new__(cls, map(float, colour[:3]))
        new._colourSpace = colourSpace.lower()
        new.r, new.g, new.b = new
        return new

    def _multiply(self, matrix):
        """Multiply the vector by a matrix."""
        m = matrix
        v = self
        return (m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
                m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
                m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2])

    @property
    def colourSpace(self):
        """Get the name of the colourspace."""
        return self._colourSpace

    def rgb(self, colourSpace='srgb'):
        """Convert the colour to RGB values with a colourspace."""
        if self.colourSpace == colourSpace:
            return self

        # Get the transformation matrixs for the base colour space
        matrixes = self.TRANSFORMATION_MATRIX.get(self.colourSpace, {})
        try:
            matrix = matrixes[colourSpace]
        except KeyError:
            if matrixes:
                error = 'unable to convert {old!r} to {new!r}'
            else:
                error = 'unknown colour space {old!r}'
            raise NotImplementedError(error.format(old=self.colourSpace, new=colourSpace))

        # Run the conversion
        return type(self)(self._multiply(matrix), colourSpace=colourSpace)

    def srgb(self):
        """Get the SRG colour values."""
        return self.rgb('srgb')

    def acesCG(self):
        """Get the ACEScg colour values."""
        return self.rgb('acescg')


class Colour(object):
    """Hold LEGO colour data."""

    __slots__ = ('_id', '_data', '_bzColour')

    def __init__(self, data, id):
        self._data = data
        self._id = id
        self._bzColour = {}

        for key, colourSpace in (('acesCG', 'acescg'), ('sRGB', 'srgb'), ('maya_primaries', 'srgb')):
            try:
                colour = data['BlueZooColor'][key]
            except KeyError:
                continue
            if colour is not None:
                self._bzColour[key] = ColourSpaceTransform(colour, colourSpace=colourSpace)

    def __repr__(self):
        return '<{} {} "{}">'.format(type(self).__name__, self.id, self.data.get('Color', 'unknown'))

    @property
    def id(self):
        """Get the colour ID."""
        return self._id

    @property
    def data(self):
        """Get the colour data."""
        return self._data

    @property
    def name(self, raw=False):
        """Get the colour name."""
        try:
            if raw:
                return self.data['Color']
            return '#{} {}'.format(self.id, self.data['Color'])
        except KeyError:
            return None

    @property
    def active(self):
        """If the colour is active."""
        return self.data.get('Active', True)

    @property
    def shaderVersion(self):
        """Shader version of the colour."""
        return self.data.get('ShaderVersion', 1.0)

    @property
    def isRefractive(self):
        """If the colour is refractive."""
        return self.data.get('isRefractive', False)

    @property
    def isMetallic(self):
        """If the colour is metallic."""
        return self.data.get('isMetallic', False)

    @property
    def isGlitter(self):
        """If the colour has glitter."""
        return self.data.get('hasGlitter', False)

    @property
    def isOpalescent(self):
        """If the colour is opalescent."""
        return self.data.get('isOpalescent', False)

    @property
    def bzColour(self):
        """Get the Blue Zoo colour override."""
        if 'maya_primaries' in self._bzColour:
            return self._bzColour['maya_primaries'].rgb()
        elif 'sRGB' in self._bzColour:
            return self._bzColour['sRGB'].rgb()
        elif 'acesCG' in self._bzColour:
            return self._bzColour['acesCG'].rgb()
        return self.viewportColour.rgb()

    def _chooseBestColour(self, key):
        """Choose the best colour to use."""
        if key in self.data:
            if self.isRefractive:
                for colourData in self.data[key]:
                    if 'refraction' in colourData[3].lower():
                        return colourData
            return self.data[key][0]
        return [0, 0, 0, 0]

    @property
    def viewportColour(self):
        """Choose a colour for the viewport."""
        return ColourSpaceTransform(self._chooseBestColour('Viewport'))

    @property
    def productionColour(self):
        """Choose a colour for production."""
        return ColourSpaceTransform(self._chooseBestColour('Production'))


class ColourPalette(object):
    """Store the full LEGO colour palette data."""

    __slots__ = ('_colours', '_filePath')

    def __init__(self, filePath='Y:/LEGO/1686s_LegoCitySeries1/Libraries/Shader_Library/Color_ID_List_BZ.json'):
        self._colours = {}
        self.filePath = filePath

    def __contains__(self, matID):
        """Check if a material ID exists."""
        return matID in self._colours

    @property
    def filePath(self):
        """Get the palette file path."""
        return self._filePath

    @filePath.setter
    def filePath(self, palette):
        """Set a new palette file path."""
        self._filePath = palette

        with open(self._filePath) as f:
            paletteData = json.load(f).items()
        self._colours = {int(matID): Colour(data, int(matID)) for matID, data in paletteData}

    def colour(self, matID, default=None):
        """Get a single colour."""
        return self._colours.get(matID, default)

    def colours(self):
        """Get multiple colours."""
        return list(self._colours.values())

    def save(self, filePath=None):
        """Save the palette data to disk."""
        if filePath is None:
            filePath = self.filePath

        data = {str(colour.id): colour.data for colour in self.colours()}
        with open(self.filePath, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=4, sort_keys=True)
