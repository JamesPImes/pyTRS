
# Guide to `PLSSDesc` objects

A `PLSSDesc` object takes the raw text of a full PLSS land description and parse it into one or more `Tract` objects, each of which represents the land lying within a single, specific Twp/Rge/Section.

`# TODO: Table of contents with links`

## Creating a `PLSSDesc` object

A `PLSSDesc` object takes raw text and immediately parses it into `Tract` objects.
```
raw_description = """T154N-R97W
Sec 14: NE/4
Sec 15: W/2"""

parsed_plssdesc = pytrs.PLSSDesc(raw_description)
```
Just to demonstrate that we have created some `Tract` objects, we'll print some of their basic data to console:

```
parsed_plssdesc.print_data(['trs', 'desc'])
```
... which prints:
```
Tract 1 / 2
trs  : 154n97w14
desc : NE/4

Tract 2 / 2
trs  : 154n97w15
desc : W/2
```

### Optional init parameters:

|Parameter              | Explanation                                                          |Footnote |
|:----------------------|:---------------------------------------------------------------------|:-------:|
|`layout=<str>`         | Force the parser to assume some specific order for Twp/Rge/Sec/desc  | 1       |
|`config=<str>`         | Configure the parser with a number of options                        | 2       |
|`parse_qq=<bool>`      | Whether the resulting `Tract` objects should also parse into lots/aliquots               |         |
|`source=<any>`         | Specify where this description came from.                            | 3       |
|`wait_to_parse=<bool>` | Do not parse at init.                                                |         |

1) The parser will deduce the `layout` if not specified here. Generally, you should let the parser deduce it unless you're certain that your dataset contains only one type of `layout`. (See more information on `layout` here.)  [# TODO: LINK TO LAYOUT]

2) See `ptrs.Config` objects for more information on `config=` options.  [# TODO: LINK TO CONFIG]

3) `source` does not affect the behavior of the parse in any way. Instead, it is meant as an internal record of where the description originally came from. It will be passed down to any `Tract` objects created by this `PLSSDesc`.(For example, if it came from a particular report, or a specific row in a spreadsheet, etc.) This can be useful for parsing numerous land descriptions (e.g., processing a large spreadsheet). It gets stored to the `.source` attribute (in both `PLSSDesc` and `Tract` objects).


#### `Tract` objects are stored in the `.parsed_tracts` attribute

A `PLSSDesc` object stores `Tract` objects it created in the `.parsed_tracts` attribute (specifically, a `pytrs.TractList` object that holds the tracts, a subclass of the standard `list`).

```
raw_description = """T154N-R97W
Sec 14: NE/4
Sec 15: W/2"""

a_plssdesc = pytrs.PLSSDesc(raw_description)

len(a_plssdesc.parsed_tracts)   # -> 2  (we found 2 Tracts)
```

Any unspecified parameters in `.parse()` will default to the corresponding values configured when the `PLSSDesc` was created (or reconfigured since).


## Parsing a `PLSSDesc` into `Tract` objects

##### Parse automatically when created.

By default, parsing is done automatically when a `PLSSDesc` object is created:
```
raw_description = """T154N-R97W
Sec 14: NE/4
Sec 15: W/2"""

parsed_plssdesc = pytrs.PLSSDesc(raw_description)
```

##### Re-parse the original description with the `.parse()` method.

If we want to try parsing with different parameters, we can use the `.parse()` method, which returns a `pytrs.TractList` object containing all of the created `Tract` objects. If `commit=True` (on by default), the returned `TractList` will also be stored to the `.parsed_tracts` attribute of the `PLSSDesc`.

```
raw_description = "T154N-R97W Sec 14: NE/4"
dsc1 = pytrs.PLSSDesc(raw_description)

new_parsed_tracts = dsc1.parse(
    commit=False, segment=True, clean_qq=True, parse_qq=True)
``` 


## Populate lots/aliquots in the subordinate `Tract` objects

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


## Extracting data from the parsed `Tract` objects in bulk

[See the guide on extracting Tract data]  [#TODO: Link]


## `layout` (syntax of Twp/Rge/Sec/Desc)

The PLSS itself does not place many strict limitations on the syntax of Township, Range, Section, and 'description block' -- i.e., they can appear in essentially any order (except that Township pretty much always comes before Range). Below are the different permutations (called `layout`) that can be handled by pyTRS:

| layout      | Order of components    | Example                        | Footnotes |
|:------------|:-----------------------|:-------------------------------|:---------:|
|`'TRS_desc'` | Twp - Rge - Sec - desc | T154N-R97W <br> Sec 14: NE/4   | 1         |
|`'TR_desc_S'`| Twp - Rge - desc - Sec | T154N-R97W <br> NE/4 of Sec 14 | 1         |
|`'desc_STR'` | desc - Sec - Twp - Rge | NE/4 of Sec 14, T154N-R97W     |           |
|`'s_desc_TR'`| Sec - desc - Twp - Rge | Sec 14: NE/4, T154N-R97W       | 3         |
|`'copy_all'` | n/a                    | n/a                            | 2         |

Because the components can appear in varying order, a PLSS description will be parsed differently, which is why the concept of `layout` exists in this library at all.

In general, the parsing algorithm is capable of deducing the `layout` of the input data. However, the `layout` can also be dictated by the user ([via `config=` init parameter] [#TODO : LINK TO CONFIG]); although doing so is not recommended, unless you reliably know the layout of your dataset and want to capture errors very strictly.

Get a tuple of all currently implemented `layout` options in `pytrs.IMPLEMENTED_LAYOUTS`. Get a string containing examples of each in `pytrs.IMPLEMENTED_LAYOUT_EXAMPLES`


Footnotes:
1) None of these layouts are required to be one one line or on multiple lines. However, in real world data, `TRS_desc` and `TR_desc_S` (i.e., when Twp/Rge come first) layouts are often broken out onto multiple lines.

2) `'copy_all'` is a stopgap layout used by pyTRS to ensure that the text is maintained in the event that the layout cannot be successfully deduced (perhaps due to an omission or unrecognizable misspelling of section, township, or range).

3) *If you're writing land descriptions like this, please just stop doing that.*


#### Known `layout` limitations
You will notice that the above `layout` table does *__not__* account for descriptions where the Section is couched *__within__* the description block itself, like so:
```
T154N-R97W
That part of the NE/4 of Section 14 lying north of the river
```
...or...
```
That part of the NE/4 of Section 14 lying north of the river, in T154N-R97W
```

That's a target area for improvement in future versions.

(*These two examples would both be interpreted as `"154n97w14: That part of the NE/4"`, assuming the parser is allowed to deduce the layout.*)