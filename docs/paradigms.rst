paradigms.txt
=============

This section is under construction.

``paradigms.txt`` contains the rules of inflection as lists of affixes (or affix combinations) grouped into paradigms.

Introduction
------------

Two kinds of objects are used when describing morphology in ``uniparser-morph``: *paradigms* and *morphemes*, or *inflexions*. The ``paradigms.txt`` file is just a collection of paradigms, while each paradigm is basically a collection of morpheme objects.

A morpheme object can describe one real inflectional or productive derivational affix, but it can also describe a combination of multiple morphemes, or a part of a morpheme, or just some string that can appear in a word. In other words, morpheme objects do not have to coincide with "real" linguistic entities. We will henceforth use the term "morpheme" in this non-linguistic sense.

Each paradigm must have a name. The names are used for referencing paradigms in :doc:`the vocabulary </lexemes>` and in paradigm links (see below). Each paradigm starts with ``-paradigm: paradigm_name``; the contents of a paradigm must follow this line and have an indent of at least one whitespace.

Morphemes
---------

Each morpheme starts with ``-flex: ``, followed by a string that contains the characters that represent that morpheme in the orthography of your language, as well as certain special characters. Each morpheme has to have at least one dot (``.``), a special character indicating where the stem (or one part of a multi-part stem) can attach; see :doc:`the overview of the format </format>` for details.

After that, a number of lines, each indented one whitespace more that the first line, describe properties of the morpheme as key-value pairs. Two commonly used properties are ``gramm`` and ``gloss``. The former is a string that contains the list of tags associated with that morpheme, i.e. tags that should appear in the analysis of each word form that contains it. If there are multiple tags, they should be separated by a comma (no whitespaces). ``gloss`` contains the gloss for the morpheme, if you choose to have glossing; otherwise, you can omit it. The rest of the fields (see below) are optional.

