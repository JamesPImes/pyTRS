These docs are auto-generated from the docstrings, and they're probably more complicated than any user probably needs, and the rST needs to be cleaned up! Essentially everything is documented directly in the docstrings, so if you're banging your head against the walls here, you might check the docstrings directly.  *(Sorry! I'm getting to it as I have time!)*

The primary classes in this library get imported to the top-level when you `import pyTRS`, but they are actually implemented in a deeper package (e.g., the `pyTRS.PLSSDesc` class is actually implemented in `pyTRS.parser.parser.PLSSDesc`, which is where you'll find docs for it).

It makes for simple access in code, but it means the relevant docs are not where you would assume.

|Access the class as...	|Find its docs at...				|
|-----------------------|-----------------------------------|
|`pyTRS.PLSSDesc` 		| `pyTRS.parser.parser.PLSSDesc`	|
|`pyTRS.Tract` 			| `pyTRS.parser.parser.Tract`		|
|`pyTRS.Config` 		| `pyTRS.parser.parser.Config`		|
|`pyTRS.TractList` 		| `pyTRS.parser.parser.TractList`	|


