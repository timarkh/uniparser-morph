.. uniparser-morph documentation master file, created by
   sphinx-quickstart on Sat Feb 27 14:50:06 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Uniparser morphology
====================

``uniparser-morph`` is yet another rule-based morphological analysis tool. No built-in rules are provided; you will have to write some if you want to parse texts in your language. Uniparser-morph was developed primarily for under-resourced languages, which don't have enough data for training statistical parsers. Here's how it's different from other similar tools:

* It is designed to be usable by theoretical linguists with no prior knowledge of NLP (and has been successfully used by them). So it's not just another way of defining an FST; the way you describe lexemes and morphology resembles what you do in a traditional theoretical description, at least in part.
* It was developed with a large variety of linguistic phenomena in mind and is easily applicable to most languages -- not just the Standard Average European.
* Apart from POS-tagging and full morphological tagging, there is a glossing option (words can be split into morphemes).
* Lexemes can carry any number of attributes that have to end up in the annotation, e.g. translations into the metalanguage.
* Ambiguity is allowed: all words you analyze will receive all theoretically possible analyses regardless of the context. (You can then use e.g. CG_ for rule-based disambiguation.)
* While, in computational terms, the language described by ``uniparser-morph`` rules is certainly regular, the description is actually NOT entirely converted into an FST. Therefore, it's not nearly as fast as FST-based analyzers. The speed varies depending on the language structure and hardware characteristics, but you can hardly expect to parse more than 20,000 words per second. For heavily polysynthetic languages that figure can go as low as 200 words per second. So it's not really designed for industrial use.

.. _CG: https://visl.sdu.dk/constraint_grammar.html

The primary usage scenario I was thinking about is the following:

* You have a corpus of texts where you want to add morphological annotation (this includes POS-tagging).
* You manually prepare a grammar for the language in ``uniparser-morph`` format (probably making use of existing digital dictionaries of the language).
* You compile a list of unique words in your corpus and parse it.
* Then you annotate your texts based on this wordlist with any software you want.

Of course, you can do other things with ``uniparser-morph``, e.g. make it a part of a more complex NLP pipeline; just make sure low speed is not an issue in your case.

If you want to write rules for your language, see :doc:`Format overview </format>` for ``uniparser-morph`` format description. If you already have a grammar and would like to know how to analyze texts with it, see :doc:`Usage </usage>`.

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   usage
   format
   lexemes
   paradigms
   bad_analyses
   lex_rules
