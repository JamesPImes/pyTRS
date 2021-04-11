# CSV Parser

A GUI application for parsing PLSS descriptions in a .csv file.

![Screenshot01](https://github.com/JamesPImes/pyTRS/tree/master/samples/csv_parser/images/ss01.png)

Takes a [.csv file](https://github.com/JamesPImes/pyTRS/tree/master/samples/csv_parser/sample_data/sample_data.csv) containing raw PLSS descriptions and parses them, generating a [new .csv file](https://github.com/JamesPImes/pyTRS/tree/master/samples/csv_parser/sample_data/sample_data_pytrs_parsed.csv) with rows/columns inserted as necessary, such that there is one row per identified tract.

(`parse_csv.py` and `parse_csv.pyw` are identical, except that the latter will not show a console when run.)


#### Quick note

A version of this application had previously been included as a package of `pytrs` before the `v1.0.0` release, but I decided it wasn't worth maintaining as an official part of the library, so I'm including it here as a sample implementation. If nothing else, it demonstrates how the `pytrs.interface_tools` package can be used in a GUI application.
