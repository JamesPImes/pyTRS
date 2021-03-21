
# Guide to `Config` objects and `config=` parameters

The parsing of `PLSSDesc` and `Tract` objects is configured with `Config` objects (or equivalent `config=` parameters).

To configure a `PLSSDesc` or `Tract` object, encode all of the desired parameters into a single string, separated by comma (spaces are optional with no effect).

```
chosen_config_options = 'n, w, segment, clean_qq, parse_qq'

# Now pass it to `config=` when creating a PLSSDesc.
some_plssdesc = pytrs.PLSSDesc(
    'T154N-R97W Sec 14: NE/4',
    config=chosen_config_options")

# Or  to `config=` when creating a Tract.
some_tract = pytrs.Tract(
    'NE/4',
    trs='154n97w14',
    config=chosen_config_options)
```

### `config=` parameters vs. equivalent parsing method parameters

Essentially all config parameters have corresponding parameters in the `PLSSDesc.parse()` and/or `Tract.parse()` methods (or associated methods). For example, `'clean_qq'` can be one of the `config=` parameters, and/or specified as `clean_qq=True` when calling either `PLSSDesc.parse()` or `Tract.parse()`.

*__Wherever `config=` parameters (passed at init) are later in conflict with a parameter in a `.parse()` method, the method's parameter will control.__*

On the other hand, calling `PLSSDesc.parse()` without specifying `clean_qq=` will cause it to look to however the object was configured via `config=` when it was created.


### Reconfiguring a `PLSSDesc` or `Tract` later

We can also (re)configure a `PLSSDesc` or `Tract` object later by setting its `.config` attribute, but there are two caveats to know:

1) Setting the `.config` will not cause the object to be parse. You must trigger that by calling `.parse()`.

2) Doing it this way will ONLY enact the parameters *__specifically__* included in the newly assigned `.config`. It will *__not__* reset any defaults or overwrite any __other__ prior config settings for that object. 
  
```
chosen_config_options = 'n, w, segment, clean_qq, parse_qq'

some_plssdesc = pytrs.PLSSDesc('T154N-R97W Sec 14: NE/4')
some_plssdesc.config = chosen_config_options
some_plssdesc.parse()

some_tract = pytrs.Tract('NE/4', trs='154n97w14')
some_tract.config = chosen_config_options
some_tract.parse()
```


## `Config` parameter table

Note: Including a parameter that affects only `PLSSDesc` objects in the `config=` for a `Tract` object (or vice versa) will not break anything -- it will simply have no effect for that object type. (In fact, passing the `Tract` config parameters to a `PLSSDesc` object will control the behavior of the `Tract` objects created by that `PLSSDesc`.) 

[# TODO: Link to the various sections where appropriate] 

|Config Parameter |Default|PLSSDesc|Tract|Footnote |Link |Effect |
|-----------------|:-----:|:------:|:---:|:-------:|:---:|:------|
|`'n'` or `'default_ns.n'`	|x *	|x	|x **	|1 *, 2 **	|	|Assume any missing N/S in a Twp should be 'n'	|
|`'s'` or `'default_ns.s'`	|	|x	|x **	|1, 2	|	|Assume any missing N/S in a Twp should be 's'	|
|`'w'` or `'default_ew.w'`	|x *	|x	|x **	|1 *, 2 **	|	|Assume any missing E/W in a Rge should be 'w'	|
|`'e'` or `'default_ew.e'`	|	|x	|x **	|1, 2	|	|Assume any missing E/W in a Rge should be 'e'	|
|`'wait_to_parse'`	|	|x	|	|	|	|Hold off on parsing PLSSDesc object at init	|
|`'parse_qq'`	|	|x	|x	|	|	|Populate lots/aliquots in a `Tract` object (or in a `PLSSDesc` object's subordinate `Tract` objects) when created.	|
|`'init_preprocess'`	|	|x	|x	|3	|	|Will preprocess description at init	|
|`'init_preprocess.False'`	|x	|x	|x	|3	|	|Will NOT preprocess description at init	|
|`'clean_qq'`	|	|	|x	|	|xx	|expect ONLY clean aliquots/lots (no metes-and-bounds, exceptions, etc.)	|
|`'require_colon'`	|x	|x	|	|7	|	|Require a colon between Section number and its following description block (on a 'first-pass' attempt at a parse only)	|
|`'require_colon.False'`	|	|x	|7	|	|	|Do not require a colon in that position	|
|`'include_lot_divs'`	|x	|	|x	|	|	|Report lot divisions (i.e., `'N/2 of Lot 1'` -> `'N2 of L1'`)	|
|`'include_lot_divs.False`	|	|	|x	|	|	|Do NOT report lot divisions (i.e. just `'L1'`, even if divided further)	|
|`'ocr_scrub'`	|	|x	|x **	|2	|	|Scrub common OCR artifacts from the text	|
|`'ocr_scrub.False'`	|x	|x	|x **	|2	|	|Do NOT scrub OCR artifacts from the text	|
|`'segment'`	|	|x	|	|	|	|Segment PLSS description before parsing into `Tract` objects. (MIGHT capture descriptions with multiple layouts.)	|
|`'segment.False`	|x	|x	|	|	|	|Do NOT segment the description before parsing.	|
|`'qq_depth_min.<number>`	|x (=`2`)	|	|x 	|4	|xx	|specify the MINIMUM 'depth' to parse aliquots. Value of `2` renders quarter-quarters (QQs).	|
|`'qq_depth_max.<number>`	|	|	|x	|4	|xx	|specify the MAXIMUM 'depth' to parse aliquots, and discard any smaller divisions.	|
|`'qq_depth.<number>`	|	|	|x	|4	|xx	|specify the EXACT 'depth' to parse aliquots, and discard any smaller divisions.	|
|`'break_halves'`	|	|	|x	|4, 5	|	|break all aliquot halves into quarters, EVEN IF we're at divisions smaller than the specified `qq_depth_min`.	|
|`'break_halves.False`	|x	|	|x	|4, 5 |xx	|Leave aliquot halves as halves when we're at divisions smaller than the specified `qq_depth_min`	|
|`'TRS_desc'`	|	|x	|	|Y	|xx	|Force the parser to use `TRS_desc'` layout	|
|`'desc_STR'`	|	|x	|	|Y	|xx	|Force the parser to use `desc_STR'` layout	|
|`'S_desc_TR'`	|	|x	|	|Y	|xx	|Force the parser to use `S_desc_TR'` layout	|
|`'TR_desc_S'`	|	|x	|	|Y	|xx	|Force the parser to use `TR_desc_S'` layout	|
|`'copy_all'`	|	|x	|	|Y	|xx	|Force the parser to use `copy_all'` layout	|


1) Objects for which `default_ns` or `default_ew` is not specified will fall back to the class attributes `PLSSDesc.MASTER_DEFAULT_NS` and `PLSSDesc.MASTER_DEFAULT_EW` (which are `'n'` and `'w'` unless changed by the user). If your data is from an area where you expect only South townships or East ranges, it may be simpler to set those `PLSSDesc` class attributes instead. 

2) `default_ns`, `default_ew`, and `ocr_scrub` currently only affect `Tract` objects that are created via the `Tract.from_twprgesec()` method.

3) Preprocessing is done automatically whenever an object is parsed. Using `init_preprocess` is only relevant if you do not parse at init but want to see the preprocessed description anyway.

4) The size of the aliquots that get parsed is controlled by `qq_depth` or its `qq_depth_min` / `qq_depth_max`. Setting `qq_depth` will override `qq_depth_min` and `qq_depth_max`. By default (`qq_depth_min.2`), aliquots are parsed to quarter-quarters (QQs) but allows for smaller divisions if they exist in the description). See the section on `qq_depth` etc. for more details. [# TODO: LINK]

5) In aliquot parsing, `break_halves` forces all halves into the equivalent quarters--e.g., `'W2SENE'` -> [`'NWSENE'`, `'SWSENE'`]. The effect of `break_halves` is only *noticeable* if the halves occur 'deeper' than the `qq_depth_min` (otherwise the halves would be broken into quarters anyway). See the section on `qq_depth` etc. for more details. [# TODO: LINK]

6) Forcing the parser to assume a specific `layout` is generally not advised, unless you are certain that all of the descriptions in your dataset have the same layout.

7) `require_colon` only impacts `'TRS_desc'` and `'S_desc_TR'` layouts -- i.e. layouts where description block follows the section number.


### Some specific parameters


#### `clean_qq` for expanded aliquot parsing
If you know you have a very clean dataset, with nothing but simple aliquots and lots (i.e. no metes-and-bounds descriptions, exceptions, etc.) then we can use `'clean_qq'`.
 
This parameter can be used in either a `PLSSDesc` or `Tract`.

*__Note:__* When used in a `PLSSDesc` object, `'clean_qq'` will *__not__* affect how many `Tract` objects are found--only how broadly those `Tract` objects should look for aliquots.

Here, in a `PLSSDesc`:
```
raw_desc = 'T154N-R97W Sec 14: NE'

plssdesc1 = pytrs.PLSSDesc(raw_desc, parse_qq=True, config='clean_qq')
plssdesc1.parsed_tracts[0].qqs      # -> ['NENE', 'NWNE', 'SENE', 'SWNE']

# Without specifying 'clean_qq' we won't find any aliquots.
plssdesc2 = pytrs.PLSSDesc(raw_desc, parse_qq=True)
plssdesc2.parsed_tracts[0].qqs      # -> []
```

Here, in a `Tract`:
```
tract_txt = 'Lots 1 - 3, NE'

tract2 = pytrs.PLSSDesc("NE", parse_qq=True, config='clean_qq')
tract2.lots_qqs      # -> ['L1', 'L2', 'L3', NENE', 'NWNE', 'SENE', 'SWNE']

# Without specifying 'clean_qq' we won't find the aliquots.
tract1 = pytrs.Tract(tract_txt, parse_qq=True)
tract1.lots_qqs      # -> ['L1', 'L2', 'L3']
```

`'NE'` as it appears in the text in these examples is __intended__ as the "Northeast Quarter" but can't be recognized as such without `'clean_qq'`. The reason for this is to avoid a ton of unwanted false matches in real-world data. That is, we don't want to interpret `'The west one hundred feet of the SW/4'` as `'The west oNE¼ hundred feet of the SW/4'` (i.e. the SW/4 __and__ the NE/4, which would happen under `'clean_qq'` parsing).

(Aliquot recognition of short but common abbreviations is an area for improvement in future versions.)


#### Control the granularity (or 'depth') of aliquot parsing with `qq_depth`, `qq_depth_min`, and/or `qq_depth_max`

By default, aliquots will be parsed into quarter-quarters ('QQs', or traditional 40-acre divisions), but will *__allow__* smaller divisions if they exist in the data. In this example, the `'SE/4NW/4'` describes a 40-acre division (already a QQ) whereas `'E/2NE/4NW/4'` describes a 20-acre parcel (being half of a QQ):

```
>>> tract_demo_default = pytrs.Tract(
        desc='SE/4NW/4, E/2NE/4NW/4',
        trs='154n97w14')
>>> tract_demo_default.parse()
>>> print(tract_demo_default.qqs)
['SENW', 'E2NENW']
```


##### `qq_depth_min`

If we want to *__force__* divisions smaller than 40 acres, we can set the config parameter `'qq_depth_min.<number>'`, where `<number>` specifies how many times to divide the section by 4. That is, the section will be divided (on a grid) into a number of pieces equal to `4^(depth)`.

The default is `'qq_depth_min.2'` (i.e. 16 quarter-quarters). But we can break it into 64 pieces (each 10-acres, assuming a 'perfect' section) with `qq_depth_min.3`, thus: 

```
>>> tract_demo_min = pytrs.Tract(
        desc='SE/4NW/4, E/2NE/4NW/4',
        trs='154n97w14',
        parse_qq=True,
        config='qq_depth_min.3')
>>> print(tract_demo_min.qqs)
['NESENW', 'NWSENW', 'SESENW', 'SWSENW', 'NENENW', 'SENENW']
```


##### `qq_depth_max`

If we want to *__prohibit__* (i.e. discard) divisions smaller than 40 acres, we can use the config parameter `'qq_depth_max.<number>'`, which works similarly. This will discard any divisions smaller than the specified depth. In this example, the `'E/2NE/4NW/4'` gets parsed as the `'NENW'`, thus:

```
>>> tract_demo_max = pytrs.Tract(
        desc='SE/4NW/4, E/2NE/4NW/4',
        trs='154n97w14',
        parse_qq=True,
        config='qq_depth_max.2')
>>> print(tract_demo_max.qqs)
['SENW', 'NENW']
```

*__WARNING__: `qq_depth_max` should be equal to or greater than `qq_depth_min`, or there will likely be more parsed QQs than actually exist in the data.*


##### `qq_depth` (i.e. exact QQ depth)

If we want to specify the *__exact__* size of *__every__* element, no bigger and no smaller, we can use the config parameter `'qq_depth.<number>'`, which is equivalent to setting `qq_depth_min` and `qq_depth_max` to the same number (which is how it is implemented behind the scenes).

```
>>> tract_demo_exact = pytrs.Tract(
        desc='SE/4NW/4, E/2NE/4NW/4',
        trs='154n97w14',
        parse_qq=True,
        config='qq_depth.2')
>>> print(tract_demo_exact.qqs)
['SENW', 'NENW']
```

*__Note__: If specified, `qq_depth` will override `qq_depth_min` and `qq_depth_max`.* 



##### Warning: Do not set `qq_depth_min` or `qq_depth` too high.

Because we're dealing with powers of 4, setting `qq_depth_min` or `qq_depth` to a value higher than 3 or 4 will quickly become very computationally expensive. `'ALL of Section 14, T154N-R97W'` parsed to a `qq_depth` of 5 will return a list of 1024 aliquot pieces, each 0.625 acres in size. And to a depth of 6 will return a list of 4096 aliquot pieces (each 0.15625 acres in size).

