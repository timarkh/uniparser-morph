Short usage guide
=================

If you already have prepared the grammar rules in the right format, you have to put them in the same folder where you run your script. (If not, see :doc:`the format description </format>`.)

Import the ``Analyzer`` class from the package, make an instance and load your grammar files::

	from uniparser_morph import Analyzer
	a = Analyzer()
	a.load_grammar()

Now you can use one of several functions to analyze text in your language. Beware that the analyzer performs actual initialization when first asked to analyze something, so expect some delay after the first function call you make. Usually it takes several seconds to initialize things, but that depends on the language.

If you want to analyze words or sentences on the fly, call ``analyze_words()``::

	analyses = a.analyze_words('Морфологияез')
	# If you pass a single string, you will get a list of Wordform objects

	# You can also pass lists (even nested lists) and specify output format ('xml' or 'json')
	# If you pass a list, you will get a list of analyses with the same structure

	analyses = a.analyze_words([['А'], ['Мон', 'тонэ', 'яратӥсько', '.']],
	                           format='xml')
	# format='xml' means you will get an XML string like <w><ana lex="..." gr="..." ...></ana>...</w>
	# for each token instead of a list of Wordform objects

	analyses = a.analyze_words(['Морфологияез', [['А'], ['Мон', 'тонэ', 'яратӥсько', '.']]],
	                           format='json')
	# format='json' means you will get a list of dictionaries such as {'lemma': ..., 'gr': ..., ...}
	# for each token instead of a list of Wordform objects

You can change the default settings by assigning non-default values to the properties of your ``Analyzer`` object.
