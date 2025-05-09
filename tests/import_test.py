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

    # Test replacements in the stem
    a.initialize_parser()
    a.m.MIN_REPLACEMENT_WORD_LEN = 6
    a.m.MIN_REPLACEMENT_STEM_LEN = 5
    analyses = a.analyze_words('лучшее', replacementsAllowed=1)
    print(analyses)
    print(a.m.MIN_REPLACEMENT_WORD_LEN)
    analyses = a.analyze_words('лучше', replacementsAllowed=1)
    print(analyses)
    analyses = a.analyze_words('котькдазгес', replacementsAllowed=1)
    print(analyses)
    analyses = a.analyze_words('коьткудазгес', replacementsAllowed=1)
    print(analyses)
    analyses = a.analyze_words('котькыд', replacementsAllowed=1)
    print(analyses)

    # Test morpheme segmentation in the stem
    analyses = a.analyze_words('котькудазгес')
    print(analyses)
    analyses = a.analyze_words('котькуд')
    print(analyses)
    analyses = a.analyze_words('данъяськиськом')
    print(analyses)

    # Test clitics
    analyses = a.analyze_words('paruhkaonai')
    print(analyses)
    analyses = a.analyze_words('котькудhkao')
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

    # Test simple derivations
    analyses = a.analyze_words('тулы')
    print(analyses)
    analyses = a.analyze_words('ныттулы')
    print(analyses)
    analyses = a.analyze_words('уыныс')
    print(analyses)
    analyses = a.analyze_words('ныууыныс')
    print(analyses)

    # Test recursive derivations
    for w in [
        "yarika",     # bare verb
        "yarikase",   # adverbialized verb
        "tatune",     # bare adverb
        "tatunemï",   # nominalized adverb
        "yarikasemï"  # adverbialized, then nominalized verb
    ]:
        print(a.analyze_words(w))

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
