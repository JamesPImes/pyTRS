# `Tract` attribute table

Access these `Tract` attributes directly, or [compile them in bulk](https://github.com/JamesPImes/pyTRS/blob/master/guides/guides/extracting_data.md#guide-to-extracting-data-in-bulk-from-parsed-objects) with various methods.

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
| `.source`         | user-specified source of the data that was parsed <br> (specify `source=<any value>` at init) | (any)            	|          |
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

