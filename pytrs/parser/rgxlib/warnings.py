
import re


# Pattern to look for possible wellbore exceptions.
well_regex = re.compile(r'(wellbore|well)', re.IGNORECASE)

# Pattern to look for possible depth limitations.
depth_regex = re.compile(r'(depth|formation|surf|down|form|top|base)', re.IGNORECASE)

# Pattern to look for possible 'including' language.
including_regex = re.compile(r'incl', re.IGNORECASE)

# Pattern to look for possible exceptions/limitations.
less_except_regex = re.compile(r'(less|except|limit)', re.IGNORECASE)

# Pattern to look for 'insofar' language.
isfa_regex = re.compile(r'(in\s?so\s?far)', re.IGNORECASE)
