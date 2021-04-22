
# Guide to `TRS` objects

pyTRS uses a standard format for representing Township / Range / Section, detailed below.

The [`TRS` class](https://github.com/JamesPImes/pyTRS/blob/master/guides/guides/trs.md#trs-objects) can be used to compile a string in this format, from the Twp/Rge/Sec components. It can also be used to [extract the components](https://github.com/JamesPImes/pyTRS/blob/master/guides/guides/trs.md#trs-attribute-table) from a pyTRS-standardized Twp/Rge/Sec.

## Standard pyTRS format for Twp/Rge/Sec

pyTRS uses a standardized format for representing Township / Range / Section:

| Component | Format                                                | Example       |
|-----------|-------------------------------------------------------|---------------|
| Township  | Up to three digits, plus `'n'` or `'s'` for direction | `T154N -> '154n'` <br> `T7S -> '7s'`|
| Range     | Up to three digits, plus `'e'` or `'w'` for direction | `R97W -> '97w'` <br> `R9E -> '9e'`|
| Section   | Exactly two digits                                    | `Section 14 -> '14'` <br> `Section 1 -> '01'`|

These are combined to form the `trs` in a standardized format:

* `Section 14 of T154N-R97W` becomes `'154n97w14'`
* `Section 1 of T7S-R9E` becomes `'7s9e01'`

#### Undefined Twp/Rge/Sec

When a `Tract` or `TRS` object is created without specifying Twp/Rge/Sec, its `trs` is set to the undefined value, `'___z___z__'`, i.e.:

| Component | Format   |
|-----------|----------|
| Township  | `'___z'` |
| Range     | `'___z'` |
| Section   | `'__'`   |

#### Error Twp/Rge/Sec

When a `Tract` or `TRS` object is created with a `trs` that couldn't be deciphered (or when a `PLSSDesc` couldn't parse a Twp/Rge/Sec that made sense), the `trs` is set to the error value, `'XXXzXXXzXX'`, i.e.:

| Component | Format   |
|-----------|----------|
| Township  | `'XXXz'` |
| Range     | `'XXXz'` |
| Section   | `'XX'`   |

## `TRS` objects

A `TRS` object will take the `trs` in the pyTRS standard format and break it into is component parts. Pass the appropriately formatted string as the sole argument when creating a `TRS` object.

```
trs1 = pytrs.TRS('154n97w14')

trs1.twp        # -> '154n'
trs1.rge        # -> '97w'
# etc.
```

#### Get the `trs` in standard pyTRS format from uncompiled Twp/Rge/Sec components

Create a `TRS` object with the `TRS.from_twprgesec()` method, then get its `.trs` attribute.

```
trs2 = pytrs.TRS.from_twprgesec(twp=154, rge=97, sec=14, default_ns='n', default_ew='w')

trs2.trs        # -> '154n97w14'
trs2.twp        # -> '154n'
trs2.rge        # -> '97w'
# etc.
```

`TRS.from_twprgesec()` takes these parameters:

|Parameter              | Explanation                                                         |Footnote |
|:----------------------|:--------------------------------------------------------------------|:-------:|
| `twp=<str or int>`    | Township (e.g., `'154n'`, `'1s'`, etc.)                             | 1       |
| `rge=<str or int>`    | Range, either an int or a str (e.g., `'97w'`, `'9e'`, etc.)        | 1       |
| `sec=<str or int>`    | Section, either an int or a str (e.g., `'14'`, `14`, `'01'`, `1`, etc.)      |         |
| `default_ns=<'n' or 's'>` | Whether to default Township to North or South, if not specified | 1       |
| `default_ns=<'e' or 'w'>` | Whether to default Range to East or West, if not specified      | 1       |

Footnotes:
1) If `twp` is passed as an int, or as a string that doesn't encode North/South (e.g., `'154'` instead of `'154n'`), it will fall back to what is specified in `default_ns` (if any). Similarly, if `rge` is passed as an int or as a string that doesn't encode East/West (e.g., `'97'` instead of `'97w'`), it will default to `default_ew`. If not specified there, it will fall back to `PLSSDesc.MASTER_DEFAULT_NS` and `PLSSDesc.MASTER_DEFAULT_EW`, which are `'n'` and `'w'` unless changed by the user. 

## TRS Attribute Table

| Attribute         | Explanation                                                           | Possible Type(s) 	| Footnote |
|:------------------|:----------------------------------------------------------------------|------------------	|:--------:|
| `.trs`            | The Twp/Rge/Sec combination in the [standard pyTRS format](https://github.com/JamesPImes/pyTRS/blob/master/guides/guides/trs.md#standard-pytrs-format-for-twprgesec)              | str              	| |
| `.twp`            | Twp portion of `.trs`                                                 | str              	| | 
| `.twp_num`        | Twp portion of `.trs` (without N/S), as an int or None                 | int, None        	| 1 |
| `.twp_ns`         | N/S portion of `.trs`, as a str or None                               | str, None        	| 1 |
| `.twp_undef`      | Whether the Twp was undefined. | bool | 1 |
| `.ns`         | same as `.twp_ns`                               | str, None        	|  1 |
| `.rge`            | Rge portion of `.trs`                                                 | str              	| |
| `.rge_num`        | Rge portion of `.trs` (without E/W), as an int or None                | int, None        	| 1 |
| `.rge_ew`         | E/W portion of `.trs`, as a str or None                               | str, None        	| 1 |
| `.ew` | same as `.rge_ew` | str, None | 1 |
| `.rge_undef`      | Whether the Rge was undefined. | bool | 1 |
| `.twprge`         | Twp/Rge portion of `.trs`                                             | str              	| |
| `.sec`            | Section portion of `.trs`, as a str                                   | str              	| |
| `.sec_num`        | Section portion of `.trs`, as an int or None                          | int, None        	| 1 |
| `.sec_undef`      | Whether the Section was undefined. | bool | 1 |

1) When a `trs` was an error or was undefined, `twp_num`, `twp_ns`, `ns`, `rge_num`, `rge_ew`, `ew`, and `sec_num` are all set to `None`. To know whether it was undefined an error is specified in the `twp_undef`, `rge_undef`, and `sec_undef` attribute, respectively. As an example:

* `twp_num` is `None` and `twp_undef` is `True` -> This was an *__undefined__* township.
* `twp_num` is `None` and `twp_undef` is `False` -> This was an *__error__* township.
* `twp_num` is not `None` -> This township is fine.
* (and similar for range and section)


## `TRSList` objects

The class `TRSList` is very similar to [`TractList`](https://github.com/JamesPImes/pyTRS/blob/master/guides/guides/tractlist.md) (in fact they are both subclassed from the same superclass and contain many of the same methods), but it holds `TRS` objects instead of `Tract` objects.

If you add to a `TRSList` a string, the string will first be converted to a `TRS` object.

```
trs1 = pytrs.TRS('154n97w14')
trs2 = pytrs.TRS('154n97w15')
trs_list = pytrs.TRSList([trs1, trs2])

# Or add strings directly (they will be converted to TRS objects):
trs_list = TRSList(['154n97w14', '154n97w15'])
```

We can also pass to it `Tract` objects, in which case the `.trs` attribute will be extracted and converted to a `TRS` object before being added.
```
tract = pytrs.Tract('NE/4', trs='154n97w14')
trs_list = pytrs.TRSList([tract])
```

Similarly, we can extract/convert the `.trs` attributes in `Tract` objects from a `PLSSDesc` or `TractList` object if we pass them to `.extend()`:
```
plssdesc = pytrs.PLSSDesc('T154N-R97W Sec 14: NE/4, Sec 15: W/2')
trs_list = pytrs.TRSList()
trs_list.extend(plssdesc)

# or even...
trs_list = pytrs.TRSList(plssdesc)
```
(In either case, `trs_list` contains `TRS` objects for `154n97w14` and `154n97w15`.)


### Sorting / Filtering / Grouping

We can sort, filter, or group `TRSList` objects, essentially the same [as with `TractList` objects](https://github.com/JamesPImes/pyTRS/blob/master/guides/guides/sort_filter_group.md#guide-to-sorting--filtering--grouping-tract-objects-in-a-tractlist-or-plssdesc):
```
trs_list = pytrs.TRSList(['154n97w14', '154n97w14', '154n97w15', '155n97w22'])
trs_list.custom_sort(sort_key='s,r,t')
group_dict = trs_list.group(by_attribute='twprge', sort_key='s,r')
selected = trs_list.filter(key=lambda x: x.twprge = '154n97w')
discarded = trs_list.filter_duplicates(drop=True)
``` 

## Get a regular list of strings with `TRSList.to_strings()`

Use this method to get a regular list of strings in the pyTRS standard format.

```
trs1 = pytrs.TRS('154n97w14')
trs2 = pytrs.TRS('154n97w01')
trs_list = pytrs.TRSList([trs1, trs2])

plain_list = trs_list.to_strings()
```

In this example, `plain_list` is simply `['154n97w14', '154n97w01']` (holding strings).