
import re

# A regex for extra context around pp_twprge_no_nsr preprocessing
# (need to rule out "Lots" at the start of such a match):
lots_context_regex = re.compile(r'Lo?ts?|Lo?s?t', re.IGNORECASE)


