# pyTRS Quick Start Guide
*(__Note:__ This guide assumes that you are already familiar with the [PLSS](https://en.wikipedia.org/wiki/Public_Land_Survey_System) and its terminology.)*

## Bird's Eye View

pyTRS is imported as `pytrs`.

The two primary parsing classes in the library are [`PLSSDesc`]() and [`Tract`](), which are automatically imported as top-level classes when importing `pytrs` (accessable as `pytrs.PLSSDesc` and `pytrs.Tract`, even though they are implemented as `pytrs.parser.parser.PLSSDesc` and `pytrs.parser.parser.Tract`).

The conceptual difference between these two classes is that a `Tract` object represents land within a single, specific section; whereas a `PLSSDesc` object can represent land across any number of sections (in a single township, or across multiple townships).

Parsing a `PLSSDesc` object will creates one or more `Tract` objects.

`Tract` objects can also be created directly, for when our dataset already has the description blocks separated from their respective Twp/Rge/Sec.

__Important Note:__ Twp/Rge/Sec is represented in this library as a string, using a standardized format. `Section 14 of T154N-R97W` becomes `'154n97w14'`; whereas `Section 1 of T7S-R9E` becomes `'7s9e01'`.  See [the guide on `TRS` objects]() more information.  [#TODO: Link]



### Parsing full PLSS land descriptions with `PLSSDesc` objects

Parse PLSS land descriptions into tracts with a `PLSSDesc` object.

```
import pytrs

raw_description = "T154N-R97W Sec 14: NE/4, Sec 15: W/2"

parsed_plssdesc = pytrs.PLSSDesc(raw_description)

# Extract some data from the parsed description with `.tracts_to_dict()`.
tract_data = parsed_plssdesc.tracts_to_dict(['twp', 'rge', 'sec', 'desc'])
```

In the above example, we stored a list to the variable `tract_data`, which holds two dicts (one for each `Tract` object identified when the description was parsed).

```
[
    # The first tract:
    {
        'twp': '154n',
        'rge': '97w',
        'sec': '14',
        'desc': 'NE/4'
    },
    
    # The second tract:
    {
        'twp': '154n',
        'rge': '97w',
        'sec': '15',
        'desc': 'W/2'
    }
]
```

See [the table here]() for all of the relevant data that can be extracted from a parsed `PLSSDesc` object.  [# TODO: LINK]

See [the guide here]() for the various methods for extracting the data. [# TODO: LINK]


### Parsing tracts into lots/aliquots with `Tract` objects

Imagine we already have a dataset with description blocks separated from their respective Twp/Rge/Sec -- perhaps a table or spreadsheet that looks like this:

|Line|Twp/Rge/Sec| Twp | Rge | Sec | Description |
|:----:|:---:|:---:|:---:|:---:|:------------|
| 1 |"154n97w14"|154|97|14|"NE/4"|
| 2 |"154n97w15"|154|97|15|"W/2"|
| 3 |"154n97w01"|154|97|1|"Lots 1 - 3, S/2NE/4"|
|etc.| | | | | |

We can parse the text under `'Description'` block into lots/aliquots with `Tract` objects, and then access their `.lots`, `.qqs` (i.e. quarter-quarters), and `.lots_qqs` attributes. Pass parameter `parse_qq=True` when creating a `Tract` object to instruct it to populate its lots/aliquots.

```
import pytrs

tract_3 = pytrs.Tract('Lots 1 - 3, S/2NE/4', trs='154n97w01', parse_qq=True)

print(tract_3.lots)         # -> prints "['L1', 'L2', 'L3']"
print(tract_3.qqs)          # -> prints "['SENE', 'SWNE']"
print(tract_3.lots_qqs)     # -> prints "['L1', 'L2', 'L3', 'SENE', 'SWNE']"
```

To create a `Tract` object without first compiling the Twp/Rge/Sec into the pyTRS standard format, use the `Tract.from_twprgesec()` method.

```
import pytrs

tract_1 = pytrs.Tract(
    'NE/4', twp=154, rge=97, sec=14, default_ns='n', default_ew='w', 
    parse_qq=True)

print(tract_1.trs)          # -> prints '154n97w14'
print(tract_1.twp)          # -> prints '154n'
```

(If we just care about parsing to lots/aliquots, we don't even need to specify Twp/Rge/Sec.)
