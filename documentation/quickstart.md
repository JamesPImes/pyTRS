# pyTRS Quick Start Guide
*(__Note:__ This guide assumes that you are already familiar with the [PLSS](https://en.wikipedia.org/wiki/Public_Land_Survey_System) and its terminology.)*

## Bird's Eye View

pyTRS is imported as `pytrs`.

The two primary parsing classes in the library are [`PLSSDesc`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#creating-plssdesc-objects) and [`Tract`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#tract-objects), which are automatically imported as top-level classes when importing `pytrs` (accessable as `pytrs.PLSSDesc` and `pytrs.Tract`, even though they are implemented as `pytrs.parser.parser.PLSSDesc` and `pytrs.parser.parser.Tract`).

The conceptual difference between these two classes is that a `Tract` object represents land within a single, specific section; whereas a `PLSSDesc` object can represent land across any number of sections (in a single township, or across multiple townships).

In practical terms, this means that, before any parsing has taken place, a `Tract` object has a description block that has been separated from its respective Twp/Rge/Section; whereas a `PLSSDesc` has all of the description/Twp/Rge/Sec as a single block of text.

[When a `PLSSDesc` object is parsed](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#parsing-plssdesc-objects-into-one-or-more-tract-objects), it will create one or more `Tract` objects -- i.e. it will break the full text down into Twp, Rge, Section, and the portion of the description that 'belongs to' that T/R/S combo (i.e. 'TRS').

[When a `Tract` object is parsed](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#parsing-tract-objects-into-lotsqqs), it does not create any new specialized objects. Instead, it parses its own description block (leaving it intact) to look for lots and QQs\*\*, which populate its `.lots` and `.qqs` attributes (e.g., `'Lots 1 - 3, NE/4'` into lots `'L1'`, `'L2'`, and `'L3'`; and QQs `'NENE'`, `'NWNE'`, `'SENE'`, and `'SWNE'`).

`PLSSDesc` and `Tract` objects can both be [configured with `config=` parameters (or `Config` objects)](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#config-objects-and-config-parameters), and can both [generate warning and error flags](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#warning-and-error-flags-w_flags-and-e_flags-attributes) when parsed.

\*\* *(In the terminology of this module, `'QQ'` means an aliquot 'quarter-quarter' -- i.e. 1/16th of a standard section. For example, the Northeast Quarter of the Northeast Quarter, or `'NENE'`. __The library can optionally parse into aliquots of different sizes by specifying [`qq_depth_min`, `qq_depth_max`, and/or `qq_depth`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#control-the-granularity-or-depth-of-aliquot-parsing-with-qq_depth-qq_depth_min-and/or-qq_depth_max).__)*


##### Abbreviation of Township/Range/Section in pyTRS

The combination of Township, Range, and Section are the minimum required identifier for a unique section of land, which is why the abbreviation `TRS` appears throughout this library (and in its name). In pyTRS, these components are always formatted as follows:

* `twp`: 1 to 3 digits + direction ('n' or 's') -- `Township 154 North` -> `'154n'`;  or `Township 1 South` -> `'1s'`

* `rge`: 1 to 3 digits + direction ('e' or 'w') -- `Range 97 West` -> `'97w'`;  or `Range 7 East` -> `'7e'`

* `sec`: Always 2 digits, with a leading `'0'` if necessary -- `Section 1` -> `'01'`

* `trs` -- The combination of `twp` + `rge` + `sec` ( i.e. the minimum required identifier for a unique section of land) -- `Section 1 of Township 154 North, Range 97 West` -> `'154n97w01'`

* `twprge` -- The combination of `twp` + `rge` ( i.e. the minimum required identifier for a unique township) -- `Township 154 North, Range 97 West` -> `'154n97w'`

*__Note:__ If there was a [flawed parse](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#warning-and-error-flags-w_flags-and-e_flags-attributes) where Township/Range or Section could not be successfully identified, `.trs` may contain `'TRerr_'` and/or `'secError'`.*

*__Note also:__ [Principal meridian](https://en.wikipedia.org/wiki/Principal_meridian) is mostly disregarded in this library, because they are so far apart that real-world ambiguity is rarely caused by their omission.*


## Quick notes on `layout` / example descriptions

The PLSS does not place strict limitations on the syntax of Township, Range, Section, and 'description block' -- i.e., they can appear in essentially any order. Below are the different permutations (called `layout`) that can be handled by pyTRS:

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
import pytrs

txt = '''Township 154 North, Range 97 West
Section 1: Lots 1 - 3 and the Southeast Quarter of the Northeast Quarter
Section 14: NE/4
Section 15: That portion of the W/2 lying south of the highway right-of-way
Township 155 North, Range 97 West
Section 22: ALL'''

# create a `PLSSDesc` object with this text (`config=` is optional).
d_obj = pytrs.PLSSDesc(txt, config='n,w,segment')
```

### Parsing `PLSSDesc` objects into one or more `Tract` objects

#### Parse `PLSSDesc` objects with the `.parse()` method
(Continuing previous example)
```
d_obj.parse()

# Optionally, parse the resulting Tract objects into lots/QQs at the
# same time with `init_parse_qq=True`
d_obj.parse(init_parse_qq=True)
```

#### Parse `PLSSDesc` objects immediately at init, with `init_parse=` and/or `init_parse_qq=` parameters

Optionally trigger a `PLSSDesc` object to parse immediately upon init with parameter `init_parse=True` and/or `init_parse_qq=True`.

The only difference between these two options is that `init_parse_qq=True` will cause every resulting `Tract` object to parse into lots and QQs, whereas `init_parse=True` will not.

```
# immediately parse into Tracts, but do NOT parse the Tracts into lots/QQs:
d_obj_2 = pytrs.PLSSDesc(txt, init_parse=True, config='n,w,segment')

# immediately parse into Tracts, AND parse the Tracts into lots/QQs:
d_obj_3 = pytrs.PLSSDesc(txt, init_parse_qq=True, config='n,w,segment')


# Can already compile the parsed data:
parsed_data = d_obj_2.tracts_to_dict('trs', 'desc', 'lots', 'qqs')
```


### Accessing parsed data inside a `PLSSDesc` object

More than likely, users will be most interested in the `Tract` objects that a `PLSSDesc` has been parsed into. There are [several methods for compiling all parsed data from the subordinate Tract objects (discussed below)](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#compiling-parsed-data-from-all-tract-objects-inside-a-plssdesc).

However, `PLSSDesc` objects also contain these instance variables, which can be accessed directly, as with any Python class.


* `.orig_desc` -- The original text. (Gets set from the first positional argument at init.)

* [`.parsed_tracts`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#directly-accessing-a-plssdesc-objects-parsed-tract-objects) -- A `pytrs.TractList` object (a subclass of `list`) containing all of the `pytrs.Tract` objects that were generated from parsing this object. \*\*

* `.pp_desc` -- The preprocessed description. (If the object has not yet been preprocessed, it will be equivalent to `.orig_desc`)

* `.source` -- (Optional) A string specifying where the description came from. Useful if parsing multiple descriptions and need to internally keep track where they came from. (Optionally specify at init with parameter `source=<str>`.)

* [`.w_flags`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#warning-and-error-flags-w_flags-and-e_flags-attributes) -- a list of warning flags (strings) generated during preprocessing and/or parsing.

* `.w_flag_lines` -- a list of 2-tuples, each being a warning flag and the line or context from the description that caused the warning.

* [`.e_flags`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#warning-and-error-flags-w_flags-and-e_flags-attributes) -- a list of error flags (strings) generated during preprocessing and/or parsing.

* `.e_flag_lines` -- a list of 2-tuples, each being an error flag and the line or context from the description that caused the error.

* `.desc_is_flawed` -- a bool, whether or not an apparently fatal flaw was discovered during parsing.

* [`.layout`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#quick-notes-on-layout--example-descriptions) -- The [user-dictated](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#config-objects-and-config-parameters) or algorithm-deduced [`layout`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#quick-notes-on-layout--example-descriptions) of the description (controls how the parsing algorithm interprets the text).


\*\* *__Note:__ `pytrs.TractList` objects are beyond the scope of this quickstart guide. For most purposes, it's sufficient to know that it is a subclass of the built-in `list` that holds `pytrs.Tract` objects. Any added functionality of a `TractList` can also be accomplished through an equivalent `PLSSDesc` method.*



#### Directly accessing a `PLSSDesc` object's parsed `Tract` objects
The `Tract` objects that are created via `PLSSDesc` parsing are stored in the `PLSSDesc` object's `.parsed_tracts` attribute, which is a `pytrs.TractList` object (a subclass of `list` with additional functionality for compiling the `Tract` data).

```
# Accessing the first parsed Tract in the list:
sample_tract = some_plssdesc.parsed_tracts[0]
```

`PLSSDesc` objects are also *__limitedly__* subscriptable, in that we can *__access__* the `Tract` objects stored in `.parsed_tracts` by subscripting the `PLSSDesc` object itself (with list indexes):

```
# equivalent to `some_plssdesc.parsed_tracts[0]`
sample_tract = some_plssdesc[0]

# equivalent to `some_plssdesc.parsed_tracts[:2]`
sliced_list_of_tracts = some_plssdesc[:2]

# equivalent to `for tract_obj in some_plssdesc.parsed_tracts: <...>`
for tract_obj in some_plssdesc:
    print(tract_obj.quick_desc())
```

But we *__cannot__* assign, `.pop()`, or `.insert()`. These will all cause errors:

```
>>> some_plssdesc[1] = pytrs.Tract(
...    desc='NE, NW', trs='154n97w14', init_parse_qq=True, config='clean_qq')
TypeError: 'PLSSDesc' object does not support item assignment

>>> tract_obj = some_plssdesc.pop(0)
AttributeError: 'PLSSDesc' object has no attribute 'pop'

>>> new_tract = pytrs.Tract(
...    desc='NE, NW', trs='154n97w14', init_parse_qq=True, config='clean_qq')
>>> some_plssdesc.insert(0, new_tract)
AttributeError: 'PLSSDesc' object has no attribute 'insert'
```

If (for some reason?) you needed that functionality, either access the `.parsed_tracts` attribute (a `pytrs.TractList` object):

```
>>> some_plssdesc.parsed_tracts[1] = pytrs.Tract(
...    desc='NE, NW', trs='154n97w14', init_parse_qq=True, config='clean_qq')

>>> tract_obj = some_plssdesc.parsed_tracts.pop(0)

>>> new_tract = pytrs.Tract(
...    desc='NE, NW', trs='154n97w14', init_parse_qq=True, config='clean_qq')
>>> some_plssdesc.parsed_tracts.insert(0, new_tract)
```

Or better yet, leave your `PLSSDesc` object intact and instead get a separate `pytrs.TractList` object by re-parsing (`commit=False` prevents the returned `TractList` from being stored to `.parsed_tracts` attribute):
```
>>> new_tractlist = some_plssdesc.parse(commit=False)
>>> popped_tract = new_tractlist.pop(0)
```


#### Compiling parsed data from all `Tract` objects inside a `PLSSDesc`

Each `Tract` object has [numerous instance attributes for the respective parsed data](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#tract-instance-variables). They are spelled out in more detail under the `Tract` portion of this quickstart guide, but for these examples, we'll pull these `Tract` attributes:

* `.trs` -- The Twp/Rge/Sec combo. Formatted such that Twp and Rge are 1 to 3 digits + direction, and section is 2 digits, and North/South and East/West are represented with the lowercase first letter. (ex: `Sec 1, T154N-R97W` -> `'154n97w01'`; or `Sec 14, T1S-R9E` -> `'1s9e14'`)

* `.twp` -- The Twp portion of .trs, a string (ex: `'154n'`)

* `.rge` -- The Rge portion of .trs, a string (ex: `'97w'`)

* `.sec` -- The Sec portion of .trs, a string (ex: `'01'`)

* `.desc` -- The description block within this TRS.

* `.qqs` -- A list of identified QQ's (or smaller)

* `.lots` -- A list of identified lots.

In the following methods, specify which parsed data we want to extract from each parsed `Tract` by listing the attribute names (i.e. strings, without the leading period).



##### Print the parsed data to console with `.print_data()`
```
d_obj.print_data('twp', 'rge', 'sec', 'trs', 'desc', 'qqs', 'lots')
```

... resulting in this printed to console:
```
Tract #1
twp  : 154n
rge  : 97w
sec  : 01
trs  : 154n97w01
desc : Lots 1 - 3 and the Southeast Quarter of the Northeast Quarter
qqs  : SENE
lots : L1, L2, L3

Tract #2
twp  : 154n
rge  : 97w
sec  : 14
trs  : 154n97w14
desc : NE/4
qqs  : NENE, NWNE, SENE, SWNE
lots : 

Tract #3
twp  : 154n
rge  : 97w
sec  : 15
trs  : 154n97w15
desc : That portion of the W/2 lying south of the highway right-of-way
qqs  : NENW, NWNW, SENW, SWNW, NESW, NWSW, SESW, SWSW
lots : 

Tract #4
twp  : 155n
rge  : 97w
sec  : 22
trs  : 155n97w22
desc : ALL
qqs  : NENE, NWNE, SENE, SWNE, NENW, NWNW, SENW, SWNW, NESE, NWSE, SESE, SWSE, NESW, NWSW, SESW, SWSW
lots : 
```



##### Compile the parsed data into dicts with `.tracts_to_dict()`:

(i.e. a list of dicts, with one dict per parsed `Tract`)

```
stored_data = d_obj.tracts_to_dict('twp', 'rge', 'sec', 'trs', 'desc', 'qqs', 'lots')
```

Which looks like this (formatted with linebreaks here, just for better visual representation):
```
[
{'twp': '154n',
'rge': '97w',
'sec': '01',
'trs': '154n97w01',
'desc': 'Lots 1 - 3 and the Southeast Quarter of the Northeast Quarter',
'qqs': ['SENE'],
'lots': ['L1', 'L2', 'L3']},

{'twp': '154n',
'rge': '97w',
'sec': '14',
'trs': '154n97w14',
'desc': 'NE/4',
'qqs': ['NENE', 'NWNE', 'SENE', 'SWNE'],
'lots': []},

{'twp': '154n',
'rge': '97w',
'sec': '15',
'trs': '154n97w15',
'desc': 'That portion of the W/2 lying south of the highway right-of-way',
'qqs': ['NENW', 'NWNW', 'SENW', 'SWNW', 'NESW', 'NWSW', 'SESW', 'SWSW'],
'lots': []},

{'twp': '155n',
'rge': '97w',
'sec': '22',
'trs': '155n97w22',
'desc': 'ALL',
'qqs': ['NENE', 'NWNE', 'SENE', 'SWNE', 'NENW', 'NWNW', 'SENW', 'SWNW', 'NESE', 'NWSE', 'SESE', 'SWSE', 'NESW', 'NWSW', 'SESW', 'SWSW'],
'lots': []}
]
```


##### Compile the parsed data into a nested list with `.tracts_to_list()`:

```
stored_data =  d_obj.tracts_to_list('twp', 'rge', 'sec', 'trs', 'desc', 'qqs', 'lots')
```
Which looks like this (again formatted with linebreaks for better visual representation):
```
[
['154n', '97w', '01', '154n97w01', 'Lots 1 - 3 and the Southeast Quarter of the Northeast Quarter', ['SENE'], ['L1', 'L2', 'L3']],

['154n', '97w', '14', '154n97w14', 'NE/4', ['NENE', 'NWNE', 'SENE', 'SWNE'], []],

['154n', '97w', '15', '154n97w15', 'That portion of the W/2 lying south of the highway right-of-way', ['NENW', 'NWNW', 'SENW', 'SWNW', 'NESW', 'NWSW', 'SESW', 'SWSW'], []],

['155n', '97w', '22', '155n97w22', 'ALL', ['NENE', 'NWNE', 'SENE', 'SWNE', 'NENW', 'NWNW', 'SENW', 'SWNW', 'NESE', 'NWSE', 'SESE', 'SWSE', 'NESW', 'NWSW', 'SESW', 'SWSW'], []]
]
```


## `Tract` objects

If your dataset already has each respective description block separated from its Twp/Rge/Sec, you should create a `Tract` object directly (again [`config='clean_qq'` or other parameters](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#config-objects-and-config-parameters) are optional):

```
import pytrs

t_obj_1 = pytrs.Tract(desc='NE/4', trs='154n97w14', config='clean_qq')


# Alternative method, when your source of Twp/Rge/Sec are separate:
t_obj_2 = pytrs.Tract.from_twprgesec(desc='NE/4', twp='154n', rge='97w', sec=14, config='clean_qq')
```


### Parsing `Tract` objects into lots/QQs

#### Parse `Tract` objects with the `.parse()` method

(Continuing previous example)

```
t_obj_1.parse()
```


#### Parse `Tract` objects immediately at init, with `init_parse_qq=` parameter

Optionally trigger a `Tract` object to parse immediately upon init with parameter `init_parse_qq=True`.

```
# immediately parse into lots/QQs (`config=` is optional):
t_obj_3 = pytrs.Tract('NE/4', trs='154n97w14', init_parse_qq=True, config='clean_qq')


# Can already compile the parsed data:
parsed_data = t_obj_3.to_dict('trs', 'desc', 'lots', 'qqs')
```


#### Control the granularity (or 'depth') of aliquot parsing with `qq_depth`, `qq_depth_min`, and/or `qq_depth_max`

By default, aliquots will be parsed into quarter-quarters ('QQs', or traditional 40-acre divisions), but will *__allow__* smaller divisions if they exist in the data. In this example, the `'SE/4NW/4'` describes a 40-acre division (already a QQ) whereas `'E/2NE/4NW/4'` describes a 20-acre parcel (being half of a QQ):

```
>>> tract_demo_default = pytrs.Tract(
        desc="SE/4NW/4, E/2NE/4NW/4",
        trs="154n97w14")
>>> tract_demo_default.parse()
>>> print(tract_demo_default.qqs)
['SENW', 'E2NENW']
```


##### `qq_depth_min`

If we want to *__force__* divisions smaller than 40 acres, we can set the config parameter `'qq_depth_min.<number>'`, where `<number>` specifies how many times to divide the section by 4. That is, the section will be divided into a number of pieces equal to `4^(depth)`.

The default is `'qq_depth_min.2'` (i.e. 16 quarter-quarters). But we can break it into 64 pieces (each 10-acres, assuming a 'perfect' section) with `qq_depth_min.3`, thus: 

```
>>> tract_demo_min = pytrs.Tract(
        desc="SE/4NW/4, E/2NE/4NW/4",
        trs="154n97w14",
        config="qq_depth_min.3")
>>> tract_demo_min.parse()
>>> print(tract_demo_min.qqs)
['NESENW', 'NWSENW', 'SESENW', 'SWSENW', 'NENENW', 'SENENW']
```

...Equivalently, as a kwarg in `.parse()` (which would override whatever was specified in `config=`, if any):
```
>>> tract_demo_min = pytrs.Tract(
        desc="SE/4NW/4, E/2NE/4NW/4",
        trs="154n97w14")
>>> tract_demo_min.parse(qq_depth_min=3)
```


##### `qq_depth_max`

If we want to *__prohibit__* (i.e. discard) divisions smaller than 40 acres, we can use the config parameter `'qq_depth_max.<number>'`, which works similarly. This will discard any divisions smaller than the specified depth. In this example, the `'E/2NE/4NW/4'` gets parsed as the `'NENW'`, thus:

```
>>> tract_demo_max = pytrs.Tract(
        desc="SE/4NW/4, E/2NE/4NW/4",
        trs="154n97w14",
        config="qq_depth_max.2")
>>> tract_demo_max.parse()
>>> print(tract_demo_max.qqs)
['SENW', 'NENW']
```

*__WARNING__: `qq_depth_max` should be equal to or greater than `qq_depth_min`, or there will likely be more parsed QQs than actually exist in the data.*

...Equivalently, as a kwarg in `.parse()` (which would override whatever was specified in `config=`, if any):
```
>>> tract_demo_max = pytrs.Tract(
        desc="SE/4NW/4, E/2NE/4NW/4",
        trs="154n97w14")
>>> tract_demo_min.parse(qq_depth_max=2)
```


##### `qq_depth` (i.e. exact QQ depth)

If we want to specify the *__exact__* size of *__every__* element, no bigger and no smaller, we can use the config parameter `'qq_depth.<number>'`, which is equivalent to setting `qq_depth_min` and `qq_depth_max` to the same number (which is how it is implemented behind the scenes).

```
>>> tract_demo_exact = pytrs.Tract(
        desc="SE/4NW/4, E/2NE/4NW/4",
        trs="154n97w14",
        config="qq_depth.2")
>>> tract_demo_exact.parse()
>>> print(tract_demo_exact.qqs)
['SENW', 'NENW']
```

...Equivalently, as a kwarg in `.parse()` (which would override whatever was specified in `config=`, if any):
```
>>> tract_demo_min = pytrs.Tract(
        desc="SE/4NW/4, E/2NE/4NW/4",
        trs="154n97w14")
>>> tract_demo_min.parse(qq_depth=2)
```

*__Note__: If specified, `qq_depth` will override `qq_depth_min` and `qq_depth_max`.* 



##### Warning: Do not set `qq_depth_min` or `qq_depth` too high.

Because we're dealing with powers of 4, setting `qq_depth_min` or `qq_depth` to a value higher than 3 or 4 will quickly become very computationally expensive. `'ALL of Section 14, T154N-R97W'` parsed to a `qq_depth` of 5 will return a list of 1024 aliquot pieces, each 0.625 acres in size. And to a depth of 6 will return a list of 4096 aliquot pieces (each 0.15625 acres in size).



### Accessing parsed data inside a `Tract` object

#### `Tract` instance variables
Each `Tract` has these attributes, which can be accessed directly as necessary, or compiled with `.to_dict()`, `.to_list()`, or `.to_str()` methods (or compiled for multiple `Tract` objects using the `.tracts_to_dict()` and `.tracts_to_list()` methods via `PLSSDesc` object or `TractList` object).

* `.trs` -- The Twp/Rge/Sec combo. Formatted such that Twp and Rge are 1 to 3 digits + direction, and section is 2 digits, and North/South and East/West are represented with the lowercase first letter. (ex: `Sec 1, T154N-R97W` -> `'154n97w01'`; or `Sec 14, T1S-R9E` -> `'1s9e14'`)

* `.twp` -- The Twp portion of .trs, a string (ex: `'154n'`)

* `.rge` -- The Rge portion of .trs, a string (ex: `'97w'`)

* `.sec` -- The Sec portion of .trs, a string (ex: `'01'`)

* `.twprge` -- The Twp/Rge portion of `.trs`, a string (ex: `'154n97w'`)

* `.desc` -- The description block within this TRS. (Does not get changed via parsing.)

* `.qqs` -- A list of identified QQ's (or smaller) formatted as 4
    characters (or more, if there are further divisions) -- ex: `'Northeast Quarter'` -> `['NENE', 'NWNE', 'NENW', 'NWNW']`; or `N/2SE/4SE/4` -> `['N2SESE']`

* `.lots` -- A list of identified lots. -- ex: `'Lot 1, North Half of Lot 2'` -> `['L1', 'N2 of L2']`

* `.lots_qqs` -- A joined list of identified lots and QQ's -- ex: `['L1', 'N2 of L2', 'NENE', 'NWNE', 'NENW', 'NWNW']`

* `.lot_acres` -- A dict of lot names and their apparent gross acreages,
    as stated in the original description -- ex: `Lots 1(38.29), 2(39.22), 3(39.78)` -> `{'L1': '38.29', 'L2':'39.22', 'L3':'39.78'}`

* `.pp_desc` -- The preprocessed description. (If the object has not yet been preprocessed, it will be equivalent to `.desc`)

* `.source` -- (Optional) A string specifying where the description came from. Useful if parsing multiple descriptions and need to internally keep track where they came from. (Optionally specify at init with parameter `source=<str>`.)

* `.orig_desc` -- The full, original text of the parent `PLSSDesc` object, if any. (Automatically filled in if the `Tract` object was created via `PLSSDesc` parsing, but can also be specified at init.)

* `.orig_index` -- An integer representing the order in which this `Tract` object was created while parsing the parent `PLSSDesc` object (if applicable).

* [`.w_flags`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#warning-and-error-flags-w_flags-and-e_flags-attributes) -- a list of warning flags (strings) generated during preprocessing and/or parsing.

* `.w_flag_lines` -- a list of 2-tuples, each being a warning flag and the line or context from the description that caused the warning.

* [`.e_flags`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/quickstart.md#warning-and-error-flags-w_flags-and-e_flags-attributes) -- a list of error flags (strings) generated during preprocessing and/or parsing.

* `.e_flag_lines` -- a list of 2-tuples, each being an error flag and the line or context from the description that caused the error.

* `.desc_is_flawed` -- a bool, whether or not an apparently fatal flaw was discovered during parsing of the parent `PLSSDesc` object, if any. (`Tract` objects themselves are agnostic to fatal flaws.)

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
stored_data = t_obj_1.to_dict('twp', 'rge', 'sec', 'trs', 'desc', 'qqs', 'lots')
```

Which looks like this (formatted with linebreaks here, just for better visual representation):
```
{
    'twp': '154n',
    'rge': '97w',
    'sec': '14',
    'trs': '154n97w14',
    'desc': 'NE/4',
    'qqs': ['NENE', 'NWNE', 'SENE', 'SWNE'],
    'lots': []
}
```


##### Compile the parsed data into a list with `.to_list()`:

```
stored_data =  t_obj_1.to_list('twp', 'rge', 'sec', 'trs', 'desc', 'qqs', 'lots')
```
Which looks like this:
```
['154n', '97w', '14', '154n97w14', 'NE/4', ['NENE', 'NWNE', 'SENE', 'SWNE'], []]
```




## `Config` objects and `config=` parameters

The parsing of `PLSSDesc` and `Tract` objects is configured with `Config` objects (or equivalent `config=` parameters).

A full list of config options is provided in [`config parameters.txt`](https://github.com/JamesPImes/pyTRS/blob/master/documentation/config%20parameters.txt), or can be printed to console by importing `pytrs.utils` and calling `pytrs.utils.config_parameters()`.

If passing parameters to to `config=`, separate them with commas (spaces between are optional and have no effect).

```
import pytrs

d_obj = pytrs.PLSSDesc('T154N-R97W Sec 14: NE/4', config='n,w,clean_qq')
t_obj = pytrs.Tract('NE/4', trs='154n97w14', config='n,w,clean_qq')
```

Equivalently, we can create a `Config` object (which takes the same parameter options), and pass that to `config=`.

```
import pytrs

cf_1 = pytrs.Config('n,w,clean_qq')

d_obj = pytrs.PLSSDesc('T154N-R97W Sec 14: NE/4', config=cf_1)
t_obj = pytrs.Tract('NE/4', trs='154n97w14', config=cf_1)
```

Several config parameters have corresponding parameters in the `PLSSDesc.parse()` and/or `Tract.parse()` methods. For example, `'clean_qq'` can be one of the `config=` parameters, and/or specified as `clean_qq=True` when calling either `PLSSDesc.parse()` or `Tract.parse()`. Where `config=` parameters (passed at init) are later in conflict with a parameter in a `.parse()` method, the method will control.

```
# init with `clean_qq` setting turned on
d_obj = pytrs.PLSSDesc('T154N-R97W Sec 14: NE/4', config='clean_qq')

# allow the init config to have effect
d_obj.parse()

# or, override the init config
d_obj.parse(clean_qq=False)


# similarly:

# init with `clean_qq` setting turned on
t_obj = pytrs.Tract('NE/4', trs='154n97w14', config='clean_qq')

# allow the init config to have effect
t_obj.parse()

# or, override the init config
t_obj.parse(clean_qq=False)
```


## Warning and Error Flags (`.w_flags` and `.e_flags` attributes)

If the parsing algorithms are 'concerned' about something in the input, they can generate 'warning' flags for the user's attention, stored in the `.w_flags` attribute of both `PLSSDesc` and `Tract` objects. For example, if a PLSS description apparently includes the same lot twice (flagged as `'dup_lot'`), it might mean that there was a typo in the original text -- and the algorithm 'suspects' that the parsed output __might not be__ as intended.

If the issues are serious enough, they are deemed 'error' flags, stored in the `.e_flags` attribute of both `PLSSDesc` and `Tract` objects. For example, if no section or no Twp/Rge combo could be identified, then by definition, a required component is missing (or the parser could not recognize one of the required components), and the parsed output is __almost certainly not__ as intended.

A full list of flags that can be generated, and their definitions, can be found in `flags.html`. __[TODO: Link]__

__Important:__ The absense of a warning/error flag does not necessarily mean that the output is correct, so results should be examined for fidelity, regardless of flags.



##### `.w_flags` example:

(Both `PLSSDesc` and `Tract` objects have a `.w_flags` attribute.)

```
import pytrs

# A Tract with duplicate lots
t_obj = pytrs.Tract(desc='Lots 1 - 3, SE/4NE/4, Lot 2', trs='154n97w01')
t_obj.parse()

print(t_obj.w_flags)
```
...results in this, printed to console:
```
['dup_lot']
```



##### `.e_flags` example:

(Both `PLSSDesc` and `Tract` objects have a `.e_flags` attribute.)

```
import pytrs

# Trying to parse a knowingly incomplete PLSS description (no township)
d_obj = pytrs.PLSSDesc('-R97W Sec 14: NE/4')
d_obj.parse()

print(d_obj.e_flags)
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