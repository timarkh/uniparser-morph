import re

POS_UNSPECIFIED = -1
POS_NONFINAL = 0
POS_FINAL = 1
POS_BOTH = 1

GLOSS_EMPTY = 0
GLOSS_AFX = 1
GLOSS_IFX = 2
GLOSS_REDUPL_R = 3
GLOSS_REDUPL_L = 4
GLOSS_STEM = 5
GLOSS_STEM_FORCED = 6
GLOSS_STEM_SPEC = 7
GLOSS_NEXT_FLEX = 8
GLOSS_STARTWITHSELF = 100


rxStemParts = re.compile('(\\.|[^.]+)')
lexPropertyFields = {'lex', 'stem', 'paradigm', 'gramm', 'gloss',
                      'lexref', 'stem-incorp', 'gramm-incorp',
                      'gloss-incorp'}
wfPropertyFields = {'wf', 'gloss', 'lemma', 'gramm', 'wfGlossed'}


def check_compatibility(sublex, flex, errorHandler=None):
    """
    Check if the given SubLexeme and the given Inflexion
    are compatible.
    """
    if flex.stemNum is not None and len(sublex.numStem & flex.stemNum) <= 0 and\
            sublex.lex.num_stems() > 1:
        return False
    for rxTest in flex.regexTests:
        if not check_for_regex(sublex, rxTest, errorHandler):
            return False
    return True


def check_for_regex(item, rxTest, errorHandler=None, checkWordform=False):
    """
    Perform the given RegexTest against the given item (SubLexeme or Wordform).
    """
    if rxTest.field == 'stem' or rxTest.field == 'prev':
        if not rxTest.perform(item.stem):
            return False
    elif rxTest.field == 'paradigm':
        if errorHandler is not None:
            errorHandler.raise_error('Paradigm names cannot be subject to '
                                     'regex tests.')
        return False
    elif not checkWordform and rxTest.field in lexPropertyFields:
        searchField = rxTest.field
        if searchField == 'lex':
            searchField = 'lemma'
        if not rxTest.perform(item.lex.__dict__[searchField]):
            return False
    elif checkWordform and rxTest.field in wfPropertyFields:
        searchField = rxTest.field
        if searchField == 'lex':
            searchField = 'lemma'
        if not rxTest.perform(item.__dict__[searchField]):
            return False
    else:
        if not checkWordform:
            testResults = [rxTest.perform(d[1])
                           for d in item.lex.otherData
                           if d[0] == rxTest.field]
        else:
            testResults = [rxTest.perform(d[1])
                           for d in item.otherData
                           if d[0] == rxTest.field]
        if len(testResults) <= 0 or not all(testResults):
            return False
    return True


def remove_morph_breaks(stem):
    """
    If the stem contains several morphemes separated by a & sign,
    join them for lookup purposes.
    """
    stem = stem.replace('&', '')
    return stem


def replace_morph_breaks(gloss):
    """
    If the stem or its gloss contains several parts separated by a & sign,
    replace it with a hyphen.
    """
    gloss = gloss.replace('&', '-')
    return gloss


rxCleanL = re.compile('([>~\\-])-+')
rxCleanR = re.compile('-+([<~])$')


def join_stem_flex(stem, stemGloss, flex, bStemStarted=False):
    """
    Join a stem and an inflexion.
    """
    wfGlossed = ''
    gloss = ''
    wf = ''
    pfxPart = ''
    ifxs = ''
    mainPart = ''
    curStemParts = rxStemParts.findall(stem)
    curFlexParts = flex.flexParts[0]
    stemSpecs = ''.join(['.' + fp.gloss for fp in curFlexParts
                         if fp.glossType == GLOSS_STEM_SPEC])
    parts = [curStemParts, curFlexParts]
    pos = [0, 0]    # current position in [stem, flex]
    iSide = 0       # 0 = stem, 1 = flex
    glossType = GLOSS_STEM
    while any(pos[i] < len(parts[i]) for i in [0, 1]):
        if iSide == 0 and pos[iSide] == len(parts[iSide]):
            iSide = 1
        elif iSide == 1 and pos[iSide] == len(parts[iSide]):
            iSide = 0
        if (iSide == 0 and parts[iSide][pos[iSide]] in ['.', '[.]']) or\
           (iSide == 1 and parts[iSide][pos[iSide]].flex in ['.', '[.]']):
            pos[iSide] += 1
            if iSide == 0:
                iSide = 1
            elif iSide == 1:
                if pos[1] == 1 and not pos[0] == 1:
                    continue
                glossType = parts[iSide][pos[iSide] - 1].glossType
                iSide = 0
            continue
        elif iSide == 1 and\
           parts[iSide][pos[iSide]].glossType == GLOSS_STARTWITHSELF:
            pos[iSide] += 1
            continue
        curPart = parts[iSide][pos[iSide]]
        if iSide == 0:
            wf += remove_morph_breaks(curPart)
            bStemStarted = True
            wfGlossed += replace_morph_breaks(curPart)
            if glossType in [GLOSS_STEM, GLOSS_STEM_FORCED]:
                mainPart += stemGloss + stemSpecs
        elif iSide == 1:
            wf += curPart.flex.replace('0', '')
            curFlex = curPart.flex
            if len(curFlex) <= 0 and not curPart.glossType == GLOSS_EMPTY:
                curFlex = '∅'
            if curPart.glossType == GLOSS_AFX:
                if bStemStarted:
                    mainPart += '-' + curPart.gloss + '-'
                else:
                    pfxPart += '-' + curPart.gloss + '-'
                wfGlossed += '-' + curFlex + '-'
            elif curPart.glossType == GLOSS_IFX:
                ifxs += '<' + curPart.gloss + '>'
                wfGlossed += '<' + curFlex + '>'
            elif curPart.glossType == GLOSS_REDUPL_R:
                # if bStemStarted:
                bStemStarted = True
                mainPart += '-' + curPart.gloss + '~'
                # else:
                #     pfxPart += '-' + curPart.gloss + '~'
                wfGlossed += '-' + curPart.flex + '~'
            elif curPart.glossType == GLOSS_REDUPL_L:
                # if bStemStarted:
                bStemStarted = True
                mainPart += '~' + curPart.gloss + '-'
                # else:
                #     pfxPart += '~' + curPart.gloss + '-'
                wfGlossed += '~' + curPart.flex + '-'
            elif curPart.glossType == GLOSS_STEM_SPEC:
                wfGlossed += curPart.flex
            elif curPart.glossType in [GLOSS_STEM,
                                       GLOSS_STEM_FORCED]:
                bStemStarted = True
                wfGlossed += curPart.flex
                mainPart += stemGloss + stemSpecs
            elif curPart.glossType == GLOSS_EMPTY:
                bStemStarted = True
                wfGlossed += curPart.flex
        pos[iSide] += 1
        gloss = pfxPart + ifxs + mainPart
    try:
        gloss = rxCleanL.sub('\\1', gloss).strip('-~')
        gloss = rxCleanR.sub('\\1', gloss).strip('-~')
        wfGlossed = rxCleanL.sub('\\1', wfGlossed).strip('-~')
        wfGlossed = rxCleanR.sub('\\1', wfGlossed).strip('-~')
    except:
        pass
    return wf, wfGlossed, gloss
