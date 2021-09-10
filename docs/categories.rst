categories.json
===============

``categories.json`` is an optional file. It can be used to classify grammatical tags into category. Category labels are strings, just as tags. For example, ``N`` and ``V`` could belong to a category called ``pos``, ``nom`` and ``acc`` to ``case``, and ``sg`` and ``pl``, to ``number``. You will only need that file if you want CoNLL-like output (:doc:`format='conll' </usage>` when calling analysis functions).

``categories.json`` is a dictionary. Its keys are tags and values are their categories. Here is an example:

.. code-block:: javascript
  :linenos:
    
    {
        "A": "pos",
        "S": "pos",
        "V": "pos",
        "acc": "case",
        "gen": "case",
        "nom": "case"
    }

If you have ``categories.json`` and use ``conll`` formatting, this is what you get:

* The POS column is filled with the tag(s) that are categorized as ``pos`` in the file.
* All the rest goes to the next column as key-value pairs joined by ``|``. So instead of ``nom,sg`` you will get something like ``Case=nom|Number=sg``, provided both ``nom`` and ``sg`` are in the file.
