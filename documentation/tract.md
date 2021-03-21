
# Guide to `Tract` objects

## `Tract` attribute table

| Attribute         | Explanation                                                           | Possible Type(s) 	| Footnote |
|-------------------|-----------------------------------------------------------------------|------------------	|:--------:|
| `.trs`            | The Twp/Rge/Sec combination in the standard pyTRS format              | str              	| 1, 5     |
| `.twp`            | Twp portion of `.trs`                                                 | str              	| 1, 5     | 
| `.twp_num`        | Twp portion of `.trs`, as an int or None                              | int, None        	| 5        |
| `.twp_ns`         | N/S portion of `.trs`, as a str or None                               | str, None        	|  5       |
| `.rge`            | Rge portion of `.trs`                                                 | str              	| 1, 5     |
| `.rge_num`        | Rge portion of `.trs`, as an int or None                              | int, None        	|  5       |
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
1) The standard pyTRS format for Twp/Rge/Sec is up to 3 digits for Twp (plus `'n'` or `'s'`) and for Rge (plus `'e'` or `'w'`), and exactly two digits for section. (Examples: `Sec 14 of T154N-R97W` -> `'154n97w14'`; and `Sec 1 of T7S-R9E` -> `'7s9e01'`) 

2) `.lots`, `.qqs`, `.lots_qqs`, and `.lot_acres` are only populated if/when a `Tract` object is parsed. If a `Tract` object was created from a `PLSSDesc` parse, it will be parsed into lots/aliquots *__only if__* `parse_qq=True` was passed. 

3) Warning and error flags are shared by a `Tract` object and its parent `PLSSDesc` object if parsed at the same time (e.g., `parse_qq=True` at init).

4) `Tract` objects will not create a `desc_is_flawed` status, but may inherit it from parent `PLSSDesc` (if any).

5) *Setting* the `.trs` attribute of a `Tract` object will populate the other associated attributes accordingly (`.twp`, `.rge`, `.sec`, etc. -- which cannot be set directly).  [# TODO: LINK TO THIS SECTION OF TRACT.MD]



## `Tract` objects created from parsing a `PLSSDesc`

When a `PLSSDesc` object is populated, it automatically creates `Tract` objects, stored in the `.parsed_tracts` attribute (specifically, a `pytrs.TractList` object that holds the tracts).

```
parsed_plssdesc = pytrs.PLSSDesc("T154N-R97W Sec 14: NE/4")

# The resulting Tract objects are stored in `.parsed_tracts` of the PLSSDesc.
for tract in parsed_plssdesc.parsed_tracts:
    print(tract.trs)
```

### Populate lots/aliquots at init with `parse_qq=True` parameter

If we want to populate the `lots`, `qqs`, `lots_qqs`, and `lot_acres` attributes of the resulting `Tract` objects, we need to specify `parse_qq=True` (or `config='parse_qq').
```
parsed_plssdesc = pytrs.PLSSDesc("T154N-R97W Sec 14: NE/4", parse_qq=True)

for tract in parsed_plssdesc.parsed_tracts:
    print(tract.lots_qqs)
```

### Populate lots/aliquots later with `.parse_tracts()` method

Alternatively, we can first parse a `PLSSDesc` without populating `lots` etc., and change our minds later.
```
parsed_plssdesc = pytrs.PLSSDesc("T154N-R97W Sec 14: NE/4")
parsed_plssdesc.parse_tracts()

for tract in parsed_plssdesc.parsed_tracts:
    print(tract.lots_qqs)
```

## Creating `Tract` objects directly

When creating a `Tract` object directly, specifying the `trs` is optional; and populating `lots`, `qqs`, `lots_qqs`, and `lot_acres` attributes is also optional (turned on with `parse_qq=True`).
```
# Optional parameter `parse_qq=True`.
tract_object = pytrs.Tract("NE/4", trs="154n97w14", parse_qq=True)

# ...or an equivalent Tract object, specifying Twp/Rge/Sec with components.
tract_object = pytrs.Tract.from_twprgesec(
    "NE/4", twp=154, rge=97, sec=14, parse_qq=True, config='n,w')
```

### Populate lots/aliquots with `.parse()`
To populate (or re-populate) the `lots`, `qqs`, `lots_qqs`, and `lot_acres` attributes later on, use the `.parse()` method.
```
tract_object = pytrs.Tract("Lots 1 - 3, NE/4")
tract_object.parse()

# `.lots_qqs` etc. are now populated.
for aliquot in tract_object.qqs:
    print(aliquot)
```

### Setting Twp/Rge/Sec (`.trs` attribute, etc.)

Setting the `.trs` attribute of a `Tract` object will populate the other associated attributes accordingly (`.twp`, `.rge`, `.sec`, etc.) -- either assigned directly (`a_tract.trs = '154n97w14'`) or with the `.set_twprgesec()` method:

```
a_tract = pytrs.Tract("NE/4")

a_tract.trs         # -> '___z___z__'  (an undefined Twp/Rge/Sec)
a_tract.twp         # -> '___z'
a_tract.twp_num     # -> None
# etc.

# Set `.trs` directly:
a_tract.trs = "154n97w14"

# Or equivalently, from the Twp/Rge/Sec components...
a_tract.set_twprgesec(twp=154, rge=97, sec=14, default_ns='n', default_ew='w')

# In either case:
a_tract.trs         # -> '154n97w14'
a_tract.twp         # -> '154n'
a_tract.twp_num     # -> 154 (an int)
a_tract.rge_ew      # -> 'w'
# etc.
```

Other Twp/Rge/Sec attributes cannot be assigned directly. They may *__only__* be populated via one of the two methods above.

## Extracting data from individual `Tract` objects

To extract data from *__multiple__* `Tract` objects, look into the `.tracts_to_dict()`, `.tracts_to_list()`, or `.tracts_to_csv()` methods in both `PLSSDesc` classes and `TractList` classes.

However, to extract data from individual `Tract` objects, use these methods:

### Extract to a dict with `.to_dict()`

Pass a list of the names of attributes we want to collect in a dict:
```
tract = pytrs.Tract("Lots 1 - 3, NE/4", trs="154n97w14", parse_qq=True)
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

### Extract to a list with `.to_list()`

Pass a list of the names of attributes we want to collect in a list:
```
tract = pytrs.Tract("Lots 1 - 3, NE/4", trs="154n97w14", parse_qq=True)
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
