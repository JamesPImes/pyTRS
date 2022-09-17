
"""
A class to configure parsing of individual PLSSDesc and Tract objects.
"""

import re

from .master_config import *
from ..plss_parse import _IMPLEMENTED_LAYOUTS

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

    All possible parameters (call ``pytrs.utils.config_parameters()`` for
    definitions) -- any unspecified parameters will fall back to
    default parsing behavior:
        -- 'n'  <or>  'default_ns.n'  vs.  's'  <or>  'default_ns.s'
        -- 'e'  <or>  'default_ew.e'  vs.  'w'  <or>  'default_ew.w'
        -- 'init_parse'  vs.  'init_parse.False'
        -- 'parse_qq'  vs.  'parse_qq.False'
        -- 'clean_qq'  vs.  'clean_qq.False'
        -- 'require_colon'  vs.  'require_colon.False'
        -- 'include_lot_divs'  vs.  'include_lot_divs.False'
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
        'include_lot_divs',
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
        'include_lot_divs',
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
        'include_lot_divs',
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
            ex: 'n,s,clean_qq,include_lot_divs.False'

        All possible parameters (call ``pytrs.utils.config_parameters()``
        for definitions) -- any unspecified parameters will fall back to
        default parsing behavior:
        -- 'n'  <or>  'default_ns.n'  vs.  's'  <or>  'default_ns.s'
        -- 'e'  <or>  'default_ew.e'  vs.  'w'  <or>  'default_ew.w'
        -- 'wait_to_parse'  vs.  'wait_to_parse.False'
        -- 'parse_qq'  vs.  'parse_qq.False'
        -- 'clean_qq'  vs.  'clean_qq.False'
        -- 'require_colon'  vs.  'require_colon.False'
        -- 'include_lot_divs'  vs.  'include_lot_divs.False'
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
        self.include_lot_divs = None
        self.ocr_scrub = None
        self.segment = None
        self.qq_depth = None
        self.qq_depth_min = None
        self.qq_depth_max = None
        self.break_halves = None

        # Remove all spaces from config_text:
        config_text = config_text.replace(' ', '')

        # Separate config parameters with ','  or  ';'
        config_lines = re.split(r'[;,]', config_text)

        # Parse each 'attrib.val' pair and commit to this Config object.
        for line in config_lines:

            if line == '':
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

    def __str__(self):
        return self.decompile_to_text()

    def __repr__(self):
        return f"Config<{self.decompile_to_text()!r}>"

    @staticmethod
    def from_parent(parent, config_name='', suppress_layout=False):
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

        config = Config()

        config.config_name = config_name
        if not suppress_layout:
            config.layout = getattr(parent, 'layout', None)
        else:
            config.layout = None
        config.init_parse = parent.init_parse
        config.parse_qq = parent.parse_qq
        config.clean_qq = parent.clean_qq
        config.default_ns = parent.default_ns
        config.default_ew = parent.default_ew
        config.include_lot_divs = parent.include_lot_divs

        return config

    def decompile_to_text(self) -> str:
        """
        Decompile a Config object into its equivalent string.
        """

        def write_val_as_text(att, val):
            if att in Config._BOOL_TYPE_ATTRIBUTES:
                if val is None:
                    return ""
                if val:
                    # If true, Config needs to receive only the
                    # attribute name (defaults to True if specified).
                    return att
                else:
                    return f"{att}.{val}"

            elif att in ['default_ns', 'default_ew']:
                if val is not None:
                    # Only need to specify 'n' or 's' to set default_ns; and
                    # 'e' or 'w' for default_ew (i.e. not 'default_ns.n' or
                    # 'default_ew.w'), so we return only `val`, and not `att`
                    return val
                else:
                    return ''
            elif val is None:
                return ''
            else:
                return f"{att}.{val}"

        write_vals = []
        for att in Config._CONFIG_ATTRIBUTES:
            w = write_val_as_text(att, getattr(self, att))
            if w:
                # Include only non-empty strings (i.e. config params
                # that were actually set)
                write_vals.append(w)

        return ','.join(write_vals)

    def _set_str_to_values(self, attrib_val, default_bool=None):
        """
        Take in a string of an attribute/value pair (in the format
        'attribute.value' or 'attribute=value') and set the appropriate
        value of the attribute.
        """

        def str_to_value(text):
            """
            Convert string to None or bool or int, if appropriate.
            """
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

        # split attribute/value pair by '.' or '='
        #   ex: 'default_ns.n' or 'default_ns=n' -> ['default_ns', 'n']
        comps = re.split(r'[\.=]', attrib_val)

        # Track whether only one component was found in the text with `only_one`:
        #   i.e. "init_parse." --> `only_one=True`
        #   but 'init_parse.True' --> `only_one=False`
        # (Both will set `self.init_parse` to `True` in this example, since it's
        # a bool-type config parameter)
        only_one = False
        if len(comps) != 2:
            only_one = True

        def decide_bool():
            """
            If only_one, return the default bool; otherwise, return
            the user-specified value from attrib_val.
            """
            if only_one:
                return default_bool
            else:
                return str_to_value(comps[1])

        if only_one and not isinstance(default_bool, bool):
            # If only one component, and default_bool was not entered as
            # a bool, return a failure value:
            return -1

        # Write values to the respective attributes. boolTypeAttribs
        # will specifically become bools:
        if comps[0] in Config._BOOL_TYPE_ATTRIBUTES:
            # If this is a bool-type attribute, set the value with decide_bool()
            setattr(self, comps[0], decide_bool())
            return 0
        elif comps[0] in ['default_ns', 'default_ew']:
            # Only writing the first letter of comps[1], in lowercase
            #   (i.e. 'North' --> 'n' or 'West' --> 'w'):
            setattr(self, comps[0], str_to_value(comps[1][0].lower()))
            return 0
        else:
            # Otherwise, set it however it's specified.
            setattr(self, comps[0], str_to_value(comps[1]))
            return 0


__all__ = [
    'Config',
    'ConfigError',
]
