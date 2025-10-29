"""AI modified version of `colour.py` to work with the CSV data insmtead of JSON."""

import csv
import re


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
        # Ensure color values are floats for math operations
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

    __slots__ = ('_id', '_data', '_parsedColour')
    # Regex to parse (B=...,G=...,R=...) string
    _bgrRe = re.compile(r'B=(\d+),G=(\d+),R=(\d+)')

    def __init__(self, data, id):
        """
        Initialize the Colour from a CSV row dictionary.

        Args:
            data (dict): A row from a csv.DictReader.
            id (int): The material ID.
        """
        self._data = data
        self._id = id
        self._parsedColour = self._parseBgrString(self.data['Color'])

    def _parseBgrString(self, bgrString):
        """Parse (B=,G=,R=) string into (R, G, B) tuple in 0-255 range."""
        match = self._bgrRe.search(bgrString)
        # Assumes match is always found
        b, g, r = map(float, match.groups())
        return (r, g, b)

    def __repr__(self):
        return '<{} {} "{}">'.format(type(self).__name__, self.id, self.data.get('Name', 'unknown'))

    @property
    def id(self):
        """Get the colour ID."""
        return self._id

    @property
    def data(self):
        """Get the colour data (the raw CSV row dict)."""
        return self._data

    @property
    def name(self, raw=False):
        """Get the colour name."""
        try:
            name_str = self.data['Name']
            if raw:
                return name_str
            return '#{} {}'.format(self.id, name_str)
        except KeyError:
            return None

    @property
    def active(self):
        """If the colour is active."""
        return self.data.get('bIsActive', 'FALSE').upper() == 'TRUE'

    @property
    def shaderVersion(self):
        """Shader version of the colour."""
        # This property was in the JSON but not the CSV
        return 1.0

    @property
    def isStandard(self):
        """If the colour is refractive (Transparent)."""
        return self.data.get('MaterialType') == 'Standard'

    @property
    def isRefractive(self):
        """If the colour is refractive (Transparent)."""
        return self.isTransparent

    @property
    def isTransparent(self):
        """If the colour is refractive (Transparent)."""
        return self.data.get('MaterialType') == 'Transparent'

    @property
    def isMetallic(self):
        """If the colour is metallic."""
        # Assumes 'Metallic' key exists and is '0' or '1'
        return bool(int(self.data['Metallic']))

    @property
    def isGlitter(self):
        """If the colour has glitter."""
        # This property was in the JSON but not the CSV
        return False

    @property
    def isOpalescent(self):
        """If the colour is opalescent."""
        # This property was in the JSON but not the CSV
        return False

    @property
    def isRubber(self):
        """If the colour is refractive (Transparent)."""
        return self.data.get('MaterialType') == 'Rubber'

    @property
    def bzColour(self):
        """Get the main sRGB colour."""
        # bzColour was an override, but now it's the main colour
        return self.viewportColour.rgb()

    @property
    def viewportColour(self):
        """Choose a colour for the viewport."""
        # The CSV has one color, so we use it.
        # Pass the 0-255 (R, G, B) tuple to the transform class
        return ColourSpaceTransform(self._parsedColour)

    @property
    def productionColour(self):
        """Choose a colour for production."""
        # The CSV has one color, so we use it.
        return ColourSpaceTransform(self._parsedColour)


class ColourPalette(object):
    """Store the full LEGO colour palette data."""

    __slots__ = ('_colours', '_filePath')

    def __init__(self, filePath):
        """
        Initialize the palette from a CSV file.

        Args:
            filePath (str): Path to the new CSV colour palette.
        """
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
        """Set a new palette file path and load it."""
        self._filePath = palette
        self._colours.clear()  # Clear old data before loading

        with open(self._filePath) as f:
            # Use csv.DictReader to read the CSV using its headers
            reader = csv.DictReader(f)
            for row in reader:
                # Assume CSV is perfectly formatted:
                # '---' key exists and its value is an integer
                matID = int(row['---'])
                self._colours[matID] = Colour(row, matID)

    def colour(self, matID, default=None):
        """Get a single colour."""
        return self._colours.get(matID, default)

    def colours(self):
        """Get multiple colours."""
        return list(self._colours.values())
