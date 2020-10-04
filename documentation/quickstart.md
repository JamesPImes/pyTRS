# pyTRS Quick Start Guide
*(__Note:__ This guide assumes that you are already familiar with the [PLSS](https://en.wikipedia.org/wiki/Public_Land_Survey_System) and its terminology.)*

## Bird's Eye View

The two primary parsing classes in the `pyTRS` library are [`PLSSDesc`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#creating-plssdesc-objects) and [`Tract`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#tract-objects).

The conceptual difference between these two classes is that a `Tract` object represents land within a single, specific section; whereas a `PLSSDesc` object can represent land across any number of sections (in a single township, or across multiple townships).

In practical terms, this means that, before any parsing has taken place, a `Tract` object has a description block that has been separated from its respective Twp/Rge/Section; whereas a `PLSSDesc` has all of the description/Twp/Rge/Sec as a single block of text.

[When a `PLSSDesc` object is parsed](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#parsing-plssdesc-objects-into-one-or-more-tract-objects), it will create one or more `Tract` objects -- i.e. it will break the full text down into Twp, Rge, Section, and the portion of the description that 'belongs to' that T/R/S combo (i.e. 'TRS').

[When a `Tract` object is parsed](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#parsing-tract-objects-into-lotsqqs), it does not create any new specialized objects. Instead, it parses its own description block (leaving it intact) to look for lots and QQs\*\*, which populate its `.lotList` and `.QQList` attributes (e.g., `'Lots 1 - 3, NE/4'` into lots `'L1'`, `'L2'`, and `'L3'`; and QQs `'NENE'`, `'NWNE'`, `'SENE'`, and `'SWNE'`).

`PLSSDesc` and `Tract` objects can both be [configured with `config=` parameters (or `Config` objects)](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#config-objects-and-config-parameters), and can both [generate warning and error flags](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#warning-and-error-flags-wflaglist-and-eflaglist-attributes) when parsed.

\*\* *(In the terminology of this module, `'QQ'` means an aliquot 'quarter-quarter' -- i.e. 1/16th of a standard section. For example, the Northeast Quarter of the Northeast Quarter, or `'NENE'`.)*

##### Abbreviation of Township/Range/Section in `pyTRS`

The combination of Township, Range, and Section are the minimum required identifier for a unique section of land, which is why the abbreviation `TRS` appears throughout this library (and in its name). In `pyTRS`', these components are always formatted as follows:

* `twp`: 1 to 3 digits + direction ('n' or 's') -- `Township 154 North` -> `'154n'`;  or `Township 1 South` -> `'1s'`

* `rge`: 1 to 3 digits + direction ('e' or 'w') -- `Range 97 West` -> `'97w'`;  or `Range 7 East` -> `'7e'`

* `sec`: Always 2 digits, with a leading `'0'` if necessary -- `Section 1` -> `'01'`

* `trs` -- The combination of `twp` + `rge` + `sec` ( i.e. the minimum required identifier for a unique section of land) -- `Section 1 of Township 154 North, Range 97 West` -> `'154n97w01'`

* `twprge` -- The combination of `twp` + `rge` ( i.e. the minimum required identifier for a unique township) -- `Township 154 North, Range 97 West` -> `'154n97w'`

*__Note:__ If there was a [flawed parse](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#warning-and-error-flags-wflaglist-and-eflaglist-attributes) where Township/Range or Section could not be successfully identified, `.trs` may contain `'TRerr_'` and/or `'secError'`.*

*__Note also:__ [Principal meridian](https://en.wikipedia.org/wiki/Principal_meridian) is mostly disregarded in this library, because they are so far apart that real-world ambiguity is rarely caused by their omission.*


## Quick notes on `layout` / example descriptions

The PLSS does not place strict limitations on the order in which the Township, Range, Section, and 'description block' must appear. Below are the different permutations (called `layout`) that can be handled by pyTRS:

**-- Township - Range - Section - Description** (i.e. `'TRS_desc'`)  *__Note:__ This layout need not be on multiple lines, but it often is.*
```
T154N-R97W
Section 14: NE/4
```

**-- Description - Section - Township - Range** (i.e. `'desc_STR'`)
```
NE/4 of Section 14, T154N-R97W
```

**-- Section - Description - Township - Range** (i.e. `'S_desc_TR'`)
```
Section 14: NE/4, T154N-R97W
```
**-- Township - Range - Description - Section** (i.e. `'TR_desc_S'`)
```
T154N-R97W
NE/4 of Section 14
```

pyTRS also has a stopgap layout (`'copy_all'`) which can be used to ensure that the text is maintained in the event that the layout cannot be successfully deduced (perhaps due to an omission or unrecognizable misspelling of section, township, or range).

Because the components can appear in varying order, a PLSS description will be parsed differently, which is why the concept of `layout` exists in this library at all.

In general, the parsing algorithm is capable of deducing the `layout` of the input data. However, the `layout` can also be dictated by the user ([via `config=` init parameter](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#config-objects-and-config-parameters)); although doing so is not recommended, unless you reliably know the layout of your dataset and want to capture errors very strictly.




#### Example description
The following description (or portions of it) will be used for examples in this quick-start guide (which is in the so-called `'TRS_desc'` layout):

```
Township 154 North, Range 97 West
Section 1: Lots 1 - 3 and the Southeast Quarter of the Northeast Quarter
Section 14: NE/4
Section 15: That portion of the W/2 lying south of the highway right-of-way
Township 155 North, Range 97 West
Section 22: ALL
```



## Creating `PLSSDesc` objects

PLSS descriptions are represented in pyTRS as `PLSSDesc` objects. The raw text of a PLSS description is passed as the first argument at init. (Optionally specify [`config=` parameters](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#config-objects-and-config-parameters) at init as well.)


```
import pyTRS

txt = '''Township 154 North, Range 97 West
Section 1: Lots 1 - 3 and the Southeast Quarter of the Northeast Quarter
Section 14: NE/4
Section 15: That portion of the W/2 lying south of the highway right-of-way
Township 155 North, Range 97 West
Section 22: ALL'''

# create a `PLSSDesc` object with this text (`config=` is optional).
d_obj = pyTRS.PLSSDesc(txt, config='n,w,segment')
```

### Parsing `PLSSDesc` objects into one or more `Tract` objects

#### Parse `PLSSDesc` objects with the `.parse()` method
(Continuing previous example)
```
d_obj.parse()

# Optionally, parse the resulting Tract objects into lots/QQs at the
# same time with `initParseQQ=True`
d_obj.parse(initParseQQ=True)
```

#### Parse `PLSSDesc` objects immediately at init, with `initParse=` and/or `initParseQQ=` parameters

Optionally trigger a `PLSSDesc` object to parse immediately upon init with parameter `initParse=True` and/or `initParseQQ=True`.

The only difference between these two options is that `initParseQQ=True` will cause every resulting `Tract` object to parse into lots and QQs, whereas `initParse=True` will not.

```
# immediately parse into Tracts, but do NOT parse the Tracts into lots/QQs:
d_obj_2 = pyTRS.PLSSDesc(txt, initParse=True, config='n,w,segment')

# immediately parse into Tracts, AND parse the Tracts into lots/QQs:
d_obj_3 = pyTRS.PLSSDesc(txt, initParseQQ=True, config='n,w,segment')


# Can already compile the parsed data:
parsed_data = d_obj_2.tracts_to_dict('trs', 'desc', 'lotList', 'QQList')
```


### Accessing parsed data inside a `PLSSDesc` object

More than likely, users will be most interested in the `Tract` objects that a `PLSSDesc` has been parsed into. There are [several methods for compiling all parsed data from the subordinate Tract objects (discussed below)](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#compiling-parsed-data-from-all-tract-objects-inside-a-plssdesc).

However, `PLSSDesc` objects also contain these instance variables, which can be accessed directly, as with any Python class.


* `.origDesc` -- The original text. (Gets set from the first positional argument at init.)

* [`.parsedTracts`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#directly-accessing-a-plssdesc-objects-parsed-tract-objects) -- A `pyTRS.TractList` object (i.e. a list) containing all of the pyTRS.Tract objects that were generated from parsing this object. \*\*

* `.ppDesc` -- The preprocessed description. (If the object has not yet been preprocessed, it will be equivalent to .origDesc)

* `.source` -- (Optional) A string specifying where the description came from. Useful if parsing multiple descriptions and need to internally keep track where they came from. (Optionally specify at init with parameter `source=<str>`.)

* [`.wFlagList`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#warning-and-error-flags-wflaglist-and-eflaglist-attributes) -- a list of warning flags (strings) generated during preprocessing and/or parsing.

* `.wFlagLines` -- a list of 2-tuples, each being a warning flag and the line or context from the description that caused the warning.

* [`.eFlagList`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#warning-and-error-flags-wflaglist-and-eflaglist-attributes) -- a list of error flags (strings) generated during preprocessing and/or parsing.

* `.eFlagLines` -- a list of 2-tuples, each being an error flag and the line or context from the description that caused the error.

* `.descIsFlawed` -- a bool, whether or not an apparently fatal flaw was discovered during parsing.

* [`.layout`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#quick-notes-on-layout--example-descriptions) -- The [user-dictated](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#config-objects-and-config-parameters) or algorithm-deduced [`layout`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#quick-notes-on-layout--example-descriptions) of the description (controls how the parsing algorithm interprets the text).


\*\* *__Note:__ `pyTRS.TractList` objects are beyond the scope of this quickstart guide. For most purposes, it's sufficient to know that it is a Python `list` that holds `pyTRS.Tract` objects. Any added functionality of a `TractList` can also be accomplished through an equivalent `PLSSDesc` method.*



#### Directly accessing a `PLSSDesc` object's parsed `Tract` objects
The `Tract` objects that are created via `PLSSDesc` parsing are stored in the `PLSSDesc` object's `.parsedTracts` attribute, which is a `pyTRS.TractList` object (a special class of `list` with additional functionality for compiling the `Tract` data).

```
# Accessing the first parsed Tract in the list:
sample_tract = d_obj_3.parsedTracts[0]
```



#### Compiling parsed data from all `Tract` objects inside a `PLSSDesc`

Each `Tract` object has [numerous instance attributes for the respective parsed data](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#tract-instance-variables). They are spelled out in more detail under the `Tract` portion of this quickstart guide, but for these examples, we'll pull these `Tract` attributes:

* `.trs` -- The Twp/Rge/Sec combo. Formatted such that Twp and Rge are 1 to 3 digits + direction, and section is 2 digits, and North/South and East/West are represented with the lowercase first letter. (ex: `Sec 1, T154N-R97W` -> `'154n97w01'`; or `Sec 14, T1S-R9E` -> `'1s9e14'`)

* `.twp` -- The Twp portion of .trs, a string (ex: `'154n'`)

* `.rge` -- The Rge portion of .trs, a string (ex: `'97w'`)

* `.sec` -- The Sec portion of .trs, a string (ex: `'01'`)

* `.desc` -- The description block within this TRS.

* `.QQList` -- A list of identified QQ's (or smaller)

* `.lotList` -- A list of identified lots.

In the following methods, specify which parsed data we want to extract from each parsed `Tract` by listing the attribute names (i.e. strings, without the leading period).



##### Print the parsed data to console with `.print_data()`
```
d_obj.print_data('twp', 'rge', 'sec', 'trs', 'desc', 'QQList', 'lotList')
```

... resulting in this printed to console:
```
Tract #1
twp     : 154n
rge     : 97w
sec     : 01
trs     : 154n97w01
desc    : Lots 1 - 3 and the Southeast Quarter of the Northeast Quarter
QQList  : SENE
lotList : L1, L2, L3

Tract #2
twp     : 154n
rge     : 97w
sec     : 14
trs     : 154n97w14
desc    : NE/4
QQList  : NENE, NWNE, SENE, SWNE
lotList : 

Tract #3
twp     : 154n
rge     : 97w
sec     : 15
trs     : 154n97w15
desc    : That portion of the W/2 lying south of the highway right-of-way
QQList  : NENW, NWNW, SENW, SWNW, NESW, NWSW, SESW, SWSW
lotList : 

Tract #4
twp     : 155n
rge     : 97w
sec     : 22
trs     : 155n97w22
desc    : ALL
QQList  : NENE, NWNE, SENE, SWNE, NENW, NWNW, SENW, SWNW, NESE, NWSE, SESE, SWSE, NESW, NWSW, SESW, SWSW
lotList : 
```



##### Compile the parsed data into dicts with `.tracts_to_dict()`:

(i.e. a list of dicts, with one dict per parsed `Tract`)

```
stored_data = d_obj.tracts_to_dict('twp', 'rge', 'sec', 'trs', 'desc', 'QQList', 'lotList')
```

Which looks like this (formatted with linebreaks here, just for better visual representation):
```
[
{'twp': '154n',
'rge': '97w',
'sec': '01',
'trs': '154n97w01',
'desc': 'Lots 1 - 3 and the Southeast Quarter of the Northeast Quarter',
'QQList': ['SENE'],
'lotList': ['L1', 'L2', 'L3']},

{'twp': '154n',
'rge': '97w',
'sec': '14',
'trs': '154n97w14',
'desc': 'NE/4',
'QQList': ['NENE', 'NWNE', 'SENE', 'SWNE'],
'lotList': []},

{'twp': '154n',
'rge': '97w',
'sec': '15',
'trs': '154n97w15',
'desc': 'That portion of the W/2 lying south of the highway right-of-way',
'QQList': ['NENW', 'NWNW', 'SENW', 'SWNW', 'NESW', 'NWSW', 'SESW', 'SWSW'],
'lotList': []},

{'twp': '155n',
'rge': '97w',
'sec': '22',
'trs': '155n97w22',
'desc': 'ALL',
'QQList': ['NENE', 'NWNE', 'SENE', 'SWNE', 'NENW', 'NWNW', 'SENW', 'SWNW', 'NESE', 'NWSE', 'SESE', 'SWSE', 'NESW', 'NWSW', 'SESW', 'SWSW'],
'lotList': []}
]
```


##### Compile the parsed data into a nested list with `.tracts_to_list()`:

```
stored_data =  d_obj.tracts_to_list('twp', 'rge', 'sec', 'trs', 'desc', 'QQList', 'lotList')
```
Which looks like this (again formatted with linebreaks for better visual representation):
```
[
['154n', '97w', '01', '154n97w01', 'Lots 1 - 3 and the Southeast Quarter of the Northeast Quarter', ['SENE'], ['L1', 'L2', 'L3']],

['154n', '97w', '14', '154n97w14', 'NE/4', ['NENE', 'NWNE', 'SENE', 'SWNE'], []],

['154n', '97w', '15', '154n97w15', 'That portion of the W/2 lying south of the highway right-of-way', ['NENW', 'NWNW', 'SENW', 'SWNW', 'NESW', 'NWSW', 'SESW', 'SWSW'], []],

['155n', '97w', '22', '155n97w22', 'ALL', ['NENE', 'NWNE', 'SENE', 'SWNE', 'NENW', 'NWNW', 'SENW', 'SWNW', 'NESE', 'NWSE', 'SESE', 'SWSE', 'NESW', 'NWSW', 'SESW', 'SWSW'], []
]
```


## `Tract` objects

If your dataset already has each respective description block separated from its Twp/Rge/Sec, you should create a `Tract` object directly (again [`config='cleanQQ'` or other parameters](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#config-objects-and-config-parameters) are optional):

```
import pyTRS

t_obj_1 = pyTRS.Tract(desc='NE/4', trs='154n97w14', config='cleanQQ')


# Alternative method, when your source of Twp/Rge/Sec are separate:
t_obj_2 = pyTRS.Tract.from_TwpRgeSec(desc='NE/4', twp='154n', rge='97w', sec=14, config='cleanQQ')
```


### Parsing `Tract` objects into lots/QQs

#### Parse `Tract` objects with the `.parse()` method

(Continuing previous example)

```
t_obj_1.parse()
```


#### Parse `Tract` objects immediately at init, with `initParseQQ=` parameter

Optionally trigger a `Tract` object to parse immediately upon init with parameter `initParseQQ=True`.

```
# immediately parse into lots/QQs (`config=` is optional):
t_obj_3 = pyTRS.Tract('NE/4', trs='154n97w14', initParseQQ=True, config='cleanQQ')


# Can already compile the parsed data:
parsed_data = t_obj_3.to_dict('trs', 'desc', 'lotList', 'QQList')
```


### Accessing parsed data inside a `Tract` object

#### `Tract` instance variables
Each `Tract` has these attributes, which can be accessed directly as necessary, or compiled with `.to_dict()`, `.to_list()`, or `.to_str()` methods (or compiled for multiple `Tract` objects using the `.tracts_to_dict()` and `.tracts_to_list()` methods via `PLSSDesc` object or `TractList` object).

* `.trs` -- The Twp/Rge/Sec combo. Formatted such that Twp and Rge are 1 to 3 digits + direction, and section is 2 digits, and North/South and East/West are represented with the lowercase first letter. (ex: `Sec 1, T154N-R97W` -> `'154n97w01'`; or `Sec 14, T1S-R9E` -> `'1s9e14'`)

* `.twp` -- The Twp portion of .trs, a string (ex: `'154n'`)

* `.rge` -- The Rge portion of .trs, a string (ex: `'97w'`)

* `.sec` -- The Sec portion of .trs, a string (ex: `'01'`)

* `.twprge` -- The Twp/Rge portion of .trs, a string (ex: `'154n97w'`)

* `.desc` -- The description block within this TRS. (Does not get changed via parsing.)

* `.QQList` -- A list of identified QQ's (or smaller) formatted as 4
    characters (or more, if there are further divisions) -- ex: `Northeast Quarter` -> `['NENE', 'NWNE', 'NENW', 'NWNW']`; or `N/2SE/4SE/4` -> `['N2SESE']`

* `.lotList` -- A list of identified lots. -- ex: `Lot 1, North Half of Lot 2` -> `['L1', 'N2 of L2']`

* `.lotQQList` -- A joined list of identified lots and QQ's -- ex: `['L1', 'N2 of L2', 'NENE', 'NWNE', 'NENW', 'NWNW']`

* `.lotAcres` -- A dict of lot names and their apparent gross acreages,
    as stated in the original description -- ex: `Lots 1(38.29), 2(39.22), 3(39.78)` -> `{'L1': '38.29', 'L2':'39.22', 'L3':'39.78'}`

* `.ppDesc` -- The preprocessed description. (If the object has not yet been preprocessed, it will be equivalent to `.desc`)

* `.source` -- (Optional) A string specifying where the description came from. Useful if parsing multiple descriptions and need to internally keep track where they came from. (Optionally specify at init with parameter `source=<str>`.)

* `.origDesc` -- The full, original text of the parent `PLSSDesc` object, if any. (Automatically filled in if the `Tract` object was created via `PLSSDesc` parsing, but can also be specified at init.)

* `.origIndex` -- An integer represeting the order in which this `Tract` object was created while parsing the parent `PLSSDesc` object (if applicable).

* [`.wFlagList`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#warning-and-error-flags-wflaglist-and-eflaglist-attributes) -- a list of warning flags (strings) generated during preprocessing and/or parsing.

* `.wFlagLines` -- a list of 2-tuples, each being a warning flag and the line or context from the description that caused the warning.

* [`.eFlagList`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#warning-and-error-flags-wflaglist-and-eflaglist-attributes) -- a list of error flags (strings) generated during preprocessing and/or parsing.

* `.eFlagLines` -- a list of 2-tuples, each being an error flag and the line or context from the description that caused the error.

* `.descIsFlawed` -- a bool, whether or not an apparently fatal flaw was discovered during parsing of the parent `PLSSDesc` object, if any. (`Tract` objects themselves are agnostic to fatal flaws.)

#### Compiling parsed data from a `Tract` object

In the following methods, specify which parsed data we want to extract from a parsed `Tract` by listing the attribute names (i.e. strings, without the leading period).



##### Get a string of the TRS + description block with `.quick_desc()`
```
parsed_txt = t_obj_1.quick_desc()
print(parsed_txt)
```

... resulting in this printed to console:
```
154n97w14: NE/4
```



##### Compile the parsed data into a dict with `.to_dict()`:

```
stored_data = t_obj_1.to_dict('twp', 'rge', 'sec', 'trs', 'desc', 'QQList', 'lotList')
```

Which looks like this (formatted with linebreaks here, just for better visual representation):
```
{'twp': '154n',
'rge': '97w',
'sec': '14',
'trs': '154n97w14',
'desc': 'NE/4',
'QQList': ['NENE', 'NWNE', 'SENE', 'SWNE'], 'lotList': []}
```


##### Compile the parsed data into a list with `.to_list()`:

```
stored_data =  t_obj_1.to_list('twp', 'rge', 'sec', 'trs', 'desc', 'QQList', 'lotList')
```
Which looks like this:
```
['154n', '97w', '14', '154n97w14', 'NE/4', ['NENE', 'NWNE', 'SENE', 'SWNE'], []]
```




## `Config` objects and `config=` parameters

The parsing of `PLSSDesc` and `Tract` objects is configured with `Config` objects (or equivalent `config=` parameters).

A full list of config options is provided in [`config parameters.txt`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/config%20parameters.txt), or can be printed to console by calling `pyTRS.utils.config_parameters()`.

If passing parameters to to `config=`, separate them with commas (spaces between are optional and have no effect).

```
import pyTRS

d_obj = pyTRS.PLSSDesc('T154N-R97W Sec 14: NE/4', config='n,w,cleanQQ')
t_obj = pyTRS.Tract('NE/4', trs='154n97w14', config='n,w,cleanQQ')
```

Equivalently, we can create a `Config` object (which takes the same parameter options), and pass that to `config=`.

```
import pyTRS

cf_1 = pyTRS.Config('n,w,cleanQQ')

d_obj = pyTRS.PLSSDesc('T154N-R97W Sec 14: NE/4', config=cf_1)
t_obj = pyTRS.Tract('NE/4', trs='154n97w14', config=cf_1)
```

Several config parameters have corresponding parameters in the `PLSSDesc.parse()` and/or `Tract.parse()` methods. For example, `'cleanQQ'` can be one of the `config=` parameters, and/or specified as `cleanQQ=True` when calling either `PLSSDesc.parse()` or `Tract.parse()`. Where `config=` parameters (passed at init) are later in conflict with a parameter in a `.parse()` method, the method will control.

```
# init with `cleanQQ` setting turned on
d_obj = pyTRS.PLSSDesc('T154N-R97W Sec 14: NE/4', config='cleanQQ')

# allow the init config to have effect
d_obj.parse()

# or, override the init config
d_obj.parse(cleanQQ=False)


# similarly:

# init with `cleanQQ` setting turned on
t_obj = pyTRS.Tract('NE/4', trs='154n97w14', config='cleanQQ')

# allow the init config to have effect
t_obj.parse()

# or, override the init config
t_obj.parse(cleanQQ=False)
```


## Warning and Error Flags (`.wFlagList` and `.eFlagList` attributes)

If the parsing algorithms are 'concerned' about something in the input, they can generate 'warning' flags for the user's attention, stored in the `.wFlagList` attribute of both `PLSSDesc` and `Tract` objects. For example, if a PLSS description apparently includes the same lot twice (flagged as `'dup_lot'`), it might mean that there was a typo in the original text -- and the algorithm 'suspects' that the parsed output __might not be__ as intended.

If the issues are serious enough, they are deemed 'error' flags, stored in the `.eFlagList` attribute of both `PLSSDesc` and `Tract` objects. For example, if no section or no Twp/Rge combo could be identified, then by definition, a required component is missing (or the parser could not recognize one of the required components), and the parsed output is __almost certainly not__ as intended.

A full list of flags that can be generated, and their definitions, can be found in `flags.html`. __[TODO: Link]__

__Important:__ The absense of a warning/error flag does not necessarily mean that the output is correct, so results should be examined for fidelity, regardless of flags.



##### `.wFlagList` example:

(Both `PLSSDesc` and `Tract` objects have a `.wFlagList` attribute.)

```
import pyTRS

# A Tract with duplicate lots
t_obj = pyTRS.Tract('Lots 1 - 3, SE/4NE/4, Lot 2', '154n97w01')
t_obj.parse()

print(t_obj.wFlagList)
```
...results in this, printed to console:
```
['dup_lot']
```



##### `.eFlagList` example:

(Both `PLSSDesc` and `Tract` objects have a `.eFlagList` attribute.)

```
import pyTRS

# Trying to parse a knowingly incomplete PLSS description (no township)
d_obj = pyTRS.PLSSDesc('-R97W Sec 14: NE/4')
d_obj.parse()

print(d_obj.eFlagList)
```
...results in this, printed to console:
```
['trError', 'noTR']
```

If we tried to print that parsed description...
```
print(d_obj.quick_desc())
```
...it looks like this:
```
'TRerr_14: -R97W Sec 14: NE/4'
```