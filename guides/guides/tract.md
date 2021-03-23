
# Guide to `Tract` objects

A `Tract` object represents land lying within a single, specific Twp/Rge/Sec.

`# TODO: Table of contents with links`

## `Tract` attribute table

Access these `Tract` attributes directly, or compile them in bulk with various methods. [#TODO: LINK]

| Attribute         | Explanation                                                           | Possible Type(s) 	| Footnote |
|:------------------|:----------------------------------------------------------------------|------------------	|:--------:|
| `.trs`            | The Twp/Rge/Sec combination in [the standard pyTRS format](https://github.com/JamesPImes/pyTRS/blob/master/guides/trs.md#standard-pytrs-format-for-twprgesec)              | str              	| 1, 5     |
| `.twp`            | Twp portion of `.trs`                                                 | str              	| 1, 5     | 
| `.twp_num`        | Twp portion of `.trs` (without N/S), as an int or None                | int, None        	| 5        |
| `.twp_ns`         | N/S portion of `.trs`, as a str or None                               | str, None        	|  5       |
| `.rge`            | Rge portion of `.trs`                                                 | str              	| 1, 5     |
| `.rge_num`        | Rge portion of `.trs` (without E/W), as an int or None                | int, None        	|  5       |
| `.rge_ew`         | E/W portion of `.trs`, as a str or None                               | str, None        	|  5       |
| `.twprge`         | Twp/Rge portion of `.trs`                                             | str              	| 1, 5     |
| `.sec`            | Section portion of `.trs`, as a str                                   | str              	| 1, 5     |
| `.sec_num`        | Section portion of `.trs`, as an int or None                          | int, None        	|  5       |
| `.desc`           | the description block of the land __within__ this Twp/Rge/Sec         | str              	|          |
| `.qqs`            | list of identified aliquots                                           | list of strings  	| 2        |
| `.lots`           | list of identified lots                                               | list of strings  	| 2        |
| `.lots_qqs`       | list of identified lots and aliquots                                  | list of strings  	| 2        |
| `.lot_acres`      | identified lots and their purported gross acreages                    | dict of {str: str}| 2        |
| `.pp_desc`        | the preprocessed description                                          | str              	|          |
| `.source`         | (optional) source specifying where the description came from          | (any)            	|          |
| `.orig_desc`      | The full, original text of the parent `PLSSDesc` object, if any.      | str, None        	|          |
| `.orig_index`     | order in which this `Tract` object was created in parent `PLSSDesc`   | int              	|          |
| `.w_flags`        | a list of warning flags                                               | list of strings  	| 3        |
| `.w_flag_lines`   | list of 2-tuples (warning flags, and their context)                   | list of tuples   	| 3        |
| `.e_flags`        | a list of error flags                                                 | list of strings  	| 3        |
| `.e_flag_lines`   | list of 2-tuples (warning flags, and their context)                   | list of tuples   	| 3        |
| `.flags`        	| a list of warning + error flags                                       | list of strings  	| 3        |
| `.flag_lines`     | list of 2-tuples (warning + error flags, and their context)           | list of tuples   	| 3        |
| `.desc_is_flawed` | If a fatal flaw was found during parsing of parent `PLSSDesc`         | bool             	| 4        |

Footnotes:
1) The [standard pyTRS format for Twp/Rge/Sec](https://github.com/JamesPImes/pyTRS/blob/master/guides/trs.md#standard-pytrs-format-for-twprgesec) is up to 3 digits for Twp (plus `'n'` or `'s'`) and for Rge (plus `'e'` or `'w'`), and exactly two digits for section. (Examples: `Sec 14 of T154N-R97W` -> `'154n97w14'`; and `Sec 1 of T7S-R9E` -> `'7s9e01'`) 

2) `.lots`, `.qqs`, `.lots_qqs`, and `.lot_acres` are only populated [if/when a `Tract` object itself is parsed](https://github.com/JamesPImes/pyTRS/blob/master/guides/tract.md#populating-lotsaliquots). If a `Tract` object was created by a `PLSSDesc`, lots/aliquots will be populated *__only if__* `parse_qq=True` was passed or `config='parse_qq'`. 

3) Warning and error flags are shared by a `Tract` object and its parent `PLSSDesc` object. A given flags might have been caused by a different `Tract` under the same parent `PLSSDesc`. (This is intentional, because flags mean something might have gone wrong during parsing, and the wrong text might have ended up with the wrong `Tract`, etc.)

4) `Tract` objects will never create a `desc_is_flawed` status, but may inherit it from parent `PLSSDesc` (if any).

5) [*Setting* the `.trs` attribute](https://github.com/JamesPImes/pyTRS/blob/master/guides/tract.md#setting-twprgesec-trs-attribute-etc) of a `Tract` object will populate the other associated attributes accordingly (`.twp`, `.rge`, `.sec`, etc. -- which cannot be set directly).


## Extracting data in bulk from a `Tract` object

[See the guide on extracting `Tract` data in bulk.](https://github.com/JamesPImes/pyTRS/blob/master/guides/extracting_data.md)




## `Tract` objects created from parsing a `PLSSDesc`

When a `PLSSDesc` object is parsed, it automatically creates `Tract` objects and stores them in the `.tracts` attribute (specifically, a `pytrs.TractList` object that holds the tracts).

```
parsed_plssdesc = pytrs.PLSSDesc("T154N-R97W Sec 14: NE/4")

# The resulting Tract objects are stored in `.tracts` of the PLSSDesc.
for tract in parsed_plssdesc.tracts:
    print(tract.trs)
```


## Creating `Tract` objects directly

When creating a `Tract` object directly, specifying the `trs` is optional; and populating `lots`, `qqs`, `lots_qqs`, and `lot_acres` attributes is also optional (parsing is turned on with `parse_qq=True` and [optionally configured with `config=`](https://github.com/JamesPImes/pyTRS/blob/master/guides/config.md)).
```
# Optional parameter `parse_qq=True`.
tract_object = pytrs.Tract(
    "NE/4", trs="154n97w14", parse_qq=True, config='clean_qq, qq_depth_min.3')
```

|Parameter              | Explanation                                                          |Footnote |
|:----------------------|:---------------------------------------------------------------------|:-------:|
|`desc=<str>`           | The description of the land lying within this unit Twp/Rge/Sec       |         |
|`trs=<str>`            | The Twp/Rge/Sec in the [standard pyTRS format](https://github.com/JamesPImes/pyTRS/blob/master/guides/trs.md#standard-pytrs-format-for-twprgesec)                         | 1       |
|`config=<str>`         | [Configure the parser with a number of options](https://github.com/JamesPImes/pyTRS/blob/master/guides/config.md)                        | 2       |
|`parse_qq=<bool>`      | Parse this `Tract` object into lots/aliquots               |         |
|`source=<any>`         | Specify where this description came from.                            | 3       |
|`orig_desc=<str>`      | The full PLSS description from which this `Tract` was carved out       | 4       |
|`orig_index=<int>`     | order in which this `Tract` object was created in parent `PLSSDesc`  | 4       |
|`desc_is_flawed=<bool>`| If a fatal flaw was found during parsing of parent `PLSSDesc`        | 4       |

Footnotes:

*[See `.from_twprgesec()` footnotes 1 - 4, which are identical.](https://github.com/JamesPImes/pyTRS/blob/master/guides/tract.md#tractfrom_twprgesec-footnotes)*


#### Create `Tract` objects with uncompiled Twp/Rge/Sec components with `Tract.from_twprgesec()`

To create a `Tract` without first compiling the Twp, Rge, and Section components into the pyTRS format, use `Tract.from_twprgesec()` method:

```
tract_object = pytrs.Tract.from_twprgesec(
    "NE/4", twp=154, rge=97, sec=14, default_ns='n', default_ew='w',
    parse_qq=True, config='clean_qq,qq_depth_min.3')
```

|Parameter              | Explanation                                                          |Footnote |
|:----------------------|:---------------------------------------------------------------------|:-------:|
|`desc=<str>`           | The description of the land lying within this unit Twp/Rge/Sec       |         |
| `twp=<str or int>`    | The Township, either an int, or a str (e.g., `'154n'`, `'1s'`, etc.) | 1, 5    |
| `rge=<str or int>`    | The Range, either an int, or a str (e.g., `'154n'`, `'1s'`, etc.)    | 1, 5    |
| `sec=<str or int>`    | The Section, either an int, or a str (e.g., `'154n'`, `'1s'`, etc.)  | 1       |
| `default_ns=<'n' or 's'>` | Whether to default Township to North or South                    | 1, 5    |
| `default_ns=<'e' or 'w'>` | Whether to default Range to East or West                         | 1, 5    |
|`config=<str>`         | [Configure the parser with a number of options](https://github.com/JamesPImes/pyTRS/blob/master/guides/config.md)                        | 2       |
|`parse_qq=<bool>`      | Parse this `Tract` object into lots/aliquots               |         |
|`source=<any>`         | Specify where this description came from.                            | 3       |
|`orig_desc=<str>`      | The full PLSS description from which this `Tract` was carved out       | 4       |
|`orig_index=<int>`     | order in which this `Tract` object was created in parent `PLSSDesc`  | 4       |
|`desc_is_flawed=<bool>`| If a fatal flaw was found during parsing of parent `PLSSDesc`        | 4       |

##### `Tract.from_twprgesec()` Footnotes:
1) The [standard pyTRS format for Twp/Rge/Sec](https://github.com/JamesPImes/pyTRS/blob/master/guides/trs.md#standard-pytrs-format-for-twprgesec) is up to 3 digits for Twp (plus `'n'` or `'s'`) and for Rge (plus `'e'` or `'w'`), and exactly two digits for section. (Examples: `Sec 14 of T154N-R97W` -> `'154n97w14'`; and `Sec 1 of T7S-R9E` -> `'7s9e01'`)  See an explanation here. [# TODO: Link to TRS.MD]

2) See [the `config` guide](https://github.com/JamesPImes/pyTRS/blob/master/guides/config.md) for more information on `config=` options.

3) `source` does not affect the behavior of the parse in any way. Instead, it is meant as an internal record of where the description originally came from. (For example, if it came from a particular report, or a specific row in a spreadsheet, etc.)  If a `Tract` is created by parsing a `PLSSDesc`, then `source` will be inherited from the parent `PLSSDesc`.  This can be useful for parsing numerous land descriptions (e.g., processing a large spreadsheet). It gets stored to the `.source` attribute (in both `PLSSDesc` and `Tract` objects).

4) `orig_desc`, `orig_index`, and `desc_is_flawed` are inherited by a `Tract` from a parent `PLSSDesc` object, if any. They *can* be set here, but there is probably not much reason for it.

5) If `twp` is passed as an int, or as a string that doesn't encode North/South (e.g., `'154'` instead of `'154n'`), it will fall back to what is specified in `default_ns` (if any), and if not there, then to `config=`. Similarly, if `rge` is passed as an int or as a string that doesn't encode East/West (e.g., `'97'` instead of `'97w'`), it will default to `default_ew` and then to `config=`. If not specified in any of those places, it will fall back to `PLSSDesc.MASTER_DEFAULT_NS` and `PLSSDesc.MASTER_DEFAULT_EW`, which are `'n'` and `'w'` unless changed by the user. 


### Populating lots/aliquots

If we want to populate the `lots`, `qqs`, `lots_qqs`, and `lot_acres` attributes of a `Tract` objects, we can trigger that in a number of ways:

1) If we instruct a `PLSSDesc` with `parse_qq=True` or `config='parse_qq'`, then the resulting `Tract` objects will be parsed into lots/QQs.

2) Call `parse()` on a `PLSSDesc` object with `parse_qq=True` to re-parse the `PLSSDesc` object itself, creating new `Tract` objects, which will also populate their lots/aliquots.

3) Call `.parse_tracts()` on an already-parsed `PLSSDesc` object to instruct its subordinate `Tract` objects to populate their lots/aliquots, *__without__* re-parsing the original `PLSSDesc` object itself (i.e. will *__not__* create new `Tract` objects).

4) Create a `Tract` object with `parse_qq=True` or `config='parse_qq'`.

5) Call `.parse()` on a `Tract` object.

*__Note:__* Control the size of the parsed aliquots with [`config=` parameters](https://github.com/JamesPImes/pyTRS/blob/master/guides/config.md), specifically the [`qq_depth_min`, `qq_depth_max`, or `qq_depth` parameters](https://github.com/JamesPImes/pyTRS/blob/master/guides/config.md#control-the-granularity-or-depth-of-aliquot-parsing-with-qq_depth-qq_depth_min-andor-qq_depth_max). By default, they are parsed into quarter-quarters (QQs), i.e. 40-acre divisions (e.g., `'W/2NE/4' -> ['NWNE', 'SWNE']`) -- but will also include smaller aliquot divisions if they exist in the description (e.g., `'E/2W/2NE/4' -> ['E2NWNE','E2SWNE']`).


### Setting Twp/Rge/Sec (`.trs` attribute, etc.)

Setting the `.trs` attribute of a `Tract` object will populate the other associated attributes accordingly (`.twp`, `.rge`, `.sec`, etc.) -- and it can be done either when created (`a_tract = pytrs.Tract("NE/4", trs='154n97w14')` or with [`Tract.from_twprgesec()`](https://github.com/JamesPImes/pyTRS/blob/master/guides/tract.md#create-tract-objects-with-uncompiled-twprgesec-components-with-tractfrom_twprgesec), assigned directly afterwards (`a_tract.trs = '154n97w14'`) or with the `.set_twprgesec()` method:
```
# `trs` is not specified for this Tract.
a_tract = pytrs.Tract("NE/4")

a_tract.trs         # -> '___z___z__'  (an undefined Twp/Rge/Sec)
a_tract.twp         # -> '___z'
a_tract.twp_num     # -> None
# etc.


# Set `.trs` directly:
a_tract.trs = '154n97w14'

# Or equivalently, from the Twp/Rge/Sec components...
a_tract.set_twprgesec(twp=154, rge=97, sec=14, default_ns='n', default_ew='w')

# Or equivalently, do it when creating the Tract...
a_tract = pytrs.Tract("NE/4", trs="154n97w14")

# Or equivalently, created via `.from_twprgesec()`...
a_tract = Tract.from_twprgesec(
    desc="NE/4", twp=154, rge=97, sec=14, default_ns='n', default_ew='w')

# In any case:
a_tract.trs         # -> '154n97w14'
a_tract.twp         # -> '154n'
a_tract.twp_num     # -> 154 (an int)
a_tract.rge_ew      # -> 'w'
# etc.
```

Various Twp/Rge/Sec attributes *__other than__* `.trs` cannot be assigned directly. They may *__only__* be populated via one of the three methods above.
