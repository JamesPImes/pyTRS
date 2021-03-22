
# Guide to extracting data in bulk from parsed objects

`Tract` objects have methods for extracting parsed data from themselves individually. [# TODO: LINK TO TRACT.MD]

But `PLSSDesc` and `TractList` objects contain methods to extract data from multiple `Tract` objects all at once--or for grouping / filtering / sorting `Tract` objects based on their attributes. This can be useful for compiling a spreadsheet, or for finding tracts that match some specific condition.

(For a guide to the various useful `Tract` attributes, see this table.)  [# TODO: LINK TO TRACT.MD ATTRIBUTE TABLE]


## Extracting data from individual `Tract` objects

To extract data from individual `Tract` objects, use these methods.

#### To a dict with `.to_dict()`

Pass a list of the names of attributes we want to collect in a dict:
```
tract = pytrs.Tract('Lots 1 - 3, NE/4', trs='154n97w14', parse_qq=True)
tract_data = tract.to_dict(['trs', 'desc', 'lots', 'qqs'])
```
The dict stored to variable `tract_data` contains these values:
```
{
    'trs': '154n97w14',
    'desc': 'Lots 1 - 3, NE/4',
    'lots': ['L1', 'L2', 'L3'],
    'qqs': ['NENE', 'NWNE', 'SENE', 'SWNE']
}
```

#### To a list with `.to_list()`

Pass a list of the names of attributes we want to collect in a list:
```
tract = pytrs.Tract('Lots 1 - 3, NE/4', trs='154n97w14', parse_qq=True)
tract_data = tract.to_list(['trs', 'desc', 'lots', 'qqs'])
```
The list stored to variable `tract_data` contains these values:
```
[
    '154n97w14',
    'Lots 1 - 3, NE/4',
    ['L1', 'L2', 'L3'],
    ['NENE', 'NWNE', 'SENE', 'SWNE']
]
```


## Extracting data from `Tract` objects in bulk

`PLSSDesc` objects and `TractList` objects both have equivalent methods for extracting `Tract` data (and sorting / filtering / grouping).

When a method is called by a `PLSSDesc` object, it will operate on the `Tract` objects stored in its own `.parsed_tracts` attribute (i.e. the `Tract` objects generated when it was parsed).
 
 On the other hand, a `TractList` object might contain `Tract` objects from any number of sources. Examples below show a `TractList` that holds the `Tract` objects from a single source, but we can add any number of them from any number of objects. See the guide on `TractList` objects for how to collect `Tract` objects from multiple sources. [# TODO: LINK TO TRACTLIST.MD]

*(See also the specialized csv writer class included as `pytrs.tractwriter.TractWriter`.)*  [# TODO: LINK TO TRACTWRITER]

#### Compile `Tract` attributes to dicts with `.tracts_to_dict()`

Use this to get a list of dicts (one dict per `Tract`). Pass a list of the names of attributes we want to collect in each dict.

```
raw_description = """T154N-R97W
Sec 14: NE/4
Sec 15: Lots 1 - 3, S/2SW/4"""

parsed_plssdesc = pytrs.PLSSDesc(raw_description, parse_qq=True)
all_tract_data = parsed_plssdesc.tracts_to_dict(['trs', 'desc', 'lots', 'qqs'])

# Equivalently with a TractList:
some_tractlist = pytrs.TractList.from_multiple([parsed_plssdesc])
all_tract_data = some_tractlist.tracts_to_dict(['trs', 'desc', 'lots', 'qqs'])
```

A list of dicts has been stored to variable `all_tract_data` (one dict for each `Tract`):
```
[
    {
        'trs': '154n97w14',
        'desc': 'NE/4',
        'lots': [],
        'qqs': ['NENE', 'NWNE', 'SENE', 'SWNE']
    },

    {
        'trs': '154n97w15',
        'desc': 'Lots 1 - 3, S/2SW/4',
        'lots': ['L1', 'L2', 'L3'],
        'qqs': ['SESW', 'SWSW']
    }
]
```

#### Compile `Tract` attributes to a list of lists with `.tracts_to_list()`

Use this to get a nested list of lists (one list per `Tract`). Pass a list of the names of attributes we want to collect.

```
raw_description = """T154N-R97W
Sec 14: NE/4
Sec 15: Lots 1 - 3, S/2SW/4"""

parsed_plssdesc = pytrs.PLSSDesc(raw_description, parse_qq=True)
all_tract_data = parsed_plssdesc.tracts_to_list(['trs', 'desc', 'lots', 'qqs'])

# Equivalently with a TractList:
some_tractlist = pytrs.TractList.from_multiple([parsed_plssdesc])
all_tract_data = some_tractlist.tracts_to_list(['trs', 'desc', 'lots', 'qqs'])
```

A list of lists has been stored to variable `all_tract_data` (one list for each `Tract`):
```
[
    ['154n97w14', 'NE/4', [], ['NENE', 'NWNE', 'SENE', 'SWNE']],
    ['154n97w15', 'Lots 1 - 3, S/2SW/4', ['L1', 'L2', 'L3'], ['SESW', 'SWSW']]
]
```

#### Write `Tract` attributes to a .csv file with `.tracts_to_csv()`

*(Note: A more robust csv writer class is included as `pytrs.tractwriter.TractWriter`. But this method is simpler, if we just need to dump the data to a csv.)*

Use this to write data to a .csv file (one row per `Tract`).

```
raw_description = """T154N-R97W
Sec 14: NE/4
Sec 15: Lots 1 - 3, S/2SW/4"""

parsed_plssdesc = pytrs.PLSSDesc(raw_description, parse_qq=True)
all_tract_data = parsed_plssdesc.tracts_to_csv(
    attributes=['trs', 'desc', 'lots', 'qqs'],
    fp=<some path>,
    mode='w',
    nice_headers=True)

# Equivalently with a TractList:
some_tractlist = pytrs.TractList.from_multiple([parsed_plssdesc])
all_tract_data = some_tractlist.tracts_to_csv(
    attributes=['trs', 'desc', 'lots', 'qqs'],
    fp=<some path>,
    mode='w',
    nice_headers=True)
```

|Parameter              | Explanation                                                          |Footnote |
|:----------------------|:---------------------------------------------------------------------|:-------:|
|`attributes=<list>`| a list of names of the attributes to include|
|`fp=<path>`| The filepath of the .csv file to write to.|
|`mode=<'w' or 'a'>`| The mode to open the file in (either `'w'` or `'a'`)| 1|
|`nice_headers=<bool, list, or dict>`| use custom headers (see footnote) | 2 |

1) `mode` serves the same purpose as it does in the builtin `open()` function. Here, it defaults to `'w'` (a new file, and overwriting any file already at that path). Use mode `'a'` to add this data to an existing .csv file.

2) `nice_headers` defaults to `False` (i.e. just use the attribute names themselves as headers). Alternatively, may pass any of the following:

* a dict keyed by attribute name, whose values are the headers to use. (Any missing keys will result in using the attribute name itself.)

* a list of headers to use. (Should be equal in length to the list passed as ``attributes``, but will not raise an error if that's not the case. The resulting column headers will just be fewer than the actual number of columns.)

* pass as `True` to use the values in the `Tract.ATTRIBUTES` dict for headers. *(__Warning:__ Any value passed that is not a list or dict and that evaluates to `True` will cause this behavior.)*



#### Print `Tract` attributes to console with `.print_data()`

If you just need to quickly check the data, you can print it to console. 

```
>>> raw_description = """T154N-R97W
Sec 14: NE/4
Sec 15: Lots 1 - 3, S/2SW/4"""

>>> parsed_plssdesc = pytrs.PLSSDesc(raw_description, parse_qq=True)
>>> parsed_plssdesc.print_data(['trs', 'desc', 'lots', 'qqs'])
```
The above example prints this to console:
```
Tract 1 / 2
trs  : 154n97w14
desc : NE/4
lots : 
qqs  : NENE, NWNE, SENE, SWNE

Tract 2 / 2
trs  : 154n97w15
desc : Lots 1 - 3, S/2SW/4
lots : L1, L2, L3
qqs  : SESW, SWSW
```

Equivalently with a TractList:
```
>>> raw_description = """T154N-R97W
Sec 14: NE/4
Sec 15: Lots 1 - 3, S/2SW/4"""

>>> parsed_plssdesc = pytrs.PLSSDesc(raw_description, parse_qq=True)
>>> some_tractlist = pytrs.TractList.from_multiple([parsed_plssdesc])
>>> some_tractlist.print_data(['trs', 'desc', 'lots', 'qqs'])
```

## Grouping / Filtering / Sorting `Tract` objects in a `TractList` or `PLSSDesc`

### `.sort_tracts()`

Sort the `Tract` objects stored in this `TractList` (in place), with optional custom sort keys (see below).

First, `sort_key=<lambda>` and `reverse=<bool>` parameters can be used here -- identical in behavior to the built-in `list.sort(key=<lambda>, reverse=<bool>)`, but note the parameter name here is `sort_key`, rather than `key`. (This is named `sort_key` because it is also a parameter in [the grouping methods](), and it serves the same purpose there.) [#TODO: LINK]

```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])

# Sort by the number of aliquots identified in each Tract (most-to-least).
t_list.sort_tracts(sort_key=lambda tract: len(tract.qqs), reverse=True)
```

#### Custom sorting by Twp/Rge/Sec (and creation order):

The `.sort_tracts()` method has additional customized key options for sorting operations that are commonly needed for tracts, and which would be onerous to implement every time (e.g., by Township number, from north-to-south, while also accounting for error/undefined townships). __These are passed as a string, instead of a lambda.__

```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])

# Sort by Township, north-to-south.
t_list.sort_tracts(sort_key='t.ns')
```

##### Custom `sort_key` options:

|Option	|Option<br>Sub-type	|Sort `Tract` objects by...	|Footnote|
|----------	|:---------	|:---------	|:---------:|
|`'i'`	|	| the original order they were created	||
|`'t'`	|	|Township	||
|	|`'t.num'`	|raw Township number (ignoring N/S)	||
|	|`'t.ns'`	|north-to-south	||
|	|`'t.sn'`	|south-to-north	||
|`'r'`	|	|Range	||
|	|`'r.num'`	|raw Range number (ignoring E/W)	||
|	|`'r.ew'`	|east-to-west	|1|
|	|`'r.we'`	|west-to-east	|1|
|`'s'`	|	|Section number	||

Footnotes:
1) Sorting by east/west does not account for different Principal Meridians.

Use as many sort keys as you want. Place them all in a single string, separated by comma (spaces are optional). They will be applied in order from left-to-right, so place the highest 'priority' sort last (e.g., `'s, t.ns'` to first sort by section, then by township from north-to-south).

Reverse any or all of the custom keys by adding `'.reverse'` (or `'.rev'`) at the end of it.

*__Important__: The parameter `reverse=<bool>` has __no effect__ on these string-based custom keys. Instead, encode the intended reverse into the string itself, such as `'s.reverse'` (i.e. section number, highest-to-lowest).*

###### Example custom `sort_key`:

| Example | Outcome | Footnote |
|---------|------------------------------|:---:|
|`'s.reverse,r.ew,t.ns'` | Sort by section number (reversed, so largest-to-smallest);<br>then sort by Range (east-to-west);<br>then sort by Township (north-to-south)|  |
|`'i,s,r,t'`|Sort by original order;<br>then sort by Section (smallest-to-largest);<br>then sort by Range (smallest-to-largest);<br>then sort by Township (smallest-to-largest)| 1 |

Footnotes:
1) `'i,s,r,t'` is the default behavior of `.sort_tracts()`.

Example use:

```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])

# sort by Section from largest to smallest (i.e. reverse), then sort 
# by Rge from east-to-west, then by Twp from north-to-south.
t_list.sort_tracts(sort_key='s.reverse,r.ew,t.ns')
```


Note that Twp/Rge's that [are errors or undefined (i.e. `'XXXzXXXz'` or `'___z___z'`)]() will be sorted to the end of the list when sorting on Twp and/or Rge (whether by number, north-to-south, south-to-north, east-to-west, or west-to-east).  Similarly, [error Sections and undefined sections (i.e. `'XX'` or `'__'`)]() will be sorted to the end of the list when sorting on section.  (The exception is if the sort is reversed, in which case, they come first.) [#TODO: LINKS]



### `.filter()`

Filter into a new `TractList` those `Tract` objects that meet some condition (passed as a lambda or other function that returns a bool or bool-like value).

```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])
new_list = t_list.filter(key=lambda tract: tract.twprge in ['154n97w', '155n97w'])
new_list2 = t_list.filter(
    key=lambda tract: tract.sec_num is not None and tract.sec_num < 16)
```

Optionally remove the matching `Tract` objects from the original `TractList` with `drop=True`.
```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])
new_list3 = t_list.filter(key=lambda tract: tract.twp == '154n', drop=True)
```

### `.group()`

We can group `Tract` objects by attribute -- e.g., by Twp/Rge (all tracts in T154N-R97W, all those in T155N-R97W, etc.) -- into a dict, by using the `.group()` method on a `TractList` or `PLSSDesc`.

```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])
grouped_tracts = t_list.group(by_attribute='twprge')
```

It's hard to depict, but the dict stored above to var `grouped_tracts` looks like this, with each key being a unique `twprge` value among the tracts in the original `TractList`:
```
{
    '154n97w': [
            <pytrs.parser.parser.Tract object at 0x04660B08>,
            <pytrs.parser.parser.Tract object at 0x04660B80>,
            <pytrs.parser.parser.Tract object at 0x04660C10>,
            <pytrs.parser.parser.Tract object at 0x04660C58>
    ],
    '155n98w': [
            <pytrs.parser.parser.Tract object at 0x04660CA0>,
            <pytrs.parser.parser.Tract object at 0x04660CE8>
    ],
    <etc.>
}
```

To demonstrate a bit more intuitively, let's print some contents:
```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])

# Group by `.twprge` attribute values.
grouped_tracts = t_list.group(by_attribute='twprge')

# Get the tracts whose `.twprge` is '154n97w'.
t_list_154n97w = grouped_tracts['154n97w']

# Show that it's a TractList object and how many tracts are in it.
type(t_list_154n97w)        # -> <class 'pytrs.parser.parser.TractList'>
len(t_list_154n97w)         # -> 4  (this TractList holds 4 Tract objects)

# Use the `.print_data()` TractList method to print Tract data to console.
t_list_154n97w.print_data(['trs', 'desc'])
```

For our example, the above prints this to console:
```
Tract 1 / 4
trs  : 154n97w14
desc : NE/4

Tract 2 / 4
trs  : 154n97w15
desc : W/2

Tract 3 / 4
trs  : 154n97w16
desc : W/2

Tract 4 / 4
trs  : 154n97w17
desc : W/2
```

#### Nested grouping

If we pass a list of attribute names to `by_attributes=[<list of attribute names>]` instead of a single attribute, we get a nested dict (one layer per attribute name in the list).

```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])

# Group by `.twp` and then by `.rge` attribute values.
nested_grouped_tracts = t_list.group(by_attribute=['twp', 'rge'])
```
Again, it's hard to depict, but the dict stored to variable `nested_grouped_tracts` looks like this, keyed by unique `.twp` values, with the dict in the next level down keyed by unique `.rge` values. The values in the deepest level dict will be a `TractList` of the `Tract` objects in that group.
```
{
    '154n': {
        '97w': [
            <pytrs.parser.parser.Tract object at 0x042871D8>,
            <pytrs.parser.parser.Tract object at 0x042876E8>,
            <pytrs.parser.parser.Tract object at 0x04287E38>,
            <pytrs.parser.parser.Tract object at 0x04287E08>
            ],
        '96w': [
            <pytrs.parser.parser.Tract object at 0x042A6E20>,
            <pytrs.parser.parser.Tract object at 0x042871C0>,
            <pytrs.parser.parser.Tract object at 0x042A6E68>
            ]
    },
    '155n': {
        '98w': [
            <pytrs.parser.parser.Tract object at 0x042A62C8>,
            <pytrs.parser.parser.Tract object at 0x042A6AA8>
        ],
        '96w': [
            <pytrs.parser.parser.Tract object at 0x042A6C28>
        ]
    },
    <etc.>
}
```

To demonstrate, we'll get the `Tract` objects whose `.twp` was `'154n'` and whose `.rge` was `'97w'`, and then print some of their basic data to console:
```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])

# Group by `.twp` and then by `.rge` attribute values.
nested_grouped_tracts = t_list.group(by_attribute=['twp', 'rge'])

# Get the tracts whose `.twp` is '154n'.
dict_154n = nested_grouped_tracts['154n']

# Show that it's a dict, and that it in turns holds 2 more dicts.
type(dict_154n)             # -> <class 'dict'>
len(dict_154n)              # -> 2  (there were two unique ranges in '154n')

# Get the TractList of tracts whose `.twp` was '154n' and `.rge` was '97w'.
t_list_154n97w = dict_154n['97w']

# Show that it's a TractList object and how many tracts are in it.
type(t_list_154n97w)        # -> <class 'pytrs.parser.parser.TractList'>
len(t_list_154n97w)         # -> 4  (this TractList holds 4 Tract objects)

# Use the `.print_data()` TractList method to print Tract data to console.
t_list_154n97w.print_data(['trs', 'desc'])
```

For our example, the above prints this to console:
```
Tract 1 / 4
trs  : 154n97w14
desc : NE/4

Tract 2 / 4
trs  : 154n97w15
desc : W/2

Tract 3 / 4
trs  : 154n97w16
desc : W/2

Tract 4 / 4
trs  : 154n97w17
desc : W/2
```

#### Add new tracts to an existing dict of grouped tracts

Use the `into=<dict>` parameter to add additional tracts to an existing dict of grouped tracts.

```
t_list_1 = pytrs.TractList.from_multiple([<some large list of tracts>])
grouped_tracts = t_list_1.group(by_attribute='twprge')

grouped_tracts.keys()           # -> dict_keys(['154n97w', '155n97w'])

t_list_2 = pytrs.TractList.from_multiple([<some other list of tracts>])
t_list_2.group(by_attribute='twprge', into=grouped_tracts)

grouped_tracts.keys()           # -> dict_keys(['154n97w', '155n97w', '154n96w'])
```

Note: In the above example, the tracts are added to the `grouped_tracts` dict, so it doesn't matter whether we re-assign the returned dict to var `grouped_tracts`. New keys are added as necessary.

#### Sort the grouped tracts

Use the parameters `sort_key=` (and optionally `reverse=`) to sort *__each__* of the `TractList` objects in the dict of group tracts. (Takes any of the [options available in `.sort_tracts()` method]().) [# TODO: LINK]

An example using the `TractList` custom sort keys -- sorting by Range (number), then Township (north-to-south):
```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])
sorted_grouped_tracts = t_list.group(by_attribute='twprge', sort_key='r,t.ns')
```

An example using a lambda (i.e. using the built-in `list.sort()` functionality) -- in this case by the number of aliquots in each `Tract` (i.e. length of `.qqs` attribute):
```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])
sorted_grouped_tracts = t_list.group(
    by_attribute='twprge',
    sort_key=lambda tract: len(tract.qqs),
    reverse=True)
```

##### Sort the grouped tracts afterwards with the `sort_grouped_tracts()` function

Sort or resort a group without creating a new dict by using the `sort_grouped_tracts()` method.

```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])
grouped_tracts = t_list.group(by_attribute='twprge')

pytrs.sort_grouped_tracts(grouped_tracts, sort_key='r,t.ns')
```

