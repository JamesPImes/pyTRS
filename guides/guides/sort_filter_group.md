# Guide to Sorting / Filtering / Grouping `Tract` objects in a `TractList` or `PLSSDesc`

`PLSSDesc` has equivalent methods for [sorting](#sort) / [filtering](#filter) / [grouping](#group) the `Tract` objects in its `.tracts` attribute.

## <a name='sort'>`.sort_tracts()`</a>

Sort the `Tract` objects stored in this `TractList` (in place), with optional custom sort keys (see below).

Firstly, `sort_key=<lambda>` and `reverse=<bool>` parameters can be used here -- identical in behavior to the built-in `list.sort(key=<lambda>, reverse=<bool>)`, but note the parameter name here is `sort_key`, rather than `key`. (This is named `sort_key` because it is also a parameter in [the grouping methods](sort_filter_group.md#group), and it serves the same purpose there.)

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
|`'t'`	|	|Township	|1|
|	|`'t.num'`	|raw Township number (ignoring N/S)	||
|	|`'t.ns'`	|north-to-south	|2|
|	|`'t.sn'`	|south-to-north	|2|
|`'r'`	|	|Range	|1|
|	|`'r.num'`	|raw Range number (ignoring E/W)	||
|	|`'r.ew'`	|east-to-west	|2|
|	|`'r.we'`	|west-to-east	|2|
|`'s'`	|	|Section number	||

Footnotes:
1) If `'t'` or `'r'` is passed, it will sort by `'t.num'` and `'r.num'` respectively unless `'t.ns'` (etc.) is specified.

2) Baselines and principal meridians are not considered when sorting by north/south or east/west.

Use as many sort keys as you want. Place them all in a single string, separated by comma (spaces are optional). They will be applied in order from left-to-right, so place the highest 'priority' sort last (e.g., `'s, t.ns'` to first sort by section, then by township from north-to-south).

Reverse any or all of the custom keys by adding `'.reverse'` (or `'.rev'`) at the end of it.

*__Important__: The parameter `reverse=<bool>` has __no effect__ on these string-based custom keys. Instead, encode the intended reverse into the string itself, such as `'s.reverse'` (i.e. section number, highest-to-lowest).*

###### Example custom `sort_key`:

| Example | Outcome | Footnote |
|---------|------------------------------|:---:|
|`'s.reverse,r.ew,t.ns'` | Sort by section number (reversed, so largest-to-smallest);<br>then sort by Range (east-to-west);<br>then sort by Township (north-to-south)|  |
|`'i,s,r,t'`|Sort by original order;<br>then sort by Section (smallest-to-largest);<br>then sort by Range (smallest-to-largest);<br>then sort by Township (smallest-to-largest)| 1 |

Footnotes:
1) `'i,s,r,t'` is the default behavior of `.sort_tracts()` if no `sort_key` is passed.

Example use:

```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])

# sort by Section from largest to smallest (i.e. reverse), then sort 
# by Rge from east-to-west, then by Twp from north-to-south.
t_list.sort_tracts(sort_key='s.reverse,r.ew,t.ns')
```


Note that Twp/Rge's that are [errors](trs.md#error) or [undefined](trs.md#undefined) (i.e. `'XXXzXXXz'` or `'___z___z'`) will be sorted to the end of the list when sorting on Twp and/or Rge (whether by number, north-to-south, south-to-north, east-to-west, or west-to-east).  Similarly, [error Sections](trs.md#error) and [undefined sections](trs.md#undefined) (i.e. `'XX'` or `'__'`)](trs.md#error) will be sorted to the end of the list when sorting on section.  (The exception is if the sort is reversed, in which case, they come first.)



## <a name='filter'>`.filter()`</a>

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

## <a name='group'>`.group_by()`</a>

We can group `Tract` objects by attribute -- e.g., by Twp/Rge (all tracts in T154N-R97W, all those in T155N-R97W, etc.) -- into a dict, by using the `.group_by()` method on a `TractList` or `PLSSDesc`.

```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])
grouped_tracts = t_list.group_by(attribute='twprge')
```

It's hard to depict, but the dict stored above to var `grouped_tracts` looks like this, with each key being a unique `twprge` value among the tracts in the original `TractList`:
```
{
    '154n97w': 
        TractList(4)<['154n97w14: NE/4', '154n97w15: W/2', '154n97w16: W/2', '154n97w17: W/2']>,
    '155n97w':
        TractList(2)<['155n97w01: Lots 1 - 3, S/2N/2', '155n97w02: Lots 2, 4, SE/4']>,
    <etc.>
}
```

To demonstrate a bit more intuitively, let's get the `Tract` objects whose `.twprge` was `'154n97w'` (i.e. the `TractList` in the dict that is keyed by `'154n97w'`) and print some contents:
```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])

# Group by `.twprge` attribute values.
grouped_tracts = t_list.group_by(attribute='twprge')

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

#### Group by non-standard attributes

Grouping is *__not__* limited to only the `Tract` attributes that come standard in this library. You can assign custom attributes to the `Tract` objects and then group by that, so long as the values are a hashable type.

In this example, tracts are grouped by the number of aliquot quarter-quarters identified in each:

```
for tract in some_tractlist:
    tract.num_qqs = len(tract.qqs)
grouped_tracts = some_tractlist.group_by('num_qqs')
```

...Or whether any lot acreages were defined:
```
for tract in some_tractlist:
    tract.acres_defined = len(tract.lot_acres) > 0
grouped_tracts = some_tractlist.group_by('acres_defined')
```

#### Grouping by multiple attributes

If we pass a list of attribute names to `attributes=[<list of attribute names>]` instead of a single attribute, then the keys of the returned dict will be tuples, the elements of which line up with the listed attributes in `attributes`.

```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])

# Group by `.twp` and then by `.rge` attribute values.
grouped_tracts = t_list.group_by(attribute=['twp', 'rge'])
```
Again, it's hard to depict, but the dict stored to variable `grouped_tracts` looks like this, keyed by unique tuples of (`.twp`, `.rge` value pairs). Each value is still a `TractList` of the `Tract` objects whose corresponding attributes match the key tuple.
```
{
    ('154n', '97w'):
        TractList(4)<['154n97w14: NE/4', '154n97w15: W/2', '154n97w16: W/2', '154n97w17: W/2']>, 
    ('155n', '97w'):
        TractList(2)<['155n97w01: Lots 1 - 3, S/2N/2', '155n97w02: Lots 2, 4, SE/4']>, 
    ('155n', '98w'):
        TractList(2)<['155n98w31: SW/4NE/4', '155n98w32: SE/4NW/4']>, 
    ('155n', '96w'):
        TractList(1)<['155n96w27: ALL']>,
    <etc.>
}
```

To demonstrate, we'll get the `Tract` objects whose `.twp` was `'154n'` and whose `.rge` was `'97w'` (i.e. the `TractList` in the dict that is keyed by the tuple `('154n', '97w')` ), and then print some of their basic data to console:
```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])

# Group by `.twp` and then by `.rge` attribute values.
grouped_tracts = t_list.group_by(attribute=['twp', 'rge'])

# Get the tracts whose `.twp` is '154n' and `.rge` is '97w'.
t_list_154n97w = grouped_tracts[('154n', '97w')]

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
grouped_tracts = t_list_1.group_by(attribute='twprge')

grouped_tracts.keys()       # -> dict_keys(['154n97w', '155n97w'])

t_list_2 = pytrs.TractList.from_multiple([<some other list of tracts>])
t_list_2.group_by(attribute='twprge', into=grouped_tracts)

grouped_tracts.keys()       # -> dict_keys(['154n97w', '155n97w', '154n96w'])
```

Note: In the above example, the tracts are added to the `grouped_tracts` dict (because of parameter `into=grouped_tracts`), so it doesn't matter whether we re-assign the returned dict to var `grouped_tracts` (i.e. `into=grouped_tracts` and the dict returned by the method are the same object). New keys are added as necessary.

#### Sort the grouped tracts

Use the parameters `sort_key=` (and optionally `reverse=`) to sort *__each__* of the `TractList` objects in the dict of group tracts. (Takes any of the [options available in `.sort_tracts()` method](sort_filter_group.md#sort).)

An example using the `TractList` custom sort keys -- sorting by Range (number), then Township (north-to-south):
```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])
sorted_grouped_tracts = t_list.group_by(attribute='twprge', sort_key='r,t.ns')
```

An example using a lambda (i.e. using the built-in `list.sort()` functionality) -- in this case by the number of aliquots in each `Tract` (i.e. length of `.qqs` attribute):
```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])
sorted_grouped_tracts = t_list.group_by(
    attribute='twprge',
    sort_key=lambda tract: len(tract.qqs),
    reverse=True)
```

##### Sort the grouped tracts afterwards with the `sort_grouped_tracts()` function

Sort or resort a group without creating a new dict by using the `sort_grouped_tracts()` method.

```
t_list = pytrs.TractList.from_multiple([<some large list of tracts>])
grouped_tracts = t_list.group_by(attribute='twprge')

pytrs.sort_grouped_tracts(grouped_tracts, sort_key='r,t.ns')
```
