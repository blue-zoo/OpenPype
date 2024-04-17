#!-*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2014 Joshua Banton and PyTimeCode developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

__name__ = "timecode"
__version__ = "1.4.0"
__description__ = "SMPTE Time Code Manipulation Library"
__author__ = "Erkan Ozgur Yilmaz"
__author_email__ = "eoyilmaz@gmail.com"
__url__ = "https://github.com/eoyilmaz/timecode"


class Timecode(object):
    """The main timecode class.

    Does all the calculation over frames, so the main data it holds is frames, then when
    required it converts the frames to a timecode by using the frame rate setting.

    Args:
        framerate (Union[str, int, float, Fraction]): The frame rate of the Timecode
            instance. If a str is given it should be one of ['23.976', '23.98', '24',
            '25', '29.97', '30', '50', '59.94', '60', 'NUMERATOR/DENOMINATOR', ms']
            where "ms" equals to 1000 fps. Otherwise, any integer or Fractional value is
            accepted. Can not be skipped. Setting the framerate will automatically set
            the :attr:`.drop_frame` attribute to correct value.
        start_timecode (Union[None, str]): The start timecode. Use this to be able to
            set the timecode of this Timecode instance. It can be skipped and then the
            frames attribute will define the timecode, and if it is also skipped then
            the start_second attribute will define the start timecode, and if
            start_seconds is also skipped then the default value of '00:00:00:00' will
            be used. When using 'ms' frame rate, timecodes like '00:11:01.040' use
            '.040' as frame number. When used with other frame rates, '.040' represents
            a fraction of a second. So '00:00:00.040' at 25fps is 1 frame.
        start_seconds (Union[int, float]): A float or integer value showing the seconds.
        frames (int): Timecode objects can be initialized with an integer number showing
            the total frames.
        force_non_drop_frame (bool): If True, uses Non-Dropframe calculation for 29.97
            or 59.94 only. Has no meaning for any other framerate. It is False by
            default.
    """

    def __init__(
        self,
        framerate,
        start_timecode=None,
        start_seconds=None,
        frames=None,
        force_non_drop_frame=False,
    ):

        self.force_non_drop_frame = force_non_drop_frame

        self.drop_frame = False

        self.ms_frame = False
        self.fraction_frame = False
        self._int_framerate = None
        self._framerate = None
        self.framerate = framerate

        self._frames = None

        # attribute override order
        # start_timecode > frames > start_seconds
        if start_timecode:
            self.frames = self.tc_to_frames(start_timecode)
        else:
            if frames is not None:
                self.frames = frames
            elif start_seconds is not None:
                if start_seconds == 0:
                    raise ValueError("``start_seconds`` argument can not be 0")
                self.frames = self.float_to_tc(start_seconds)
            else:
                # use default value of 00:00:00:00
                self.frames = self.tc_to_frames("00:00:00:00")

    @property
    def frames(self):
        """Return the _frames attribute value.

        Returns:
            int: The frames attribute value.
        """
        return self._frames

    @frames.setter
    def frames(self, frames):
        """Set the_frames attribute.

        Args:
            frames (int): A positive int bigger than zero showing the number of frames
                that this Timecode represents.
        """
        # validate the frames value
        if not isinstance(frames, int):
            raise TypeError(
                "%s.frames should be a positive integer bigger "
                "than zero, not a %s"
                % (self.__class__.__name__, frames.__class__.__name__)
            )

        if frames <= 0:
            raise ValueError(
                "%s.frames should be a positive integer bigger "
                "than zero, not %s" % (self.__class__.__name__, frames)
            )
        self._frames = frames

    @property
    def framerate(self):
        """Return the _framerate attribute.

        Returns:
            str: The frame rate of this Timecode instance.
        """
        return self._framerate

    @framerate.setter
    def framerate(self, framerate):
        """Set the framerate attribute.

        Args:
            framerate (Union[int, float, str, tuple, Fraction]): Several different type
                is accepted for this argument:

                int, float: It is directly used.
                str: Is used for setting DF Timecodes and possible values are
                    ["23.976", "23.98", "29.97", "59.94", "ms", "1000", "frames"] where
                    "ms" and "1000" results in to a milliseconds based Timecode and
                    "frames" will result a Timecode with 1 FPS.
                tuple: The tuple should be in (nominator, denominator) format in which
                    the frame rate is kept as a fraction.
                Fraction: If the current version of Python supports (which it should)
                    then Fraction is also accepted.
        """
        # Convert rational frame rate to float, defaults to None if not Fraction-like
        numerator = getattr(framerate, 'numerator', None)
        denominator = getattr(framerate, 'denominator', None)

        try:
            if "/" in framerate:
                numerator, denominator = framerate.split("/")
        except TypeError:
            # not a string
            pass

        if isinstance(framerate, tuple):
            numerator, denominator = framerate

        if numerator and denominator:
            framerate = round(float(numerator) / float(denominator), 2)
            if framerate.is_integer():
                framerate = int(framerate)

        # check if number is passed and if so convert it to a string
        if isinstance(framerate, (int, float)):
            framerate = str(framerate)

        self._ntsc_framerate = False

        # set the int_frame_rate
        if framerate == "29.97":
            self._int_framerate = 30
            self.drop_frame = not self.force_non_drop_frame
            self._ntsc_framerate = True
        elif framerate == "59.94":
            self._int_framerate = 60
            self.drop_frame = not self.force_non_drop_frame
            self._ntsc_framerate = True
        elif any(map(lambda x: framerate.startswith(x), ["23.976", "23.98"])):
            self._int_framerate = 24
            self._ntsc_framerate = True
        elif framerate in ["ms", "1000"]:
            self._int_framerate = 1000
            self.ms_frame = True
            framerate = 1000
        elif framerate == "frames":
            self._int_framerate = 1
        else:
            self._int_framerate = int(float(framerate))

        self._framerate = framerate

    def set_fractional(self, state):
        """Set if the Timecode is to be represented with fractional seconds.

        Args:
            state (bool): If set to True the current Timecode instance will be
                represented with a fractional seconds (will have a "." in the frame
                separator).
        """
        self.fraction_frame = state

    def set_timecode(self, timecode):
        """Set the frames by using the given timecode.

        Args:
            timecode (Union[str, Timecode]): Either a str representation of a Timecode
                or a Timecode instance.
        """
        self.frames = self.tc_to_frames(timecode)

    def float_to_tc(self, seconds):
        """Return the number of frames in the given seconds using the current instance.

        Args:
            seconds (float): The seconds to set hte timecode to. This uses the integer
                frame rate for proper calculation.

        Returns:
            int: The number of frames in the given seconds.ß
        """
        return int(seconds * self._int_framerate)

    def tc_to_frames(self, timecode):
        """Convert the given Timecode to frames.

        Args:
            timecode (Union[str, Timecode]): Either a str representing a Timecode or a
                Timecode instance.

        Returns:
            int: The number of frames in the given Timecode.
        """
        # timecode could be a Timecode instance
        if isinstance(timecode, Timecode):
            return timecode.frames

        hours, minutes, seconds, frames = map(int, self.parse_timecode(timecode))

        if isinstance(timecode, int):
            time_tokens = [hours, minutes, seconds, frames]
            timecode = ":".join(str(t) for t in time_tokens)

            if self.drop_frame:
                timecode = ";".join(timecode.rsplit(":", 1))

        if self.framerate != "frames":
            ffps = float(self.framerate)
        else:
            ffps = float(self._int_framerate)

        if self.drop_frame:
            # Number of drop frames is 6% of framerate rounded to nearest
            # integer
            drop_frames = int(round(ffps * 0.066666))
        else:
            drop_frames = 0

        # We don't need the exact framerate anymore, we just need it rounded to
        # nearest integer
        ifps = self._int_framerate

        # Number of frames per hour (non-drop)
        hour_frames = ifps * 60 * 60

        # Number of frames per minute (non-drop)
        minute_frames = ifps * 60

        # Total number of minutes
        total_minutes = (60 * hours) + minutes

        # Handle case where frames are fractions of a second
        if len(timecode.split(".")) == 2 and not self.ms_frame:
            self.fraction_frame = True
            fraction = timecode.rsplit(".", 1)[1]

            frames = int(round(float("." + fraction) * ffps))

        frame_number = (
            (hour_frames * hours)
            + (minute_frames * minutes)
            + (ifps * seconds)
            + frames
        ) - (drop_frames * (total_minutes - (total_minutes // 10)))

        return frame_number + 1  # frames

    def frames_to_tc(self, frames, skip_rollover = False):
        """Convert frames back to timecode.

        Args:
            frames (int): Number of frames.

        Returns:
            str: The string representation of the current Timecode instance.
        """
        if self.drop_frame:
            # Number of frames to drop on the minute marks is the nearest
            # integer to 6% of the framerate
            ffps = float(self.framerate)
            drop_frames = int(round(ffps * 0.066666))
        else:
            ffps = float(self._int_framerate)
            drop_frames = 0

        # Number of frames per ten minutes
        frames_per_10_minutes = int(round(ffps * 60 * 10))

        # Number of frames in a day - timecode rolls over after 24 hours
        frames_per_24_hours = int(round(ffps * 60 * 60 * 24))

        # Number of frames per minute is the round of the framerate * 60 minus
        # the number of dropped frames
        frames_per_minute = int(round(ffps) * 60) - drop_frames

        frame_number = frames - 1

        # If frame_number is greater than 24 hrs, next operation will rollover
        # clock
        if not skip_rollover:
            frame_number %= frames_per_24_hours

        if self.drop_frame:
            d = frame_number // frames_per_10_minutes
            m = frame_number % frames_per_10_minutes
            if m > drop_frames:
                frame_number += (drop_frames * 9 * d) + drop_frames * (
                    (m - drop_frames) // frames_per_minute
                )
            else:
                frame_number += drop_frames * 9 * d

        ifps = self._int_framerate

        frs = frame_number % ifps
        if self.fraction_frame:
            frs = round(frs / float(ifps), 3)

        secs = int((frame_number // ifps) % 60)
        mins = int(((frame_number // ifps) // 60) % 60)
        hrs = int((((frame_number // ifps) // 60) // 60))

        return hrs, mins, secs, frs

    def tc_to_string(self, hrs, mins, secs, frs):
        """Return the string representation of a Timecode with given info.

        Args:
            hrs (int): The hours portion of the Timecode.
            mins (int): The minutes portion of the Timecode.
            secs (int): The seconds portion of the Timecode.
            frs (int): The frames portion of the Timecode.

        Returns:
            str: The string representation of this Timecode.ßß
        """
        if self.fraction_frame:
            return "{hh:02d}:{mm:02d}:{ss:06.3f}".format(hh=hrs, mm=mins, ss=secs + frs)

        ff = "{:02d}"
        if self.ms_frame:
            ff = "{:03d}"

        return ("{:02d}:{:02d}:{:02d}{}" + ff).format(
            hrs, mins, secs, self.frame_delimiter, frs
        )

    def to_systemtime(self, as_float=False):
        """Convert a Timecode to the video system timestamp.
        For NTSC rates, the video system time is not the wall-clock one.

        Args:
            as_float (bool): Return the time as a float number of seconds.

        Returns:
            str: The "system time" timestamp of the Timecode.
        """
        if self.ms_frame:
            return self.float-(1e-3) if as_float else str(self)

        hh, mm, ss, ff = self.frames_to_tc(self.frames + 1, skip_rollover=True)
        framerate = float(self.framerate) if self._ntsc_framerate else self._int_framerate
        ms = ff/framerate
        if as_float:
            return (hh*3600 + mm*60 + ss + ms)
        return "{:02d}:{:02d}:{:02d}.{:03d}".format(hh, mm, ss, round(ms*1000))

    def to_realtime(self, as_float=False):
        """Convert a Timecode to a "real time" timestamp.
        Reference: SMPTE 12-1 §5.1.2

        Args:
            as_float (bool): Return the time as a float number of seconds.

        Returns:
            str: The "real time" timestamp of the Timecode.
        """
        #float property is in the video system time grid
        ts_float = self.float

        if self.ms_frame:
            return ts_float-(1e-3) if as_float else str(self)

        # "int_framerate" frames is one second in NTSC time
        if self._ntsc_framerate:
            ts_float *= 1.001
        if as_float:
            return ts_float

        f_fmtdivmod = lambda x: (int(x[0]), x[1])
        hh, ts_float = f_fmtdivmod(divmod(ts_float, 3600))
        mm, ts_float = f_fmtdivmod(divmod(ts_float, 60))
        ss, ts_float = f_fmtdivmod(divmod(ts_float, 1))
        ms = round(ts_float*1000)

        return "{:02d}:{:02d}:{:02d}.{:03d}".format(hh, mm, ss, ms)

    @classmethod
    def parse_timecode(cls, timecode):
        """Parse the given timecode string.

        This uses the frame separator do decide if this is a NDF, DF or a
        or milliseconds/fraction_of_seconds based Timecode.

        '00:00:00:00' will result a NDF Timecode where, '00:00:00;00' will result a DF
        Timecode or '00:00:00.000' will be a milliseconds/fraction_of_seconds based
        Timecode.

        Args:
            timecode (Union[int, str]): If an integer is given it is converted to hex
                and the hours, minutes, seconds and frames are extracted from the hex
                representation. If a str is given it should follow one of the SMPTE
                timecode formats.ß

        Returns:
            (int, int, int, int): A tuple containing the hours, minutes, seconds and
                frames part of the Timecode.
        """
        if isinstance(timecode, int):
            hex_repr = hex(timecode)
            # fix short string
            hex_repr = "0x%s" % (hex_repr[2:].zfill(8))
            hrs, mins, secs, frs = tuple(
                map(int, [hex_repr[i : i + 2] for i in range(2, 10, 2)])
            )

        else:
            bfr = timecode.replace(";", ":").replace(".", ":").split(":")
            hrs = int(bfr[0])
            mins = int(bfr[1])
            secs = int(bfr[2])
            frs = int(bfr[3])

        return hrs, mins, secs, frs

    @property
    def frame_delimiter(self):
        """Return correct frame deliminator symbol based on the framerate.

        Returns:
            str: The frame deliminator, ";" if this is a drop frame timecode, "." if
                this is a millisecond based Timecode or ":" in any other case.
        """
        if self.drop_frame:
            return ";"

        elif self.ms_frame or self.fraction_frame:
            return "."

        else:
            return ":"

    def __iter__(self):
        """Yield and iterator.

        Yields:
            Timecode: Yields this Timecode instance.
        """
        yield self

    def next(self):
        """Add one frame to this Timecode to go the next frame.

        Returns:
            Timecode: Returns self. So, this is the same Timecode instance with this
                one.
        """
        self.add_frames(1)
        return self

    def back(self):
        """Subtract one frame from this Timecode to go back one frame.

        Returns:
            Timecode: Returns self. So, this is the same Timecode instance with this
                one.
        """
        self.sub_frames(1)
        return self

    def add_frames(self, frames):
        """Add or subtract frames from the number of frames of this Timecode.

        Args:
            frames (int): The number to subtract from or add to the number of frames of
                this Timecode instance.
        """
        self.frames += frames

    def sub_frames(self, frames):
        """Add or subtract frames from the number of frames of this Timecode.

        Args:
            frames (int): The number to subtract from or add to the number of frames of
                this Timecode instance.
        """
        self.add_frames(-frames)

    def mult_frames(self, frames):
        """Multiply frames.

        Args:
            frames (int): Multiply the frames with this number.
        """
        self.frames *= frames

    def div_frames(self, frames):
        """Divide the number of frames to the given number.

        Args:
            frames (int): The other number to divide the number of frames of this
                Timecode instance to.
        """
        self.frames = int(self.frames / frames)

    def __eq__(self, other):
        """Override the equality operator.

        Args:
            other (Union[int, str, Timecode]): Either and int representing the number of
                frames, a str representing the start time of a Timecode with the same
                frame rate of this one, or a Timecode to compare with the number of
                frames.

        Returns:
            bool: True if the other is equal to this Timecode instance.
        """
        if isinstance(other, Timecode):
            return self.framerate == other.framerate and self.frames == other.frames
        elif isinstance(other, str):
            new_tc = Timecode(self.framerate, other)
            return self.__eq__(new_tc)
        elif isinstance(other, int):
            return self.frames == other

    def __ge__(self, other):
        """Override greater than or equal to operator.

        Args:
            other (Union[int, str, Timecode]): Either and int representing the number of
                frames, a str representing the start time of a Timecode with the same
                frame rate of this one, or a Timecode to compare with the number of
                frames.

        Returns:
            bool: True if the other is greater than or equal to this Timecode instance.
        """
        if isinstance(other, Timecode):
            return self.framerate == other.framerate and self.frames >= other.frames
        elif isinstance(other, str):
            new_tc = Timecode(self.framerate, other)
            return self.frames >= new_tc.frames
        elif isinstance(other, int):
            return self.frames >= other

    def __gt__(self, other):
        """Override greater than operator.

        Args:
            other (Union[int, str, Timecode]): Either and int representing the number of
                frames, a str representing the start time of a Timecode with the same
                frame rate of this one, or a Timecode to compare with the number of
                frames.

        Returns:
            bool: True if the other is greater than this Timecode instance.
        """
        if isinstance(other, Timecode):
            return self.framerate == other.framerate and self.frames > other.frames
        elif isinstance(other, str):
            new_tc = Timecode(self.framerate, other)
            return self.frames > new_tc.frames
        elif isinstance(other, int):
            return self.frames > other

    def __le__(self, other):
        """Override less or equal to operator.

        Args:
            other (Union[int, str, Timecode]): Either and int representing the number of
                frames, a str representing the start time of a Timecode with the same
                frame rate of this one, or a Timecode to compare with the number of
                frames.

        Returns:
            bool: True if the other is less than or equal to this Timecode instance.
        """
        if isinstance(other, Timecode):
            return self.framerate == other.framerate and self.frames <= other.frames
        elif isinstance(other, str):
            new_tc = Timecode(self.framerate, other)
            return self.frames <= new_tc.frames
        elif isinstance(other, int):
            return self.frames <= other

    def __lt__(self, other):
        """Override less than operator.

        Args:
            other (Union[int, str, Timecode]): Either and int representing the number of
                frames, a str representing the start time of a Timecode with the same
                frame rate of this one, or a Timecode to compare with the number of
                frames.

        Returns:
            bool: True if the other is less than this Timecode instance.
        """
        if isinstance(other, Timecode):
            return self.framerate == other.framerate and self.frames < other.frames
        elif isinstance(other, str):
            new_tc = Timecode(self.framerate, other)
            return self.frames < new_tc.frames
        elif isinstance(other, int):
            return self.frames < other

    def __add__(self, other):
        """Return a new Timecode with the given timecode or frames added to this one.

        Args:
            other (Union[int, Timecode]): Either and int value or a Timecode in which
                the frames are used for the calculation.

        Raises:
            TimecodeError: If the other is not an int or Timecode.

        Returns:
            Timecode: The resultant Timecode instance.
        """
        # duplicate current one
        tc = Timecode(self.framerate, frames=self.frames)
        tc.drop_frame = self.drop_frame

        if isinstance(other, Timecode):
            tc.add_frames(other.frames)
        elif isinstance(other, int):
            tc.add_frames(other)
        else:
            raise TimecodeError(
                "Type {} not supported for arithmetic.".format(other.__class__.__name__)
            )

        return tc

    def __sub__(self, other):
        """Return a new Timecode instance with subtracted value.

        Args:
            other (Union[int, Timecode]): The number to subtract, either an integer or
                another Timecode in which the number of frames is subtracted.

        Raises:
            TimecodeError: If the other is not an int or Timecode.

        Returns:
            Timecode: The resultant Timecode instance.
        """
        if isinstance(other, Timecode):
            subtracted_frames = self.frames - other.frames
        elif isinstance(other, int):
            subtracted_frames = self.frames - other
        else:
            raise TimecodeError(
                "Type {} not supported for arithmetic.".format(other.__class__.__name__)
            )
        tc = Timecode(self.framerate, frames=abs(subtracted_frames))
        tc.drop_frame = self.drop_frame
        return tc

    def __mul__(self, other):
        """Return a new Timecode instance with multiplied value.

        Args:
            other (Union[int, Timecode]): The multiplier either an integer or another
                Timecode in which the number of frames is used as the multiplier.

        Raises:
            TimecodeError: If the other is not an int or Timecode.

        Returns:
            Timecode: The resultant Timecode instance.
        """
        if isinstance(other, Timecode):
            multiplied_frames = self.frames * other.frames
        elif isinstance(other, int):
            multiplied_frames = self.frames * other
        else:
            raise TimecodeError(
                "Type {} not supported for arithmetic.".format(other.__class__.__name__)
            )
        tc = Timecode(self.framerate, frames=multiplied_frames)
        tc.drop_frame = self.drop_frame
        return tc

    def __div__(self, other):
        """Return a new Timecode instance with divided value.

        Args:
            other (Union[int, Timecode]): The denominator either an integer or another
                Timecode in which the number of frames is used as the denominator.

        Raises:
            TimecodeError: If the other is not an int or Timecode.

        Returns:
            Timecode: The resultant Timecode instance.
        """
        if isinstance(other, Timecode):
            div_frames = int(float(self.frames) / float(other.frames))
        elif isinstance(other, int):
            div_frames = int(float(self.frames) / float(other))
        else:
            raise TimecodeError(
                "Type {} not supported for arithmetic.".format(other.__class__.__name__)
            )

        return Timecode(self.framerate, frames=div_frames)

    def __truediv__(self, other):
        """Return a new Timecode instance with divided value.

        Args:
            other (Union[int, Timecode]): The denominator either an integer or another
                Timecode in which the number of frames is used as the denominator.

        Returns:
            Timecode: The resultant Timecode instance.
        """
        return self.__div__(other)

    def __repr__(self):
        """Return the string representation of this Timecode instance.

        Returns:
            str: The string representation of this Timecode instance.
        """
        return self.tc_to_string(*self.frames_to_tc(self.frames))

    @property
    def hrs(self):
        """Return the hours part of the timecode.

        Returns:
            int: The hours part of the timecode.
        """
        hrs, mins, secs, frs = self.frames_to_tc(self.frames)
        return hrs

    @property
    def mins(self):
        """Return the minutes part of the timecode.

        Returns:
            int: The minutes part of the timecode.
        """
        hrs, mins, secs, frs = self.frames_to_tc(self.frames)
        return mins

    @property
    def secs(self):
        """Return the seconds part of the timecode.

        Returns:
            int: The seconds part of the timecode.
        """
        hrs, mins, secs, frs = self.frames_to_tc(self.frames)
        return secs

    @property
    def frs(self):
        """Return the frames part of the timecode.

        Returns:
            int: The frames part of the timecode.
        """
        hrs, mins, secs, frs = self.frames_to_tc(self.frames)
        return frs

    @property
    def frame_number(self):
        """Return the 0-based frame number of the current timecode instance.

        Returns:
            int: 0-based frame number.
        """
        return self.frames - 1

    @property
    def float(self):
        """Return the seconds as float.

        Returns:
            float: The seconds as float.
        """
        return float(self.frames) / float(self._int_framerate)


class TimecodeError(Exception):
    """Raised when an error occurred in timecode calculation."""
