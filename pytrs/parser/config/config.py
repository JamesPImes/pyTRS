
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
    A class to configure how PLSSDesc and Tract objects should be
    parsed.

    For a list of all parameter options, printed to console (must first
    import ``pytrs.utils``):
        ``pytrs.utils.config_parameters()``

    Or launch the Config GUI application (must first import
    ``pytrs.interface_tools``):
        ``pytrs.interface_tools.prompt_config()``

    For a guide to using Config objects general, printed to console
    (must first import ``pytrs.utils``):
        ``pytrs.utils.config_help()``

    All possible parameters (call ``pytrs.utils.config_parameters()``
    for definitions) -- any unspecified parameters will fall back to
    default parsing behavior:
        -- 'n'  <or>  'default_ns.n'  vs.  's'  <or>  'default_ns.s'
        -- 'e'  <or>  'default_ew.e'  vs.  'w'  <or>  'default_ew.w'
        -- 'parse_qq'  vs.  'parse_qq.False'
        -- 'clean_qq'  vs.  'clean_qq.False'
        -- 'require_colon'  vs.  'require_colon.False'
        -- 'suppress_lot_divs'  vs.  'suppress_lot_divs.False'
        -- 'ocr_scrub'  vs.  'ocr_scrub.False'
        -- 'segment'  vs.  'segment.False'
        -- 'qq_depth_min.<int>'  (defaults to 'qq_depth_min.2')
        -- 'qq_depth_max.<int>'  (defaults to 'qq_depth_max.None')
        -- 'qq_depth.<int>'  (defaults to 'qq_depth.None')
        -- 'break_halves'  vs.  'break_halves.False'
        Only one of the following may be passed -- and none of these are
        recommended:
        -- 'TRS_desc'  <or>  'layout.TRS_desc'
        -- 'desc_STR'  <or>  'layout.desc_STR'
        -- 'S_desc_TR'  <or>  'layout.S_desc_TR'
        -- 'TR_desc_S'  <or>  'layout.TR_desc_S'
        -- 'copy_all'  <or>  'layout.copy_all'
    """

    # Implemented settings that are settable via Config object:
    _CONFIG_ATTRIBUTES = (
        'default_ns',
        'default_ew',
        'layout',
        'wait_to_parse',
        'parse_qq',
        'clean_qq',
        'require_colon',
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
        'require_colon',
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

    def __init__(self, config_text=None, config_name=''):
        """
        Compile a Config object from a string ``config_text=``, with
        optional kwarg ``config_name=`` that does not affect parsing.

        Pass config parameters as a single string, with each parameter
        separated by comma. Spaces are optional and have no effect.
            ex: 'n,s,clean_qq,suppress_lot_divs.False'

        All possible parameters (call ``pytrs.utils.config_parameters()``
        for definitions) -- any unspecified parameters will fall back to
        default parsing behavior:
        -- 'n'  <or>  'default_ns.n'  vs.  's'  <or>  'default_ns.s'
        -- 'e'  <or>  'default_ew.e'  vs.  'w'  <or>  'default_ew.w'
        -- 'wait_to_parse'  vs.  'wait_to_parse.False'
        -- 'parse_qq'  vs.  'parse_qq.False'
        -- 'clean_qq'  vs.  'clean_qq.False'
        -- 'require_colon'  vs.  'require_colon.False'
        -- 'suppress_lot_divs'  vs.  'suppress_lot_divs.False'
        -- 'ocr_scrub'  vs.  'ocr_scrub.False'
        -- 'segment'  vs.  'segment.False'
        -- 'qq_depth_min.<int>'  (defaults to 'qq_depth_min.2')
        -- 'qq_depth_max.<int>'  (defaults to 'qq_depth_max.None')
        -- 'qq_depth.<int>'  (defaults to 'qq_depth.None')
        -- 'break_halves'  vs.  'break_halves.False'
        Only one of the following may be passed -- and none of these are
        recommended:
        -- 'TRS_desc'  <or>  'layout.TRS_desc'
        -- 'desc_STR'  <or>  'layout.desc_STR'
        -- 'S_desc_TR'  <or>  'layout.S_desc_TR'
        -- 'TR_desc_S'  <or>  'layout.TR_desc_S'
        -- 'copy_all'  <or>  'layout.copy_all'
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
        self.require_colon = None
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

    def text_to_attributes(self, config_text) -> None:
        """
        Convert the text into Config values and store them to the
        appropriate Config attributes.

        :param config_text: Standard Config text.
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

        :param parent: A ``PLSSDesc`` or ``Tract`` object whose config
        parameters should be compiled into this ``Config`` object.
        :param config_name: An optional string, being the name of this
        ``Config`` object.
        :param suppress_layout: Whether to include the ``.layout``
        attribute from the parent object. (Defaults to ``False``)
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
        :param kwargs:
        :param config_name: An optional string, being the name of this
        ``Config`` object.
        :return: A new ``Config``.
        """
        return cls.from_dict(kwargs, config_name)

    def decompile_to_text(self) -> str:
        """
        Decompile a Config object into its equivalent string.
        """
        write_vals = []
        for att in Config._CONFIG_ATTRIBUTES:
            w = attribute_value_to_str(att, getattr(self, att))
            if w:
                write_vals.append(w)
        return ','.join(write_vals)

    def _set_str_to_values(self, attrib_val, default_bool=None):
        """
        INTERNAL USE:

        Take in a string of an attribute/value pair (in the format
        'attribute.value' or 'attribute=value') and set the appropriate
        value of the attribute.
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


def attribute_value_to_str(attribute, value):
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
