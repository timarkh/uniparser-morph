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

Each morpheme starts with ``-flex:``, followed by a string that contains the characters that represent that morpheme in the orthography of your language, as well as certain special characters. Each morpheme has to have at least one dot (``.``), a special character indicating where the stem (or one part of a multi-part stem) can attach; see :doc:`the overview of the format </format>` for details.

After that, a number of lines, each indented one whitespace more that the first line, describe the properties of the morpheme as key-value pairs. Two commonly used properties are ``gramm`` and ``gloss``. The former is a string that contains the list of tags associated with that morpheme, i.e. tags that should appear in the analysis of each word form that contains it. If there are multiple tags, they should be separated by a comma (no whitespaces). ``gloss`` contains the gloss for the morpheme, if you choose to have glossing; otherwise, you can omit it. The rest of the fields (see below) are optional.

Here is an example of a morpheme that represents English plural::

 -flex: .s
  gramm: pl
  gloss: PL

``.s`` means that the suffix *-s* attaches to the right side of the stem to produce a word form. In turn, stems have to end with a dot in order to be able to combine with this morpheme.

If you want one morpheme to be split into several affixes, each with a separate gloss, you can split both the morpheme string and the ``gloss`` value with ``|``. In this case, ``-flex`` and ``gloss`` must have equal number of non-empty regular parts::

 -flex: .a|bc|d
  gramm: ...
  gloss: GLOSS1|GLOSS2|GLOSS3

Paradigms
---------

Simple paradigms
^^^^^^^^^^^^^^^^

The simplest paradigm is a collection of morphemes each of which can attach to the same set of stems under same circumstances. For example, if you want to describe regular nominal morphology in English, you could have a paradigm like that::

 -paradigm: N_regular
  -flex: .
   gramm: sg
  -flex: .s
   gramm: pl
   gloss: PL
  -flex: .'s
   gramm: sg,poss
   gloss: POSS
  -flex: .s'
   gramm: pl,poss
   gloss: POSS.PL

The four morphemes it contains are an empty morpheme for singular, *s* for plural, *'s* for singular possessive form and *s'* for plural possessive form. You do not need a gloss for an empty morpheme. The paradigm is named ``N_regular``; all regular nouns in :doc:`the vocabulary </lexemes>` must have a link to ``N_regular``.

Paradigm links and agglutinative languages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The simple format outlined above is theoretically enough for describing any kind of language. If the morphology of your language is more complicated than that of English (which is probably the case), you could just list all possible combinations of affixes in a paradigm. However, this would be impractical for many morphologically rich languages, since there could be thousands or millions of such combinations. This calls for another strategy: describing pieces of morphology seperately, and then describing the way they can be combined. This is especially true for agglutinative languages, where affixes are many, but rules that govern their distribution are few.

The ``uniparser-morph`` format uses *paradigm links* to deal with this problem. The idea is that you describe different sets of affixes in different paradigms and then tell the system that affixes from paradigm *B* can attach to the affixes of paradigm *A* by putting a link from *A* to *B*. A link is introduced by the ``paradigm`` key; its value must be the name of the subsequent paradigm. There may be multiple paradigm links in a paradigm, each has to be written on a separate line.

Let's take a small fragment of Hungarian nominal morphology as an example. Among other categories, Hungarian nouns attach suffixes of number and case. Number suffixes attach to the right side of the stem, and case suffixes attach to the right side of the number suffix. This could be described in the following way::

 -paradigm: N_num
  -flex: .<.>
   gramm: sg
  -flex: .ok<.>
   gramm: pl
   gloss: PL
  paradigm: N_case
 
 -pardigm: N_case
  -flex: .
   gramm: nom
  -flex: .at
   gramm: acc
   gloss: ACC
  -flex: .ban
   gramm: iness
   gloss: INESS
  ...

In the first paradigm, ``.`` stands for the stem, as usual, while ``<.>`` denotes the place where one regular part (i.e. an uninterrupted fragment than contains regular characters) of the subsequent affix can appear. In the second paradigm, there are no ``<.>`` sequences because it is final: nothing can further attach to its affixes, because there are no links in it. The ``.`` in the second paradigm means "one part of a preceding affix that does not include ``<.>``". This way, when, for example, the morpheme ``.ok<.>`` combines with ``.at``, this is how different parts of each morpheme match parts of the other morpheme:

+-------+--------+---------+
| ``.`` | ``ok`` | ``<.>`` |
+-------+--------+---------+
|     ``.``      | ``at``  |
+-------+--------+---------+

This results in a combined morpheme ``.ok|at`` with the gloss ``PL|ACC`` and ``gramm`` value of ``pl,acc``, which then can attach to the stem.

Keep in mind that the order of paradigms induced by the paradigm links only determines the order in which their morphemes can combine following rules outlined above. This order does not have to coincide with the left-to-right order of slots in a word template. While this is probably the easiest way of describing things in suffixing languages, prefixing or infixing languages may be better described in a different way. Consider the following example from Urmi (Assyrian Neo-Aramaic)::

 -paradigm: V_I_front
  -flex: вi..ə.<.>vin
   gramm: prog,cop.prs,1,sg,m.s
  -flex: вi..ə.<.>vən
   gramm: prog,cop.prs,1,sg,f.s
  -flex: вi..ə.<.>vit
   gramm: prog,cop.prs,2,sg,m.s
  ...
  paradigm: V_pro_ifx_front
 
 -paradigm: V_pro_ifx_front
  -flex: ..
   gramm: non_obj
  -flex: .in.
   gramm: 1.o,sg.o
  -flex: .əx.
   gramm: 1.o,pl.o
  ...

Here the paradigm ``V_I_front`` lists combinations of prefixes, infixes and suffixes for a certain class of verbs; note three dots in each of them for the consonants of a three-consonant stem characteristic for Semitic languages. Each affix contains a slot for a suffix that cross-references the direct object, thus splitting the morpheme string in two parts, one before ``<.>`` and one after. The paradigm ``V_pro_ifx_front`` contains affixes that can appear in this slot. Each of them has dots at both ends that correspond to the two parts of the morphemes from ``V_I_front``.

If different morphemes in a paradigm can attach different subsequent morphemes, they can have their own paradigm links, which have to be indented just like the other morpheme properties. This is what the first paradigm from the example above would look like if each morpheme had its own link::

 -paradigm: V_I_front
  -flex: вi..ə.<.>vin
   gramm: prog,cop.prs,1,sg,m.s
   paradigm: V_pro_ifx_front
  -flex: вi..ə.<.>vən
   gramm: prog,cop.prs,1,sg,f.s
   paradigm: V_pro_ifx_front
  -flex: вi..ə.<.>vit
   gramm: prog,cop.prs,2,sg,m.s
   paradigm: V_pro_ifx_front
  ...

More advanced stuff
-------------------

Free variants
^^^^^^^^^^^^^

If a morpheme has several variants, all which can appear in the same range of contexts and should be tagged the same, they can be listed in ``-flex`` separated by ``//`` (no whitespaces)::

 -flex: .a.//.b.//.c.
  gramm: abc
  gloss: ABC

If they are split into affixes with the ``|`` sign for glossing purposes, all variants have to contain the same number of affixes.

This convention only works for the string representation of morphemes. If, for example, you have an ambiguous morpheme that can mean either genitive or dative, you should create two morpheme objects, one tagged genitive and the other, dative.

Null morphemes
^^^^^^^^^^^^^^

If you turn on glossing and want an empty morpheme to be depicted as ``∅`` and have a gloss, you can put ``0`` in the place that corresponds to the null morpheme. For example, the English singular suffix could look like this::

 -flex: .0
  gramm: sg
  gloss: SG

Stem allomorphs
^^^^^^^^^^^^^^^

A lexeme in :doc:`the vocabulary </lexemes>` can have multiple stem allomorphs separated by ``|`` signs (henceforth just *stems*). Usually this means that certain stems can only be used in certain grammatical or phonological contexts. ``uniparser-morph`` numbers the stems in each lexeme: the first one is considered to have number 0, the next one, number 1, etc. If a morpheme can only be used with certain stems, you should specify their number(s) in angle brackets preceding the main part of the morpheme string. Angle brackets can contain one number or multiple numbers separated by a comma. If you have several free variants, do not forget to add a stem constraint in front of each of them::

 -flex: <0,2>.aaa//<0,2>.bbb
  gramm: pl

If a lexeme has only one stem, then these constraints do not have any effect. However if it has more than one stem, then it has to have a stem for each stem number referenced in the paradigm(s) it links to. E.g. if a paradigm has a morpheme that starts with ``<3>``, but a lexeme that links to it has less than 4 stems, that may lead to a parsing error.

If there are no stem constraints in a morpheme, it can attach to any stem.

Whenever two morphemes from different paradigms are combined (see above), the resulting morpheme gets the intersection of their stem constraints. For example::

 <2>.a<.> + .b = <2>.ab
 <0,1>.a<.> + <1>.b = <1>.ab
 <2>.a<.> + <1>.b = nothing

Stem parts
^^^^^^^^^^

Sometimes it is convenient to put certain stem characters into the paradigm. For example, in most languages with Cyrillic script, palatalization of consonants is not reflected in the consonant character itself. Instead, it can be marked either with a special "palatalizing" vowel character (like ``и``, which means "*i* + palatalization of the previous consonant"), or with the ``ь`` character ("soft sign"). If a stem ends in a palatalized consonant and the paradigm includes both morphemes that start with a palatalizing character and those that require a soft sign, you could list two stem allomorphs in the lexeme (one with the soft sign, the other without it) and then specify which morpheme requires which stem. However, it would be more convenient to have just one stem and include the soft sign in the morphemes that require it. The only problem of such an approach is that if you turn on glossing, the soft sign will become a part of the morpheme rather than the stem. In order to join it to the stem instead, you can surround it by square brackets::

 -paradigm: N_palatalized
  -flex: .[ь]
   gramm: nom,sg
  -flex: .и
   gramm: gen,sg
   gloss: GEN.SG

Morpheme IDs
^^^^^^^^^^^^

You can add an ``id`` field to morphemes and/or lexemes. IDs do not need to be unique and do not need to be assigned to each and every item. An analyzed word form will contain an ``id`` attribute if any of its parts had an ID. The value will contain the IDs of all its parts separated by a comma. Duplicate IDs will be truncated.

Incorporated words
^^^^^^^^^^^^^^^^^^

There are no tools for handling productive incorporation yet in ``uniparser-morph``. Nevertheless, some incorporation can be accounted for in the paradigms. That can work if you have a limited number of words, e.g. pronominal clitics, that can be incorporated or orthographically fused with other words (hosts). Such words can be described as morphemes with a special ``LEX`` tag. Units with a ``LEX`` tag are processed as ordinary morphemes during parsing, but a separate "subword" analysis is added for each of them as one of the postprocessing steps. A ``LEX`` tag should look like ``LEX:xxx:yyy``, where ``xxx`` is the lemma and ``yyy`` contains grammatical tags separated by a semicolon. (A semicolon is used so that a morpheme can have both ``LEX`` tags and regular tags, which are separated by a comma.)

Here is an example from Albanian::

 -paradigm: imper-act-pl-consonant
  -flex: .<.>ni
   gramm: 2,pl,imp,act
   gloss: IMP.2PL
   paradigm: IO_clitics_consonant
 
 -paradigm: IO_clitics_consonant
  -flex: .më.
   gramm: LEX:më:CLIT_PRO;gen_dat;1sg
   gloss: 1SG.GENDAT
  -flex: .na.
   gramm: LEX:na:CLIT_PRO;acc;1pl
   gloss: 1PL.ACC
  ...

These two paradigms describe a plural imperative form, where the suffix ``ni`` may be preceded by one of the object intraclitics, such as ``më`` (1sg genitive/dative). The form ``tregomëni`` 'show me' will be analyzed as follows by default (assuming JSON representation is used):

.. code-block:: javascript
  :linenos:
    
    {
        "wf": "tregomëni",
        "lemma": "tregoj",
        "gramm": "V,imp,act,2,pl",
        "wfGlossed": "trego-më-ni",
        "gloss": "show-1SG.GENDAT-IMP.2PL",
        "subwords":
        [
            {
                "wf": "",
                "lex": "më",
                "gramm": "CLIT_PRO,gen_dat,1sg"
            }
        ]
    }

This is how the same output looks in XML:

.. code-block:: xml

 <w><ana lex="tregoj" gr="V,imp,act,2,pl" parts="trego-më-ni" gloss="show-1SG.GENDAT-IMP.2PL"></ana><ana lex="më" gr="CLIT_PRO,gen_dat,1sg"></ana>tregomëni</w>

If you would like to avoid nested structures and flatten the analyses, set the ``flattenSubwords`` property of your ``Analyzer`` instance to ``True``. This is what you will get for the same example in that case:

.. code-block:: xml

 <w><ana lex="tregoj+më" gr="V,imp,act,2,pl,CLIT_PRO,gen_dat,1sg" parts="trego-më-ni" gloss="show-1SG.GENDAT-IMP.2PL"></ana>tregomëni</w>

If you want the incorporated lexeme to be annotated with additional key-value pairs, you can add them to its tags as ``Key=Value`` strings, e.g.: ``LEX:më:CLIT_PRO;gen_dat;1sg;trans_en=I``.
