import os
import sys
import inspect

curDir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentDir = os.path.dirname(curDir)
sys.path.insert(0, parentDir)

from uniparser_morph import Analyzer


if __name__ == '__main__':
    a = Analyzer()
    a.load_grammar()

    # Test morpheme segmentation in the stem
    analyses = a.analyze_words('котькудазгес')
    print(analyses)
    analyses = a.analyze_words('котькуд')
    print(analyses)

    # Test standard (underlying) morphemes
    analyses = a.analyze_words('бырйыны')
    print(analyses)
    analyses = a.analyze_words('быръемлэсь')
    print(analyses)

    # Test LEX:xxx:yyy
    analyses = a.analyze_words('юртъёсаз')
    print(analyses)
    analyses = a.analyze_words('юртъёсаз', format='xml')
    print(analyses)
    analyses = a.analyze_words('юртъёсаз', format='json')
    print(analyses)
    analyses = a.analyze_words('юртъёсаз', format='conll')
    print(analyses)
    a.g.COMPLEX_WF_AS_BAGS = True
    analyses = a.analyze_words('юртъёсаз', format='xml')
    print(analyses)
    analyses = a.analyze_words('юртъёсаз', format='json')
    print(analyses)
    analyses = a.analyze_words('юртъёсаз', format='conll')
    print(analyses)

    # Test sentences and complex structures
    analyses = a.analyze_words(['Морфологиез', [['А'], ['Мон', 'тонэ', 'яратӥсько', '.']]], format='xml')
    print(analyses)
    analyses = a.analyze_words(['Морфологиез', [['А'], ['Мон', 'морфологиез', 'яратӥсько', '.']]], format='json')
    print(analyses)
    analyses = a.analyze_words(['Морфологиез', [['А'], ['Мон', 'морфологиез', 'яратӥсько', '.']]], format='conll')
    print(analyses)
    analyses = a.analyze_words(['юртъёсын', [], [['А'], ['Мон', 'морфологиез', 'яратӥсько', '.']]],
                               cgFile=os.path.abspath('udmurt_disambiguation.cg3'), disambiguate=True)
    print(analyses)
