
# Guide to `TractList` objects

`TractList` objects are an emulation of the built-in `list`, with added functionality to:

* type-check any objects that are added to it (if an object other than a `Tract` is appended, it will raise a `TypeError`, although it can also unpack `Tract` objects out of `PLSSDesc`, `TractList` or other iterables that hold any of those object types -- see the `.from_multiple()` method).

* compile `Tract` data to lists or dicts, or write it to .csv files (see [the guide on extracting `Tract` data in bulk](https://github.com/JamesPImes/pyTRS/blob/master/guides/guides/extracting_data.md#guide-to-extracting-data-in-bulk-from-parsed-objects)).

* [sort the `Tract` objects](https://github.com/JamesPImes/pyTRS/blob/master/guides/guides/sort_filter_group.md#sort_tracts) using custom sort keys (e.g., by Township, Range, Section).

* [filter the `Tract` objects](https://github.com/JamesPImes/pyTRS/blob/master/guides/guides/sort_filter_group.md#filter) into new `TractList` objects, and optionally remove them from the original `TractList` (e.g., removing duplicates, removing errors, finding any whose `.twprge` is `'154n97w'` etc.).

* [group the `Tract` objects](https://github.com/JamesPImes/pyTRS/blob/master/guides/guides/sort_filter_group.md#group) by their shared attribute values -- e.g., by Twp/Rge.

With only a few exceptions\*\*, any method in the `TractList` class has an equivalent method in the `PLSSDesc` class. The `PLSSDesc` will apply the method to its own tracts (i.e. the `Tract` objects in its `.tracts` attribute, which is a `TractList` itself).

*\*\* `PLSSDesc` objects do not have the constructor method `.from_multiple()`, nor some of the non-public methods, nor emulations of any built-in `list` methods.*

## Creating a `TractList` (or equivalent `generator`)

If we need a collection of `Tract` objects, create a `TractList` by [initializing with `TractList()`](https://github.com/JamesPImes/pyTRS/blob/master/guides/guides/tractlist.md#creating-a-tractlist-or-equivalent-generator) or with the [more robust `TractList.from_multiple()` method](https://github.com/JamesPImes/pyTRS/blob/master/guides/guides/tractlist.md#robustly-construct-a-tractlist-from-multiple-sources-with-from_multiple).


### Constructing a `TractList` from a single iterable

We can create a `TractList` just like using the built-in `list()` function -- except that the iterable we pass must contain only `Tract`, `PLSSDesc`, and/or `TractList` objects.

```
normal_list = [tract1, tract2, plssdesc1, another_tractlist]
some_tractlist = pytrs.TractList(normal_list)
```

If the iterable includes an object of any other kind, it will raise a `TypeError`.
```
bad_list = ['foo', tract1, tract2, plssdesc1, another_tractlist]
some_tractlist = pytrs.TractList(bad_list)
```
Raises... 
```
TypeError: TractList will accept only type `pytrs.Tract`. Iterable contained <class 'str'>.
```

### Robustly construct a `TractList` from multiple sources with `.from_multiple()`

Use the `TractList.from_multiple()` method to get a new `TractList` from multiple sources. This has roughly the same behavior as initializing with `TractList()`, except that (a) it will also unpack *__nested__* lists and list-like objects...

```
normal_list1 = [tract1, tract2]

nested_list = [normal_list1, another_tractlist]

# This would raise a TypeError:
# some_tractlist = pytrs.TractList(nested_list)

# This is fine.
some_tractlist = pytrs.TractList.from_multiple(nested_list)
```

...and (b) we __do *not*__ need to first put the objects inside an iterable for `.from_multiple()`.
```
some_tractlist = pytrs.TractList.from_multiple(tract1, tract2, some_plssdesc)
``` 


## Extracting `Tract` data in bulk

See [the separate guide](https://github.com/JamesPImes/pyTRS/blob/master/guides/guides/extracting_data.md#guide-to-extracting-data-in-bulk-from-parsed-objects) on this functionality.