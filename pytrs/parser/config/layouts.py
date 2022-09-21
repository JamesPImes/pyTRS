
"""
Constants showing the currently implemented layouts for PLSS
descriptions, with examples.
"""

# All current layouts
TRS_DESC = "TRS_desc"
DESC_STR = "desc_STR"
S_DESC_TR = "S_desc_TR"
TR_DESC_S = "TR_desc_S"
COPY_ALL = "copy_all"

# A tuple of all currently implemented layouts:
_IMPLEMENTED_LAYOUTS = (
    TRS_DESC,
    DESC_STR,
    S_DESC_TR,
    TR_DESC_S,
    COPY_ALL,
)

# The same tuple as a public-facing var
IMPLEMENTED_LAYOUTS = _IMPLEMENTED_LAYOUTS

IMPLEMENTED_LAYOUT_EXAMPLES = (
    "'TRS_desc'\n"
    "T154N-R97W\nSection 14: NE/4\n\n"
    "'desc_STR'\n"
    "NE/4 of Section 14, T154N-R97W\n\n"
    "'S_desc_TR'\n"
    "Section 14: NE/4, T154N-R97W\n\n"
    "'TR_desc_S'\n"
    "T154N-R97W\nNE/4 of Section 14\n\n"
    "'copy_all'\n"
    "Note: <copy_all> means that the entire text will be copied as the "
    "description, regardless of what the actual layout is."
)
