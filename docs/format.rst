Format overview
===============

This section is under construction.

Introduction
------------

Morphological description of a language in ``uniparser-morph`` format requires at least two files:

* :doc:`lexemes.txt </lexemes>` contains the dictionary (lexemes, their POS tags, stem allomorphs etc.);
* :doc:`paradigms.txt </paradigms>` contains the inflectional information (affixes and rules of their combination).

There are also a number of optional files (see table of contents).

When trying to parse a word, ``uniparser-morph`` basically tries to split it into a combination of a stem (taken from ``lexemes.txt``) and a number of affixes (taken from ``paradigms.txt``). For each split that conforms to the rules described in those files, the word gets an analysis. The attributes of the analysis (lemma, tags etc.) are taken from the stem and affixes found. If no such split is possible, the word remains unanalyzed; there is no guesser of any form.

The description of the morphology in ``uniparser-morph`` is based on some principles that make it different from both a purely theoretical morphological description and some other rule-based analyzers:

* There is no "deep level" of any kind; all characters in stems and affixes must directly match those found in words. Sometimes this may result in a longer description, e.g. in the case of a language with an orthography that does not reflect its phonology in a straightforward way. (For example, in Cyrillics, palatalization of consonants can be marked by the choice of the neighboring vowel letter.) Still, such a description is usually more theory-neutral and easy to understand.
* There is no need for linguistic accuracy. For example, if, for some practical reason, it is easier to add a final consonant of some stems to the affixes, it's okay to do so. Or you could list all combinations of affixes in a simple flat list rather than describing them as separate categories occupying different slots. You should only care for the accuracy if you want glossing.
* If you are familiar with FieldWorks_ parsers, there are several important differences, apart from the aforementioned ones:

    * There is no unified list of morphemes; stems/roots and productive affixes are described in different places.
    * There are no "word templates": how stems and affixes combine with each other is described by links from one lexeme or paradigm to another, and by affix- or paradigm-level constraints.
    * Just as in corpus linguistics (meaning mainstream corpus linguistics dealing with large corpora of relatively well-described languages), the primary result of the analysis is *lemmatization* and *tagging*. It means that an analysis of a word should contain, first of all, its lemma (dictionary form) and a set of tags (part of speech and tags referring to other grammatical or lexical categories). Glossing and morpheme breaks are purely optional; you could turn them on, but you don't have to.

Morphemes
---------

As said before, there is no need for linguistic accuracy when describing morpheme boundaries. In what follows, a *morpheme* is understood as a string in a ``uniparser-morph`` description object that resides either in ``lexemes.txt`` or in ``paradigms.txt``. It can be either a real morpheme (stem or affix), or a combination of several affixes, or just some string that can occur within a word.

Each morpheme can contain regular characters and special sequences. Regular characters (letters, hyphens, digits etc.) will be used by the analyzer to find a match in the word. An uninterrupted sequence of regular characters constitutes one regular part of the morpheme. A regular part may be empty; there may be multiple regular parts in a morpheme. Special characters are used to define how morphemes combine with each other.

The main special character, used in both the dictionary and the paradigms, is ``.``. In a stem, it means "one regular part of an affix"; in an affix, it means "one regular part of a stem". When combining a stem with an affix, the stem's dots should match regular parts of the affix, and vice versa. All regular parts must be accounted for; matching starts from the stem. For example, the stem of an English noun "cat" could look like ``cat.``, the singular morpheme would look like ``.``, and the plural morpheme, like ``.s``. This is how the stem is combined with the plural affix:

+---------+-------+
| ``cat`` | ``.`` |
+---------+-------+
| ``.``   | ``s`` |
+---------+-------+

When the analyzer encounters the word "cats", it will find this split and produce an analysis, taking the lemma and the part of speech tag from the description of the lexeme with the stem ``cat.``, and the ``pl`` tag from the description of the morpheme ``.s``.

Here is a more complex example from Turoyo (Afro-Asiatic family). The three-consonant stem of the verb 'take' is ``.m.y.d.`` (with dots for potential prefixes, infixes and suffixes); a combination of morphemes that expresses future tense, 3sg subject and 3sg masculine object is ``g.o.a.le``. This is how they combine to produce the form ``gmoyadle``:

+-------+-------+-------+-------+-------+-------+--------+
| ``.`` | ``m`` | ``.`` | ``y`` | ``.`` | ``d`` | ``.``  |
+-------+-------+-------+-------+-------+-------+--------+
| ``g`` | ``.`` | ``o`` | ``.`` | ``a`` | ``.`` | ``le`` |
+-------+-------+-------+-------+-------+-------+--------+

When the same stem is joined with the combination of affixes ``.a..atli`` (present, 2sg subject, 1sg object) to form ``maydatli``, two of the stem's dots match empty regular sequences in the affix:

+-------+-------+-------+-------+-------+-------+----------+
| ``.`` | ``m`` | ``.`` | ``y`` | ``.`` | ``d`` | ``.``    |
+-------+-------+-------+-------+-------+-------+----------+
|       | ``.`` | ``a`` | ``.`` |       | ``.`` | ``atli`` |
+-------+-------+-------+-------+-------+-------+----------+


.. _FieldWorks: https://software.sil.org/fieldworks/