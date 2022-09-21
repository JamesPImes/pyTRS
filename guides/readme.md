# Guide to pyTRS
Copyright © 2021-2022, James P. Imes. All rights reserved.

*__Note:__ pyTRS is NOT licensed for any commercial or for-profit use. [Contact me](mailto:jamesimes@gmail.com) for licensing inquiries, or to inquire about my consulting, or just to say hello / offer feedback.*

__Note also:__ These guides are not intended to cover all of the functionality of pyTRS, but they will get you up and running for most purposes.

*__WARNING:__ As of v2.0.0 (September 2022) these guides are likely to be slightly outdated. I am working on updating them for the new version. The [official documentation](https://pytrs.readthedocs.io) on ReadTheDocs is the most accurate source of information. You may want to go there after you read the quickstart.*


## Table of Contents

| Guide                                                                                            | Main Topic                                                                                                                                | Main object<br>type(s) discussed                     |
|--------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|----------------------|
| [quickstart.md](guides/quickstart.md)                                                            | A bird's-eye view on getting started.                                                                                                     | `PLSSDesc`, `Tract` |
| [plssdesc.md](guides/plssdesc.md)                                                                | Parsing PLSS land descriptions into tracts.                                                                                               | `PLSSDesc`       |
| [tract_attributes.md](guides/tract_attributes.md)                                                | The names of data fields of parsed descriptions (i.e. `Tract` <br> attributes).                                                           | `Tract` |
| [tract.md](guides/tract.md)                                                                      | Parsing tracts into lots/aliquots.                                                                                                        | `Tract`          |
| [trs.md](guides/trs.md)                                                                          | The pyTRS standard format for Twp/Rge/Sec                                                                                                 | `TRS`, `TRSList` |
| [config.md](guides/config.md)                       | Configuring how the descriptions and lots/aliquots are parsed                                                                             | `PLSSDesc`, `Tract` |
| [extracting_data.md](guides/extracting_data.md) | Extracting data fields (e.g., township, range, section, description, <br>lots, aliquots, etc.) from tracts and land descriptions in bulk. | `Tract`, `TractList`, (`PLSSDesc`\*\*) |
| [tractlist.md](guides/tractlist.md)       | Working with tracts that were parsed from multiple land <br> descriptions, and/or multiple individually-created tracts.                   | `TractList` (`PLSSDesc`\*\*) |
| [sort_filter_group.md](guides/sort_filter_group.md) | Sorting, filtering, and grouping tracts (by Twp / Rge / Sec or <br>other attributes)                                                      | `TractList` (`PLSSDesc`\*\*) | 
| [tractwriter.md](guides/tractwriter.md)   | Streamlined writing of parsed data to .csv files                                                                                          | `TractWriter` \*\*\* |
| [examples.md](guides/examples.md)         | Some example uses of pyTRS                                                                                                                | n/a |

*\*\* `PLSSDesc` objects have most of the same methods as `TractList` objects for sorting, filtering, grouping, and extracting data. When a `PLSSDesc` object's method is used, it applies to that `PLSSDesc` object's own `.tracts` attribute.*

*\*\*\* The `TractWriter` class is imported from the `pytrs.tractwriter` package.*


### Quick note regarding the simple examples

I should point out that all of the examples in these guides use very simple descriptions just to demonstrate the functionality -- but the pyTRS library itself does a pretty good job of handling real world data, metes-and-bounds, etc. It can handle this description without issue:
```
Township 154 North, Range 97 West
Section 1: Lots 1 - 3 and the Southeast Quarter of the Northeast Quarter
Section 14: NE/4
Section 15: That portion of the W/2 lying south of the highway right-of-way
Township 155 North, Range 97 West
Sections 19 - 22: ALL
```
Or common abbreviations/symbols...
```
NE/4 of §14, 154N-97W       -> '154n97w14: NE/4'
```
Or even typos and some missing data (within reason)...
```
Twpnship 154 97 Wst
Sciton 14: Norhaest qrter
```
...becomes `'154n97w14: Norhaest qrter` (or `'154s97w14'` if configured to assume 'South' townships).

And I should also point out that all examples in these guides and in the code and its comments are dummy data or arbitrarily chosen.
