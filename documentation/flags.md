Below is a guide to the various warning flags and error flags, along with their meanings. *__Absense of these flags does not mean that the results are accurate.__*

If using `pyTRS` in as a module:
* Access __warning flags__ in the `.wFlagList` of a `pyTRS.Tract` object or `pyTRS.PLSSDesc` object.
* Access __error flags__ in the `.eFlagList` of a `pyTRS.Tract` object or `pyTRS.PLSSDesc` object.

Otherwise, how/whether these flags are displayed to the user will depend on the software that uses pyTRS.

## Warning Flags

Any of these __could__ indicate that the description was incorrectly parsed, but not necessarily that a failure occurred.

* `'T&R_fixed<...>'` -- The referenced T&R was fixed by the pre-processing function (e.g., "Township 154, Range 97" to "T154N-R97W")
  **NOTE:** 'Fixing' T&R's relies on the defaultNS and defaultEW kwargs to know whether the township should be n/s and whether the range should be e/w. If the 'fixed' T&R is not correct, it is probably because defaultNS='s' or defaultEW='e' was not specified.
* `'TR_not_pulled<...>'` -- The referenced T&R was not pulled by the parsing function as part of a separate Tract (e.g., in "...less and except the wellbore of the Johnston #1 located in the NE/4NW/4 of Section 14, T154N-R97W" -- the 'T154N-R97W' does not apparently denote a new, separate Tract)

* `'sec_not_pulled<...>'` -- The referenced Section was not pulled by the parsing function as part of a separate Tract (similar to the example for 'TR_not_pulled...')

* `'multiSec_found<...>'` -- The program noticed a multi-section (or list of sections) -- as in, "Sections 14 and 16 - 20"
  **NOTE:** A Tract will typically be created for each section within such a list, with identical descriptions.

* `'multiSec_not_pulled<...>'` -- The referenced multi-Section was not pulled by the parsing function as part of a separate Tract (similar to the example for 'TR_not_pulled...')

* `'pulled_sec_without_colon'` -- The program allowed a section that was not followed by a colon (e.g., "T154N-R97W Sec 14 NE/4" -- which should typically appear with a colon, such as "Sec 14: NE/4")

* `'Unused_desc_<...>'` -- A chunk of text was not incorporated into a Tract description.

* `'nonSequen_Lots'` -- Lots were listed non-sequentially (e.g., "Lots 9 - 3")

* `'nonSequen_sec'` -- Sections were listed non-sequentially (e.g., "Sections 9 - 3")

* `'dup_sec<...>'` -- A section appeared more than once within a list of sections.

* `'dup_QQ'` -- An apparently duplicate quarter-quarter aliquot was identified within a given section

* `'dup_lot'` -- An apparently duplicate lot was identified within a given section

* `'isfa'` -- 'insofar as' language, or other similar limitations within the original description \*

* `'except'` -- the word 'except' (or similar) appears in the original description \*

* `'including'` -- the word 'including' appears in the description \*


\* __NOTE:__ `'isfa'`, `'except'`, and `'including'` represent particular challenges for automated parsing, which is why they are flagged any time triggering words are encountered.



## Error Flags:

Any of these indicates that an error almost definitely occurred.

* `'noSection'` -- No section was identified in the original description.

* `'noTR'` -- No Township and Range was identified in the original description.

* `'noText'` -- No text was fed into the original description (either an empty string, or a non-str value)

* `'Unused_TR<...>'` -- The referenced T&R did not get incorporated into a Tract as expected.

