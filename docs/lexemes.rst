lexemes.txt
===========

This section is under construction.

Introduction
------------

``lexemes.txt`` contains the dictionary, i.e. list of all lexemes together with their dictionary characteristics and inflectional types. This is how a simple lexeme entry could look like (example from Meadow Mari)::

    -lexeme
     lex: кандаш
     stem: кандаш.//8.
     gramm: NUM,short
     paradigm: NUM_consonant
     trans_en: eight

The ``-lexeme`` line starts a new entry. An entry contains a number of key-value pairs, each with an indent of one whitespace. Indentation is therefore an important part of the format rather than a stylistic tool. Unlike in JSON objects or dictionaries in many programming languages, it is allowed in some cases to use the same key multiple times, e.g. to write ``k: v1`` and then ``k: v2`` on another line. In this case, the field ``k`` is treated as having a list of values, ``[v1, v2]``.

Pre-defined fields that have to be present in each lexeme are the following:

* ``lex`` stands for lemma, or dictionary form, of the lexeme.
* ``stem`` contains a string describing the stem of the lexeme as a morpheme object (see :doc:`format overview </format>`). If there are several free variants, i.e. variants that are equally possible in any context, they may be written inside one value separated by ``//``. In the example above, the stem of the numeral *eight* in Meadow Mari can be written either as a word *кандаш* or as a numeral *8*. In both cases, affixes can only attach to the right side of it, which is why there is a dot at the right. A stem can only include the root morpheme or be a combination of a root with some (probably non-productive) derivational affixes that you want to treat as a single lexeme (see ``Morpheme segmentation in the stem`` below).
* ``gramm`` contains tags separated by a comma. Normally tags for a lexeme would include its part of speech (``NUM`` in this case) and, possibly, some dictionary categories such as gender / noun class for nouns or transitivity for verbs.
* ``paradigm`` is a link to the inflectional paradigm for this lexeme, which describes how forms of this lexeme can be produced from its stem(s). Even if the lexeme can not be inflected (e.g. it's a conjunction), there has to be a link, which should in this case lead to a paradigm with a single empty affix. The value must be a name of a paradigm listed in :doc:`paradigms.txt </paradigms>`. There may be multiple paradigm links specified by multiple ``paradigm`` keys.

The rest is optional.

* ``gloss`` (absent here) can contain the gloss for the stem, in case you switch on glossing. All stems without this field present will be glossed as ``STEM``.
* Any other field with a string value can be added. In the example above, the lexeme contains an English translation in the ``trans_en`` field. (A translation into a metalanguage may coincide with the gloss, but generally it needs not be that concise.)

Multiple stems
--------------

If a lexeme has multiple stem allomorphs that are chosen based on grammatical or phonological context, i.e. are not free variants, they can be listed in the ``stem`` field separated by a ``|`` (no whitespaces). If there is a ``gloss`` field, it should either contain a single gloss for all allomorphs, or have exactly the same amount of glosses, one for each allomorphs, also separated by a ``|``. Here is an example from Komi-Zyrian::

 -lexeme
  lex: борд
  stem: борд.|бордй.
  gramm: N,body
  gloss: wings|wings.OBL
  paradigm: Noun-num-obl_j
  trans_en: wings

The stems are automatically numbered by ``uniparser-morph``: the first stem, *борд.*, is considered to have the number 0, while *бордй.* has the number 1. These numbers can be used in :doc:`paradigms.txt </paradigms>` to specify which morpheme requires which stem allomorph.

Morpheme segmentation in the stem
---------------------------------

Although in many cases what you describe as the stem only consists of one morpheme, it can also be a combination of a root and a number of derivations. If you enable glossing and want the stem to be split into several morphemes, each with a separate gloss, you can indicate the morpheme and gloss breaks with the ``&`` character. (Note that this is done with a different character than in the :doc:`paradigms </paradigms>` for historical reasons.) This could make sense in the case of not-very-productive derivations that you wouldn't describe in the paradigms, but would still like to see in the annotation. Here is an Udmurt example::

 -lexeme
  lex: котькуд
  stem: коть&куд.
  gramm: ADJPRO
  gloss: INDEF&which
  paradigm: Noun-mar
  trans_en: whichever

The ``&`` character splits the stem, ``котькуд``, in two parts: ``коть``, an indefiniteness marker glossed as ``INDEF``, and the root ``куд``, glossed ``which``.

Stem morpheme segmentation is designed for concatenative morphology and is not intended for stems that allow infixes.

This notation also works for :doc:`clitics </clitics>`.