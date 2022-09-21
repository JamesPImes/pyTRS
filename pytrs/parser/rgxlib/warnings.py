
"""
Regex patterns for generating warning flags.
"""

import re


# Possible wellbore exceptions.
well_regex = re.compile(r'\b(wellbore|well)\b', re.IGNORECASE)

# Possible depth limitations.
depth_regex = re.compile(
    r'(depths?|surf(ace)?|\bdown\b|form(ation)?|\btop\b|\bbase\b)',
    re.IGNORECASE)

# Possible 'including' language.
including_regex = re.compile(r'\bincl', re.IGNORECASE)

# Possible exceptions/limitations.
less_except_regex = re.compile(
    r'(\bless(\s*and\s*except)?|\bexcept|\blimit)', re.IGNORECASE)

# Look for 'insofar' language.
isfa_regex = re.compile(r'((but\s*)?only\s*)?(in\s*so\s*far)', re.IGNORECASE)
