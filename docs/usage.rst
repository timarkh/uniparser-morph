Usage guide
===========

Basic usage
-----------

If you already have prepared the grammar rules in the right format, you have to put them in the same folder where you run your script. (If not, see :doc:`the format description </format>`.)

Import the ``Analyzer`` class from the package, create an instance and load your grammar files::

	from uniparser_morph import Analyzer
	a = Analyzer()
	a.load_grammar()

Now you can use one of several functions to analyze text in your language. Beware that despite having read the grammar files, the analyzer performs actual initialization when first asked to analyze something. Therefore, expect some delay after the first function call you make. Usually it takes several seconds to initialize things, but that depends on the language.

You can change the default settings by assigning non-default values to the properties of your ``Analyzer`` object, see :ref:`settings`.

Analyze sentences
^^^^^^^^^^^^^^^^^

If you want to analyze words or sentences on the fly, call ``analyze_words()``::

	analyses = a.analyze_words('Морфологияез')
	# If you pass a single string, you will get a list of Wordform objects
	# The analysis attributes are stored in its properties
	# as string values, e.g.:
	for ana in analyses:
		print(ana.wf, ana.lemma, ana.gramm, ana.gloss)

	# You can also pass lists (even nested lists) and specify
	# output format ('xml' or 'json')
	# If you pass a list, you will get a list of analyses with the same structure

	analyses = a.analyze_words([['А'], ['Мон', 'тонэ', 'яратӥсько', '.']],
	                           format='xml')
	# format='xml' means you will get an XML string
	# like <w><ana lex="..." gr="..." ...></ana>...</w>
	# for each token instead of a list of Wordform objects

	analyses = a.analyze_words(['Морфологиез', [['А'], ['Мон', 'тонэ', 'яратӥсько', '.']]],
	                           format='json')
	# format='json' means you will get a list of dictionaries
	# such as {'lemma': ..., 'gramm': [...], ...}
	# for each token instead of a list of Wordform objects

Disambiguation with Constraint Grammar
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, ``uniparser-morph`` analyses words in isolation. This leads to occasional ambiguity, whereby a word can have multiple plausible analyses, only one of which is correct in any given context. This is a general downside of rule-based approach to morphological analysis in comparison to machine-learning methods. However, you may use rules to (partially) remove the ambiguity. One way of doing that is using the `Constraint Grammar`_ rules. If you have a CG file you would like to use after analyzing the text, you can pass the path to it when calling ``analyze_words()``::

	analyses = a.analyze_words(['Мон', 'морфологиез', 'яратӥсько', '.'],
	                           cgFile=os.path.abspath('disambiguation.cg3'),
	                           disambiguate=True)

The analyzer will call the ``cg3`` executable to disambiguate your words. For this to work, you have to install CG3 separately. On Ubuntu/Debian, you can use ``apt-get``::

	sudo apt-get install cg3

On Windows, download the binary and add the path to the ``PATH`` environment variable. See `the documentation`_ for other options.

Note that each time you call ``analyze_words()`` with ``disambiguate=True``, the CG grammar is loaded and compiled from scratch, which makes the analysis even slower. If you are analyzing a large text, it would make sense to pass the entire text contents in a single function call rather than do it sentence-by-sentence, for optimal performance.

.. _Constraint Grammar: https://visl.sdu.dk/constraint_grammar.html
.. _the documentation: https://visl.sdu.dk/cg3/single/#installation

Analyze frequency lists
^^^^^^^^^^^^^^^^^^^^^^^

If you want to annotate a corpus before you use it, the best way of doing it is annotating the frequency list, where each word occurs only once. This is much faster than annotating the texts directly. However, you will have to compile a frequency list and then insert the analyses into the corpus on your own.

A frequency list has to be a CSV file (with any separator; default is tab) with two columns. The first column is the word to be analyzed (type), the second is its frequency. Frequencies are only needed to count the proportion of analyzed tokens at the end; if you do not need this, you can just assign the frequency of 1 to each word. The default name of the frequency list is ``wordlist.csv``; you have to put it to the current working directory. The rest is simple::

    a.analyze_wordlist()

When the analysis is over (which may take a while), two files will be generated in the current directory, one with the analyses, the other with the list of unanalyzed words in the same order as in the frequency list.

.. _settings:

Settings
--------

If you want to use some non-default parameter values, you can assign a value to one of the properties ``Analyzer`` instance or, in some cases, pass a named argument to a function yuo call. These are the most important properties:

* ``lexFile``: name of the :doc:`lexicon file </lexemes>`. Defaults to ``lexemes.txt``.
* ``paradigmFile``: name of the :doc:`paradigms file </paradigms>`. Defaults to ``paradigms.txt``.
* ``delAnaFile``: name of the :doc:`bad analyses file </bad_analyses>`. Defaults to ``bad_analyses.txt``.
* ``lexRulesFile``: name of the :doc:`lexical rules file </lex_rules>`. Defaults to ``lex_rules.txt``.
* ``derivFile``: name of the :doc:`derivations file </derivations>`. Defaults to ``derivations.txt``.
* ``cliticFile``: name of the :doc:`clitics file </clitics>`. Defaults to ``clitics.txt``.
* ``conversionFile``: name of the :doc:`stem conversion file </stem_conversions>`. Defaults to ``stem_conversions.txt``.

The parameters above can be assigned strings with file names or folder names. In the latter case, all ``.txt`` files in the folder are concatenated to form the list of lexemes, paradigms, etc.

The next parameters are used when ``analyze_wordlist()`` is called and can also be passed to it as named arguments:

* ``freqListFile``: name of the frequency list file. Defaults to ``wordlist.csv``.
* ``freqListSeparator``: string used to separate columns (token and frequency) in the frequency list. Defaults to ``\t``.
* ``parsedFile``: name of the output file with analyzed words. Defaults to ``analyzed.txt``.
* ``unparsedFile``: name of the output file with unanalyzed words. Defaults to ``unanalyzed.txt``.

Finally, there are parameters that influence what is done during parsing:

* ``glossing``: Boolean value that determines whether the analyses should contain attributes for glosses and morpheme breaks. Defaults to ``True``.
