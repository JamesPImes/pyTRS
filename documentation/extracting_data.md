
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
|`nice_headers=<bool>`| Whether to use the values in the `Tract.ATTRIBUTES` dict for headers| 2 |

1) `mode` serves the same purpose as it does in the builtin `open()` function. Here, it defaults to `'w'` (a new file, and overwriting any file already at that path). Use mode `'a'` to add this data to an existing .csv file.
2) `nice_headers` defaults to `False` (i.e. just use the attribute names themselves as headers).


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

## Grouping / Filtering / Sorting `Tract` objects

### `.sort_tracts()`


```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])
t_list.sort_tracts(sort_key='r,t')
```

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

Get a dict of all of the `Tract` objects in the `TractList`, based on some attribute -- e.g., group by Twp/Rge. 

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
t_list_154n97w.print_data('trs', 'desc')
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

Pass `by_attributes=[<list of attribute names>]`.

