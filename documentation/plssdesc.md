
# Guide to `PLSSDesc` objects

A `PLSSDesc` object takes the raw text of a full PLSS land description and parse it into one or more `Tract` objects, each of which represents the land lying within a single, specific Twp/Rge/Section.

## Creating a `PLSSDesc` object

A `PLSSDesc` object takes raw text and immediately parses it into `Tract` objects.
```
raw_description = """T154N-R97W
Sec 14: NE/4
Sec 15: W/2"""

parsed_plssdesc = pytrs.PLSSDesc(raw_description)
```

### Optional init parameters are:

|Parameter              |Explanation                                                           |Footnote |
|-----------------------|:---------------------------------------------------------------------|:-------:|
|`layout=<str>`         | Force the parser to assume some specific order for Twp/Rge/Sec/desc  | 1       |
|`config=<str>`         | Configure the parser with a number of options                        | 2       |
|`parse_qq=<bool>`      | Parse the resulting `Tract` objects into lots/aliquots               |         |
|`source=<any>`         | Specify where this description came from.                            | 3       |
|`wait_to_parse=<bool>` | Do not parse at init.                                                |         |

1) The parser will deduce the `layout` if not specified here. Generally, you should let the parser deduce it unless you're certain that your dataset contains only one type of `layout`. (See more information on `layout` here.)  [# TODO: LINK TO LAYOUT]

2) See `ptrs.Config` objects for more information on `config=` options.  [# TODO: LINK TO CONFIG]

3) `source` does not affect the behavior of the parse in any way. Instead, it is meant as an internal record of where the description originally came from. It will be passed down to any `Tract` objects created by this `PLSSDesc`.(For example, if it came from a particular report, or a specific row in a spreadsheet, etc.) This can be useful for parsing numerous land descriptions (e.g., processing a large spreadsheet). It gets stored to the `.source` attribute (in both `PLSSDesc` and `Tract` objects).


### Parsing a `PLSSDesc` into `Tract` objects

Parsing is done automatically when a `PLSSDesc` object is created:
```
raw_description = """T154N-R97W
Sec 14: NE/4
Sec 15: W/2"""

parsed_plssdesc = pytrs.PLSSDesc(raw_description)
```

#### `Tract` objects are stored in the `.parsed_tracts` attribute

A `PLSSDesc` object stores `Tract` objects it created in the `.parsed_tracts` attribute (specifically, a `pytrs.TractList` object that holds the tracts, a subclass of the standard `list`).

```
raw_description = """T154N-R97W
Sec 14: NE/4
Sec 15: W/2"""

a_plssdesc = pytrs.PLSSDesc(raw_description)

len(a_plssdesc.parsed_tracts)  # -> 2  (we found 2 Tracts)
```

#### (Re)parse the original description with the `.parse()` method.

If we want to try parsing with different parameters, we can use the `.parse()` method, which returns a `pytrs.TractList` object containing all of the created `Tract` objects. If `commit=True` (on by default), the returned `TractList` will also be stored to the `.parsed_tracts` attribute of the `PLSSDesc`.

```
raw_description = "T154N-R97W Sec 14: NE/4"
dsc1 = pytrs.PLSSDesc(raw_description)

new_parsed_tracts = dsc1.parse(
    commit=False, segment=True, clean_qq=True, parse_qq=True)
``` 

Any unspecified parameters in `.parse()` will default to the corresponding values configured when the `PLSSDesc` was created (or reconfigured since).

#### Populate lots/aliquots in the subordinate `Tract` objects

The parameter `parse_qq=True` at init, or in `.parse()` will cause the resulting `Tract` objects to also populate their lots/aliquots (i.e. their `.lots`, `.qqs`, `.lots_qqs`, and `.lot_acres` attributes).

```
raw_description = "T154N-R97W Sec 14: NE/4"
dsc1 = pytrs.PLSSDesc(raw_description, parse_qq=True)

# Or...
reparsed_tracts = dsc1.parse(parse_qq=True, commit=False)
```

On the other hand, to tell the subordinate `Tract` objects to populate (or re-populate) their lots/aliquots *__without re-parsing the original PLSS land description__*, use the `.parse_tracts()` method.

```
raw_description = "T154N-R97W Sec 14: NE/4"
dsc1 = pytrs.PLSSDesc(raw_description)

dsc1.parse_tracts()
```

## Extracting data from the parsed `Tract` objects

`Tract` objects themselves have methods for extracting parsed data from themselves individually. [# TODO: LINK TO TRACT.MD]

But `PLSSDesc` objects (and `TractList` objects) contain methods to extract data from multiple `Tract` objects in bulk. This can be useful for compiling a spreadsheet, or for finding / grouping / filtering the tracts that match specific conditions.

(For a guide to the various useful `Tract` attributes, see this table.)  [# TODO: LINK TO TRACT.MD ATTRIBUTE TABLE]

### Compile `Tract` attributes to dicts with `.tracts_to_dict()`

Use this to get a list of dicts (one dict per `Tract`). Pass a list of the names of attributes we want to collect in each dict.

```
raw_description = """T154N-R97W
Sec 14: NE/4
Sec 15: Lots 1 - 3, S/2SW/4"""

parsed_plssdesc = pytrs.PLSSDesc(raw_description, parse_qq=True)
all_tract_data = parsed_plssdesc.tracts_to_dict(["trs", "desc", "lots", "qqs"])
```

The list stored to variable `all_tract_data` contains a dict for each `Tract`:
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

### Compile `Tract` attributes to a list of lists with `.tracts_to_list()`

Use this to get a nested list of lists (one list per `Tract`). Pass a list of the names of attributes we want to collect.

```
raw_description = """T154N-R97W
Sec 14: NE/4
Sec 15: Lots 1 - 3, S/2SW/4"""

parsed_plssdesc = pytrs.PLSSDesc(raw_description, parse_qq=True)
all_tract_data = parsed_plssdesc.tracts_to_list(["trs", "desc", "lots", "qqs"])
```

The list stored to variable `all_tract_data` contains a nested list for each `Tract`:
```
[
    ['154n97w14', 'NE/4', [], ['NENE', 'NWNE', 'SENE', 'SWNE']],
    ['154n97w15', 'Lots 1 - 3, S/2SW/4', ['L1', 'L2', 'L3'], ['SESW', 'SWSW']]
]
```

### Write `Tract` attributes to a .csv file with `.tracts_to_csv()`

*(Note: A more robust csv writer class is included as `pytrs.tractwriter.TractWriter`. But this method is simpler, if we just need to dump the data to a csv.)*

Use this to write data to a .csv file (one row per `Tract`).

|Parameter              |Explanation                                                           |Footnote |
|-----------------------|:---------------------------------------------------------------------|:-------:|
|`attributes`| a list of names of the `Tract` attributes to include|
|`fp=<path>`| The filepath of the .csv file to write to.|
|`mode=<'w' or 'a'>`| The mode to open the file in (either `'w'` or `'a'`)| 1|
|`nice_headers=<bool>`| Whether to use the values in the `Tract.ATTRIBUTES` dict for headers.| 2 |

1) `mode` serves the same purpose as it does in the builtin `open()` function. Here, it defaults to `'w'` (a new file, and overwriting any file already at that path). Use mode `'a'` to add this data to an existing .csv file.
2) `nice_headers` defaults to `False` (i.e. just use the attribute names themselves as headers).

```
raw_description = """T154N-R97W
Sec 14: NE/4
Sec 15: Lots 1 - 3, S/2SW/4"""

parsed_plssdesc = pytrs.PLSSDesc(raw_description, parse_qq=True)
all_tract_data = parsed_plssdesc.tracts_to_csv(
    attributes=["trs", "desc", "lots", "qqs"],
    fp=<some path>,
    mode='w',
    nice_headers=True)
```