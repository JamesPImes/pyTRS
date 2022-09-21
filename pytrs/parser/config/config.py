
"""
A class to configure parsing of individual ``PLSSDesc`` and ``Tract``
objects.
"""

import re

from .master_config import *
from .layouts import _IMPLEMENTED_LAYOUTS


class ConfigError(TypeError):
    """
    Wrong type of object was passed to ``config=`` argument or when
    initializing a Config() object.
    """
    def __init__(self, obj=None):
        msg = "`config` must be a str, None, or a pytrs.Config object."
        if obj is not None:
            msg = f"{msg} Passed type {type(obj)!r}."
        super().__init__(msg)


class Config:
    """
    A class to configure how ``PLSSDesc`` and ``Tract`` objects should
    be parsed.

    Below are all possible config settings.  Join desired settings
    together in a single string, separated by comma, with spaces
    optional (e.g., ``'s, e, clean_qq'``).

    - ``'n'`` -- set ``default_ns='n'``
    - ``'s'`` -- set ``default_ns='s'``
    - ``'e'`` -- set ``default_ew='e'``
    - ``'w'`` -- set ``default_ew='w'``
    - ``parse_qq`` -- Instruct ``Tract`` objects to parse into lots/qqs
      when initialized. (†)
    - ``clean_qq`` -- Allow broader recognition of aliquots. (†)

      .. warning::
            Use ``'clean_qq'`` only if the data you're working with has
            nothing but simple aliquots and lots (i.e. no metes-and-
            bounds descriptions, exceptions, etc.).

    - ``'sec_colon_required'`` -- Require colon after section number.
      (‡)
    - ``'sec_colon_cautious'`` -- Require colon after section number,
      but do a second pass if no valid section is discovered during the
      first pass. (‡)
    - 'suppress_lot_divs' -- Discard any divisions of lots -- e.g.,
      report 'N/2 of Lot 1' as ``'L1'``. The default behavior is to
      include lot divisions -- i.e. will report as ``'N2 of L1'`` unless
      ``'suppress_lot_divs'`` is used. (†)
    - ``'ocr_scrub'`` -- Scrub common OCR artefacts from the
      description.
    - ``'segment'`` -- Break up a PLSS description into chunks before
      parsing into tracts. (Might capture scenarios where the
      description changes ``layout`` partway through, but could also
      prevent the parser from generating proper warning flags.)
    - ``'qq_depth_min.<number>'`` -- Sets the minimum ``qq_depth`` to
      the specified <number>. (◊, †)
        - (Defaults to ``'qq_depth_min.2'`` -- i.e. parse to at least
          quarter-quarters.)
    - ``'qq_depth_max.<number>'`` -- Sets the maximum ``qq_depth`` to
      the specified <number>. (◊, †)
    - ``'qq_depth.<int>'`` -- Set the minimum *and* maximum ``qq_depth``
      to the specified <number> -- i.e. parse to the exact ``qq_depth``.
      (◊, †)
    - ``'break_halves'`` - break all aliquot halves into quarters, *even
      if* we're at divisions smaller than the specified
      ``qq_depth_min``. (†)

    - ``'TRS_desc'`` -- force ``PLSSDesc`` to be parsed as this
      ``layout``.
    - ``'desc_STR'`` -- force ``PLSSDesc`` to be parsed as this
      ``layout``.
    - 'S_desc_TR' -- force ``PLSSDesc`` to be parsed as this
      ``layout``.
    - ``'TR_desc_S'`` -- force ``PLSSDesc`` to be parsed as this
      ``layout``.
    - ``'copy_all'`` -- force ``PLSSDesc`` to be parsed as this
      ``layout``.

    († Denotes config settings that affect only ``Tract`` objects, but
    which can also be used with ``PLSSDesc`` objects to impact their
    subordinate ``Tract`` objects.)

    (‡ ``sec_colon_required`` and ``sec_colon_cautious`` only have any
    effect on ``TRS_desc`` and ``S_desc_TR`` layouts -- i.e. those
    layouts in which the description block follows the section number.
    Moreover, if ``sec_colon_required`` is used, then
    ``sec_colon_cautious`` will have no effect.)

    (◊ See below discussion regarding ``qq_depth``.)

    ``qq_depth_min``, ``qq_depth_max``, and/or ``qq_depth`` affect how
    'deeply' to parse aliquots -- i.e. to 160-acre divisions (quarter
    sections), 40-acre divisions (quarter-quarters), 10-acre divisions,
    etc.

    By default, aliquots are parsed down to *at least*
    quarter-quarters::

        # If qq_depth_min is 2 (the default).
        'N/2NE/4'  -->  ['NENE', 'NWNE']

    But smaller divisions that exist in the text will also be reported::

        # If qq_depth_min is 2 (the default).
        'S/2N/2NE/4'  -->  ['S2NENE', 'S2NWNE']

    Such smaller divisions can be curtailed by specifying
    ``qq_depth_max``. For example, if set to 2, anything smaller than
    quarter-quarter will be discarded::

        # If qq_depth_max is set to 2.
        'N/2NE/4'  -->  ['NENE', 'NWNE']
        'S/2N/2NE/4'  -->  ['NENE', 'NWNE']

    We can force parsing to smaller aliquots by increasing the
    ``qq_depth_min``::

        # If qq_depth_max is set to 3.
        'NW/4NE/4'  -->  ['NENWNE', 'NWNWNE', 'SENWNE', 'SWNWNE']
        'S/2NW/4NE/4'  -->  ['SENWNE', 'SWNWNE']

    We can force parsing to an *exact* depth by specifying ``qq_depth``
    (which will override both ``qq_depth_min`` and ``qq_depth_max``)::

        # If qq_depth is set to 1 (i.e. quarters).
        'N/2'  -->  ['NE', 'NW']
        'S/2N/2'  -->  ['NE', 'NW']

        # If qq_depth is set to 2 (i.e. quarter-quarters).
        'NE/4'  -->  ['NENE', 'NWNE', 'SENE', 'SWNE']
        'N/2NE/4'  -->  ['NENE', 'NWNE']
        'S/2N/2NE/4'  -->  ['NENE', 'NWNE']

        # If qq_depth is set to 3.
        'NW/4NE/4'  -->  ['NENWNE', 'NWNWNE', 'SENWNE', 'SWNWNE']
        'S/2N/2NE/4'  -->  ['SENENE', 'SWNENE', 'SENWNE', 'SWNWNE']

    Finally, we can use ``break_halves`` to split halves into quarters,
    even if they occur beyond the specified ``qq_depth_min``::

        # If qq_depth_min is set to 2, but also using break_halves.
        'NW/4NE/4'  -->  ['NWNE']
        'S/2NW/4NE/4'  -->  ['SENWNE', 'SWNWNE']

    .. warning::
        Do not set ``qq_depth_max`` to be less than ``qq_depth_min``.
        Doing so will result in reporting aliquots that do not actually
        exist.

    .. warning::
        Setting ``qq_depth_min`` or ``qq_depth`` to a number larger than
        4 will quickly start to be resource- and time-intensive, because
        each additional number is another exponential division.


    For a GUI application for viewing and selecting ``Config`` options,
    import and launch ``prompt_config()`` from the
    ``pytrs.interface_tools`` module:

    .. code-block:: python

        import pytrs.interface_tools
        pytrs.interface_tools.prompt_config()
    """

    # Implemented settings that are settable via Config object:
    _CONFIG_ATTRIBUTES = (
        'default_ns',
        'default_ew',
        'layout',
        'wait_to_parse',
        'parse_qq',
        'clean_qq',
        'sec_colon_required',
        'sec_colon_cautious',
        'suppress_lot_divs',
        'ocr_scrub',
        'segment',
        'qq_depth',
        'qq_depth_min',
        'qq_depth_max',
        'break_halves',
    )

    # A list of attribute names whose values should be a bool:
    _BOOL_TYPE_ATTRIBUTES = (
        'wait_to_parse',
        'parse_qq',
        'clean_qq',
        'suppress_lot_divs',
        'sec_colon_required',
        'sec_colon_cautious',
        'ocr_scrub',
        'segment',
        'break_halves',
    )

    _INT_TYPE_ATTRIBUTES = (
        'qq_depth_min',
        'qq_depth_max',
        'qq_depth',
    )

    # Those attributes relevant to PLSSDesc objects:
    _PLSSDESC_ATTRIBUTES = _CONFIG_ATTRIBUTES

    # Those attributes relevant to Tract objects:
    _TRACT_ATTRIBUTES = (
        'default_ns',
        'default_ew',
        'parse_qq',
        'clean_qq',
        'suppress_lot_divs',
        'ocr_scrub',
        'qq_depth',
        'qq_depth_min',
        'qq_depth_max',
        'break_halves',
    )

    def __init__(self, config_text: str = None, config_name=''):
        """
        Compile a Config object from a string ``config_text=``, with
        optional parameter ``config_name=`` that does not affect
        parsing.

        Pass config parameters as a single string, with each setting
        separated by comma, and spaces optional.
            ex: ``'n, w, clean_qq, suppress_lot_divs'``
        """

        # All attributes (except config_name) are defaulted to `None`,
        # because PLSSDesc and Tract objects will use only those that
        # have been specified as other than `None`.

        if isinstance(config_text, Config):
            # If a Config object is passed as the first argument,
            # decompile its text and use that:
            config_text = config_text.decompile_to_text()
        elif config_text is None:
            config_text = ''
        elif not isinstance(config_text, str):
            raise ConfigError(config_text)
        self.config_text = config_text
        self.config_name = config_name

        # Default all other attributes to `None`:
        self.default_ns = None
        self.default_ew = None
        self.layout = None
        self.wait_to_parse = None
        self.parse_qq = None
        self.clean_qq = None
        self.sec_colon_required = None
        self.sec_colon_cautious = None
        self.suppress_lot_divs = None
        self.ocr_scrub = None
        self.segment = None
        self.qq_depth = None
        self.qq_depth_min = None
        self.qq_depth_max = None
        self.break_halves = None

        # Break up text.
        self.text_to_attributes(config_text)

    def __str__(self):
        return self.decompile_to_text()

    def __repr__(self):
        return f"Config<{self.decompile_to_text()!r}>"

    def text_to_attributes(self, config_text: str) -> None:
        """
        Convert the text into ``Config`` values and store them to the
        appropriate ``Config`` attributes.

        :param config_text: standard ``Config`` text.
        :return: None.
        """
        config_text = re.sub(r'\s*', '', config_text)
        # Separate config parameters with ','  or  ';'
        for line in re.split(r'[;,]', config_text):
            if not line:
                continue
            if re.split(r'[\.=]', line)[0] in Config._BOOL_TYPE_ATTRIBUTES:
                # If string is the name of an attribute that will be stored
                # as a bool, default to `True` (but will be overruled in
                # _set_str_to_values() if specified otherwise):
                self._set_str_to_values(line, default_bool=True)
            elif line in MasterConfig._LEGAL_NS:
                # Specifying N/S can be done with just a string (there's
                # nothing else it can mean in config context.)
                self.default_ns = line
            elif line in MasterConfig._LEGAL_EW:
                # Specifying E/W can be done with just a string (there's
                # nothing else it can mean in config context.)
                self.default_ew = line
            elif line in _IMPLEMENTED_LAYOUTS:
                # Specifying layout can be done with just a string
                # (there's nothing else it can mean in config context.)
                self.layout = line
            else:
                # This method handles any other parameter.
                self._set_str_to_values(line)
        return None

    @classmethod
    def from_parent(cls, parent, config_name='', suppress_layout=False):
        """
        Compile and return a ``Config`` object from the settings in a
        ``PLSSDesc`` object or ``Tract`` object.

        :param parent: A ``PLSSDesc`` or ``Tract`` object.
        :param config_name: An optional string, being the name of this
         ``Config`` object.
        :param suppress_layout: Whether to include the ``.layout``
         attribute from the parent (if any). (Defaults to ``False``)
        """
        config = cls(config_name=config_name)
        config.layout = getattr(parent, 'layout', None)
        if suppress_layout:
            config.layout = None
        config.parse_qq = parent.parse_qq
        config.clean_qq = parent.clean_qq
        config.default_ns = parent.default_ns
        config.default_ew = parent.default_ew
        config.suppress_lot_divs = parent.suppress_lot_divs
        return config

    @classmethod
    def from_dict(cls, parameters: dict, config_name=''):
        """
        Get a new ``Config`` from a dict, keyed by parameter name. Uses
        only the keys found in the dict, and ignores any keys that do
        not correspond to ``Config`` attribute names.

        :param parameters: A dict of parameter names and corresponding
         values for the ``Config``.

        :param config_name: An optional string, being the name of this
         ``Config`` object. (If specified, will override a 'config_name'
         key in the ``parameters`` dict, if any.)

        :return: A new ``Config``.
        """
        if config_name:
            name = config_name
        else:
            name = parameters.get('config_name', '')
        cf = Config(config_name=name)
        for att in cls._CONFIG_ATTRIBUTES:
            val = parameters.get(att, None)
            if val is None:
                continue
            elif att in cls._BOOL_TYPE_ATTRIBUTES and not isinstance(val, bool):
                raise ValueError(
                    f"Illegal value type {type(val)!r} "
                    f"passed for attribute {att!r}. Expected bool."
                )
            elif att in cls._INT_TYPE_ATTRIBUTES and not isinstance(val, int):
                raise ValueError(
                    f"Illegal value type {type(val)!r} "
                    f"passed for attribute {att!r}. Expected int."
                )
            elif att == 'default_ns':
                val = verify_default_ns(val)
            elif att == 'default_ew':
                val = verify_default_ew(val)
            setattr(cf, att, val)
        return cf

    @classmethod
    def from_kwargs(cls, config_name='', **kwargs):
        """
        Get a new ``Config`` from kwargs, keyed by parameter name. Uses
        only the args provided, and ignores any parameters keys that do
        not correspond to ``Config`` attribute names.

        :param kwargs: Keyword arguments that line up with appropriate
         ``Config`` settings and values.

        :param config_name: An optional string, being the name of this
         ``Config`` object.

        :return: A new ``Config``.
        """
        return cls.from_dict(kwargs, config_name)

    def decompile_to_text(self) -> str:
        """
        Decompile a ``Config`` object into its equivalent string.
        """
        write_vals = []
        for att in Config._CONFIG_ATTRIBUTES:
            w = attrib_and_val_to_str(att, getattr(self, att))
            if w:
                write_vals.append(w)
        return ','.join(write_vals)

    def _set_str_to_values(self, attrib_val, default_bool=None):
        """
        INTERNAL USE:

        Take in a string of an attribute/value pair (in the format
        ``'attribute.value'`` or ``'attribute=value'``) and set the
        appropriate value of the attribute to this ``Config`` object.
        """
        try:
            # split attribute/value pair by : or . or =
            attribute, value = re.split(r'[\.=:]', attrib_val)
        except ValueError:
            attribute = attrib_val
            value = None
        if attribute not in self._CONFIG_ATTRIBUTES:
            raise ValueError(f"Illegal config attribute {attribute!r}")
        # Convert the value based on the category of the attribute.
        if attribute in Config._BOOL_TYPE_ATTRIBUTES:
            if value is None:
                value = default_bool
            else:
                value = str_to_value(value)
        elif attribute == 'default_ns':
            if value is not None:
                value = verify_default_ns(value)
        elif attribute == 'default_ew':
            if value is not None:
                value = verify_default_ew(value)
        else:
            value = str_to_value(value)
        if value is not None:
            setattr(self, attribute, value)
        return None


def attrib_and_val_to_str(attribute, value):
    """
    INTERNAL USE:

    Encode an attribute/value pair into the equivalent string as
    understood by ``Config`` objects.
    :param attribute:
    :param value:
    :return: The attribute/value encoded as a string that is
    understandable by ``Config`` objects.
    """
    if value is None:
        return ''
    if attribute in Config._BOOL_TYPE_ATTRIBUTES:
        if value:
            # If true, Config needs to receive only the
            # attribute name (defaults to True if specified).
            return attribute
        else:
            return f"{attribute}.{value}"
    elif attribute in ['default_ns', 'default_ew']:
        # Only need to specify 'n' or 's' to set default_ns; and 'e' or
        # 'w' for default_ew (i.e. 'default_ns.n' or 'default_ew.w' would
        # be redundant, as understood by Config objects.
        return value[0]
    else:
        return f"{attribute}.{value}"


def str_to_value(text):
    """
    INTERNAL USE:

    Convert string to None or bool or int, if appropriate. Otherwise,
    leave it as a string.
    """
    text = str(text)
    if text == 'None':
        return None
    elif text == 'True':
        return True
    elif text == 'False':
        return False
    else:
        try:
            return int(text)
        except ValueError:
            return text


def verify_default_ns(val):
    """
    INTERNAL USE:
    Verify whether a value is appropriate for ``default_ns``.  If so,
    return the first character, in lowercase; otherwise, raise a
    DefaultNSError.
    """
    if not isinstance(val, str) or val is None or not val:
        raise DefaultNSError
    first_char = val.lower()[0]
    if first_char not in MasterConfig._LEGAL_NS:
        raise DefaultNSError
    return first_char


def verify_default_ew(val):
    """
    INTERNAL USE:
    Verify whether a value is appropriate for ``default_ew``.  If so,
    return the first character, in lowercase; otherwise, raise a
    DefaultEWError.
    """
    if not isinstance(val, str) or val is None or not val:
        raise DefaultEWError
    first_char = val.lower()[0]
    if first_char not in MasterConfig._LEGAL_EW:
        raise DefaultEWError
    return first_char


__all__ = [
    'Config',
    'ConfigError',
]
