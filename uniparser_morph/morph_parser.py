import re
import copy
import time
import textdistance
from .common_functions import GLOSS_EMPTY, GLOSS_STEM, GLOSS_STEM_FORCED, GLOSS_STARTWITHSELF, POS_NONFINAL
from .paradigm import Paradigm, Inflexion
from .wordform import Wordform
from .clitic import SIDE_ENCLITIC, SIDE_PROCLITIC, SIDE_OTHER
from .morph_fst import MorphFST


class ParseState:
    def __init__(self, wf, sl, wfCorrStart, stemCorrStart, corrLength,
                 inflLevels=None, curLevel=-1, curStemPos=0, curPos=0,
                 derivsUsed=None, nextInfl=None, paraLink=None):
        self.wf = wf
        self.sl = sl
        self.wfCorrStart = wfCorrStart
        self.stemCorrStart = stemCorrStart
        self.corrLength = corrLength
        self.curStemPos = curStemPos
        self.curPos = curPos
        if inflLevels is None:
            self.inflLevels = []
        else:
            self.inflLevels = [copy.copy(il) for il in inflLevels]
        self.curLevel = curLevel
        if nextInfl is not None:
            self.inflLevels.append({'curInfl': nextInfl, 'paraLink': paraLink,
                                    'curPart': 0, 'curPos': 0})
        if derivsUsed is None:
            self.derivsUsed = []
        else:
            self.derivsUsed = copy.copy(derivsUsed)

    def __repr__(self):
        if self.curLevel == -1:
            offset = '> '
        else:
            offset = '  '
        offset += ' ' * (self.wfCorrStart - len(re.search('^[.<>]*', self.sl.stem).group(0)))
        res = self.wf + '\n'
        res += ' ' * self.curPos + '^\n'
        res += offset + self.sl.stem + '\n'
        res += offset + ' ' * self.curStemPos + '^\n'
        for iLevel in range(len(self.inflLevels)):
            inflLevel = self.inflLevels[iLevel]
            res += '-----------------\n'
            if iLevel == self.curLevel:
                offset = '> '
            else:
                offset = '  '
            res += offset
            for fp in inflLevel['curInfl'].flexParts[0]:
                res += fp.flex + ' '
            res += '\n' + offset
            for i in range(len(inflLevel['curInfl'].flexParts[0])):
                if i >= inflLevel['curPart']:
                    break
                res += ' ' * len(inflLevel['curInfl'].flexParts[0][i].flex) + ' '
            res += ' ' * inflLevel['curPos'] + '^'
            res += '\n'
        return res


class Parser:
    MAX_STEM_START_LEN = 6
    MAX_EMPTY_INFLEXIONS = 2
    MAX_TOKEN_LENGTH = 512          # to avoid stack overflow in FST recursion
    MIN_REPLACEMENT_STEM_LEN = 5    # minimal length of a stem found with at least one replacement
    MIN_REPLACEMENT_WORD_LEN = 6    # minimal length of a word form that can be only accepted with replacements
    REMEMBER_PARSES = False         # useless if parsing a frequency list
    WILDCARD = '•'                  # technical character that is considered equal to any single character

    rxFirstNonEmptyPart = re.compile('^(.*?)([^ .()\\[\\]<>|~]{1,' + str(MAX_STEM_START_LEN) +
                                     '})')
    inflStarts = ('<', '[')
    rxCleanToken = re.compile('^[-=<>\\[\\]/():;.,_!?*]+|[-=<>\\[\\]/():;.,_!?*]+$')
    rxTokenSearch = re.compile('^([^\\w]*)' +
                               '([0-9,.\\-%]+|'
                               '[\\w\\-\'`´‘’‛/@.,]+?)'
                               '([^\\w]*)$')
    rxNoReplacements = None         # words that should not be searched with replacements (language-specific)

    def __init__(self, g, verbose=0, parsingMethod='fst', errorHandler=None):
        self.g = g
        if errorHandler is None:
            errorHandler = self.g.errorHandler
        self.errorHandler = errorHandler
        self.verbose = verbose
        self.parsingMethod = parsingMethod  # 'hash' or 'fst'
        Wordform.verbosity = self.verbose
        self.wfs = {}    # list of wordforms stored in memory
                         # wordform -> [possible Wordform objects]
        self.stemStarters = {}   # letter -> [subLexemes whose firt non-empty
                                 # part starts with that letter]
                                 # (used with 'hash' parsing method)
        self.stemFst = MorphFST(self.g, self.verbose)  # (used with 'fst' parsing method)
        self.incorpFst = MorphFST(self.g, self.verbose)
        self.paradigmFsts = {}   # paradigm_name -> FST for its affixes
                                 # (used with 'fst' parsing method)
        self.dictParses = {}        # token -> [possible Wordform objects]

    def raise_error(self, message, data=None):
        if self.errorHandler is None:
            self.errorHandler = self.g.errorHandler
        self.errorHandler.raise_error(message, data)

    def print_stem_starters(self):
        if self.verbose > 0:
            print('Filling stem starters dictionary complete.')
        if self.verbose > 1:
            for start in self.stemStarters:
                print('\n*** ' + start + ' ***')
                for sl in self.stemStarters[start]:
                    print(sl)
            print('***************\n')

    def add_all_wordforms(self, lexeme):
        """
        Add all the wordforms of a given lexeme to the
        list of pre-generated wordforms.
        """
        for wf in lexeme.generate_wordforms():
            try:
                self.wfs[wf.wf].append(wf)
            except KeyError:
                self.wfs[wf.wf] = [wf]

    def fill_stem_dicts(self):
        """
        Prepare hash table with the stems ('hash' parsing method)
        """
        for l in self.g.lexemes:
            curStemStarters = {}
            for sl in l.subLexemes:
                m = self.rxFirstNonEmptyPart.search(sl.stem)
                if m is None:
                    # if there are no letters in the stem,
                    # generate all possible wordforms
                    self.add_all_wordforms(l)
                    curStemStarters = {}
                    break
                try:
                    curStemStarters[m.group(2)].append(sl)
                except KeyError:
                    curStemStarters[m.group(2)] = [sl]
            for (start, sl) in curStemStarters.items():
                try:
                    self.stemStarters[start] += sl
                except KeyError:
                    self.stemStarters[start] = sl
        self.print_stem_starters()

    def fill_stem_fst(self):
        """
        Prepare FST with the stems ('fst' parsing method)
        """
        for l in self.g.lexemes:
            for sl in l.subLexemes:
                m = self.rxFirstNonEmptyPart.search(sl.stem)
                if m is None:
                    # if there are no letters in the stem,
                    # generate all possible wordforms
                    self.add_all_wordforms(l)
                    break
                self.stemFst.add_stem(sl)

    def fill_incorporated_stem_fst(self):
        """
        Prepare FST with the incorporation versions of the stems.
        """
        for l in self.g.lexemes:
            for sl in l.subLexemes:
                if not sl.noIncorporation:
                    m = self.rxFirstNonEmptyPart.search(sl.stem)
                    if m is not None:
                        self.incorpFst.add_incorp_stem(sl)

    def fill_stems(self):
        """
        Add stems from all the sublexemes in the Grammar to the
        FST or the hash tables, depending on the current parsing
        method.
        This is a necessary preliminary step before the analysis
        begins. Usually it takes up to 10 seconds to complete.
        """
        if self.parsingMethod == 'fst':
            self.fill_stem_fst()
        elif self.parsingMethod == 'hash':
            self.fill_stem_dicts()
        else:
            self.raise_error('Unable to fill stems because the parsing method ' +
                             self.parsingMethod + ' is not supported.')
        self.fill_incorporated_stem_fst()

    def make_paradigm_fst(self, para):
        """
        Return an FST made from all affixes of the paradigm.
        """
        fst = MorphFST(self.g, verbose=self.verbose)
        for infl in para.flex:
            fst.add_affix(infl)
        # fst = fst.determinize()
        return fst

    def fill_affixes(self):
        """
        Add affixes from all paradigms to the FSTs. This step is
        necessary only when parsing method is set to 'fst'.
        """
        for p in self.g.paradigms:
            if self.verbose > 1:
                print('Making an FST for', p, '...')
            para = self.g.paradigms[p]
            self.paradigmFsts[p] = self.make_paradigm_fst(para)
        if self.verbose > 0:
            print('Created FSTs for', len(self.paradigmFsts), 'paradigms.')

    def analysis_conforms(self, wf, template):
        """
        Check if the given analysis conforms to the template provided
        as input. This function is used to check the analyses against
        the list of bad analyses in the Grammar.
        """
        # for badAna in self.g.badAnalyses:
        for k, v in template.items():
            try:
                realValue = wf.__dict__[k]
                if v.search(realValue) is None:
                    return False
                # print(v.pattern, k)
            except KeyError:
                return False
        return True

    def inflexion_may_conform(self, state, infl):
        for fp in infl.flexParts[0]:
            if fp.glossType in [GLOSS_EMPTY,
                                GLOSS_STEM,
                                GLOSS_STEM_FORCED,
                                GLOSS_STARTWITHSELF]:
                continue
            if fp.flex == '<.>':
                continue
            if fp.flex not in state.wf[state.curPos:]:
                return False
            return True
        return True

    def inflexion_is_good(self, state, infl, findDerivations=False):
        """
        Check if the inflexion infl could be part of the word,
        given the current state. If findDerivations is True, search
        only for inflexions starting with GLOSS_STARTWITHSELF.
        """
        if len(infl.flexParts) <= 0 or len(infl.flexParts[0]) <= 0:
            return False
        if findDerivations and infl.flexParts[0][0].glossType != GLOSS_STARTWITHSELF:
            return False
        if self.infl_count(state, infl) >= self.g.RECURS_LIMIT:
            return False
        for fp in infl.flexParts[0]:
            if fp.glossType == GLOSS_EMPTY or len(fp.flex) <= 0:
                continue
            else:
                if fp.flex == '<.>' or fp.glossType in [GLOSS_STEM,
                                                        GLOSS_STEM_FORCED]:
                    if self.inflexion_may_conform(state, infl):
                        return True
                    else:
                        return False
                if state.curPos >= len(state.wf):
                    return False
                # if not fp.flex.startswith(state.wf[state.curPos]):
                if not fp.flex == state.wf[state.curPos:state.curPos + len(fp.flex)]:
                    return False
                return True
        return True

    def empty_depth(self, state):
        """
        Calculate how many empty inflexions are used in the state.
        """
        emptyDepth = 0
        for level in range(len(state.inflLevels)):
            infl = state.inflLevels[level]['curInfl']
            if (len(infl.flexParts) <= 0 or len(infl.flexParts[0]) <= 0 or
                    (len(infl.flexParts[0]) == 1 and len(infl.flexParts[0][0].flex) <= 0)) and\
                     len(infl.subsequent) > 0:
                emptyDepth += 1
        return emptyDepth

    def infl_count(self, state, infl):
        """
        Count how many times given inflexion has been used in the state.
        """
        inflCount = 0
        for level in range(len(state.inflLevels)):
            curInfl = state.inflLevels[level]['curInfl']
            if curInfl == infl:
                inflCount += 1
        return inflCount

    def find_inflexions_fst(self, state, paraName, findDerivations=False, emptyDepth=0):
        try:
            paraFst = self.paradigmFsts[paraName]
        except KeyError:
            self.raise_error('No FST for the paradigm ' + paraName)
            para = self.g.paradigms[paraName]
            return self.find_inflexions_simple(state, para,
                                               findDerivations, emptyDepth)
        # print(state.wf, state.curPos)
        # print(paraFst)
        startChar = objStart = state.curPos
        if state.curPos == state.wfCorrStart:
            startChar = objStart = state.wfCorrStart + state.corrLength
        suitableInfl = paraFst.transduce(state.wf, startChar=startChar,
                                         objStart=objStart)
        result = []
        # print('Looking for:', state.wf, state.curPos, startChar)
        # print('paradigm:', paraName, '\n***\n',
        #       u'\n----\n'.join(f.flex for f in grammar.Grammar.paradigms[paraName].flex))
        # print(paraFst)
        for inflStart, inflEnd, infl, repl in suitableInfl:
            # print(inflStart, inflEnd, infl)
            if findDerivations and len(infl.flexParts) > 0 and\
                            len(infl.flexParts[0]) > 0 and\
                            infl.flexParts[0][0].glossType != GLOSS_STARTWITHSELF:
                continue
            elif self.infl_count(state, infl) >= self.g.RECURS_LIMIT:
                continue
            elif (len(infl.flexParts) <= 0 or len(infl.flexParts[0]) <= 0 or
                  (len(infl.flexParts[0]) == 1 and len(infl.flexParts[0][0].flex) <= 0)) and\
                  len(infl.subsequent) > 0:
                for sp in infl.subsequent:
                    result += self.find_inflexions(state, sp.name,
                                                   emptyDepth=emptyDepth + 1,
                                                   findDerivations=findDerivations)
            else:
                result.append((infl, paraName))
        # print('found:', [str(f[0]) for f in result])
        return result

    def find_inflexions_simple(self, state, para, findDerivations=False, emptyDepth=0):
        result = []
        for infl in para.flex:
            if self.inflexion_is_good(state, infl, findDerivations=findDerivations):
                result.append((infl, para.name))
            if (len(infl.flexParts) <= 0 or len(infl.flexParts[0]) <= 0 or
                (len(infl.flexParts[0]) == 1 and len(infl.flexParts[0][0].flex) <= 0)) and\
                 len(infl.subsequent) > 0:
                for sp in infl.subsequent:
                    result += self.find_inflexions(state, sp.name,
                                                   emptyDepth=emptyDepth + 1,
                                                   findDerivations=findDerivations)
        return result

    def find_inflexions(self, state, paraName, findDerivations=False, emptyDepth=0):
        if emptyDepth <= 0:
            emptyDepth = self.empty_depth(state)
        if emptyDepth > self.MAX_EMPTY_INFLEXIONS:
            return []
        if (len(state.derivsUsed) >= self.g.MAX_DERIVATIONS and
            '#deriv' in paraName):
            return []
        try:
            para = self.g.paradigms[paraName]
        except KeyError:
            self.raise_error('Wrong paradigm name: ' + paraName)
            return []
        if self.parsingMethod == 'hash':
            return self.find_inflexions_simple(state, para, findDerivations, emptyDepth)
        elif self.parsingMethod == 'fst':
            return self.find_inflexions_fst(state, paraName, findDerivations, emptyDepth)
        return []

    def get_wordforms(self, state, replacementsAllowed=0):
        """
        Look at the state after the loop has been finished. Check if
        the combination of stem and affixes found during the loop can
        indeed result into the wordform. Return a list of Wordform objects
        representing all possible analyses.
        """
        # check if some part of the word was not used or no inflexions were used
        if state.curPos < len(state.wf) or len(state.inflLevels) <= 0:
            return None
        # check if not the whole stem was used
        if state.curStemPos < len(state.sl.stem):
            for i in range(state.curStemPos, len(state.sl.stem)):
                if state.sl.stem[i] != '.':
                    return None
        # check if the lowest level contains an inflexion that requires continuation
        lastInfl = state.inflLevels[-1]['curInfl']
        if (lastInfl.position != POS_NONFINAL and
                any(fp.flex == '<.>' for fp in lastInfl.flexParts[0])):
            return None
        # check if inflexions at all levels have been finished
        for inflLevel in state.inflLevels:
            if inflLevel['curPart'] < len(inflLevel['curInfl'].flexParts[0]):
                for iPos in range(inflLevel['curPos'] + 1,
                                  len(inflLevel['curInfl'].flexParts[0][inflLevel['curPart']].flex)):
                    if inflLevel['curInfl'].flexParts[0][inflLevel['curPart']].flex[iPos] not in '.<>[]~|':
                        # print('NONE')
                        return None
                for iPart in range(inflLevel['curPart'] + 1, len(inflLevel['curInfl'].flexParts[0])):
                    if inflLevel['curInfl'].flexParts[0][inflLevel['curPart']].glossType not in\
                        [GLOSS_STEM, GLOSS_STEM_FORCED,
                         GLOSS_STARTWITHSELF] and\
                            len(inflLevel['curInfl'].flexParts[0][inflLevel['curPart']].flex) > 0:
                        # print(inflLevel['curInfl'].flexParts[0][inflLevel['curPart']].flex)
                        return None
        infl = copy.deepcopy(state.inflLevels[0]['curInfl'])
        for iLevel in range(1, len(state.inflLevels)):
            curLevel = state.inflLevels[iLevel]
            Paradigm.join_inflexions(infl, copy.deepcopy(curLevel['curInfl']),
                                     curLevel['paraLink'],
                                     partialCompile=self.g.PARTIAL_COMPILE)

        if infl is None:
            return None
        wf = Wordform(self.g, state.sl, infl)
        if wf is None:
            # print(infl, wf, state.wf)
            return None
        if wf.wf != state.wf:
            if (replacementsAllowed <= 0
                    or wf.wf is None or state.wf is None
                    or len(wf.wf) < self.MIN_REPLACEMENT_WORD_LEN or len(state.wf) < self.MIN_REPLACEMENT_WORD_LEN):
                return None
            elif textdistance.damerau_levenshtein.distance(wf.wf, state.wf) > replacementsAllowed:
                return None
        if self.verbose > 0:
            print(state)
        return [wf]

    def continue_loop(self, state):
        """
        Determine if, given the current state, the investigation loop
        has to be continued.
        """
        if state.curPos < len(state.wf):
            return True
        if len(state.inflLevels) <= 0 and (state.curStemPos >= len(state.sl.stem) or
                                           state.sl.stem[state.curStemPos] == '.'):
            return True
        if len(state.inflLevels) <= 0:
            return False
        curPart = state.inflLevels[-1]['curPart']
        curInflPos = state.inflLevels[-1]['curPos']
        curInfl = state.inflLevels[-1]['curInfl']
        if curPart < len(curInfl.flexParts[0]) and\
           (curInflPos >= len(curInfl.flexParts[0][curPart].flex) or
            ((state.curStemPos < len(state.sl.stem) or state.sl.stem.endswith('.')) and
             curInfl.flexParts[0][curPart].glossType in [GLOSS_STEM,
                                                         GLOSS_STEM_FORCED,
                                                         GLOSS_STARTWITHSELF]) or
            curInfl.flexParts[0][curPart].flex == '<.>'):
            return True
        return False

    def swicth_to_upper_level(self, state):
        """
        Determine if, given the current state, the investigation loop
        should go one level up, switching to the stem or the previous
        inflexion in the stack. Should be called when current part of
        the inflexion is "." or "[.]".
        """
        curPart = state.inflLevels[state.curLevel]['curPart']
        curInfl = state.inflLevels[state.curLevel]['curInfl']
        if curPart >= len(curInfl.flexParts[0]) or\
           curInfl.flexParts[0][curPart].flex not in ['.', '[.]']:
            return False
        if curInfl.flexParts[0][0].glossType == GLOSS_STARTWITHSELF:
            if curPart > 1 or (state.curStemPos < 2 and state.sl.stem.startswith('.')):
                return True
            return False
        if curPart == 0 and state.curLevel > 0 and\
                state.inflLevels[state.curLevel - 1]['curPart'] == 1 and\
                state.inflLevels[state.curLevel - 1]['curInfl'].flexParts[0][1].flex == '<.>':
            return False
        if curPart != 0 or (state.curLevel == 0
                            and state.curStemPos < 2 and state.sl.stem.startswith('.')):
            return True
        return False

    def investigate_state(self, state, replacementsAllowed=0):
        while self.continue_loop(state):
            if self.verbose > 1:
                print(state)
                time.sleep(0.2)
            if state.curLevel == -1:    # level of the stem
                if state.curStemPos >= len(state.sl.stem):
                    if self.verbose > 1:
                        print('Stem ended unexpectedly.')
                    return []
                if state.sl.stem[state.curStemPos] == '.':
                    curLevel = 0
                    state.curStemPos += 1
                    if len(state.inflLevels) > 0:
                        state.curLevel = 0
                        continue
                    else:
                        resultingStates = []
                        for infl, para in self.find_inflexions(state, state.sl.paradigm):
                            # print(infl)
                            newDerivsUsed = []
                            if '#deriv' in para:
                                newDerivsUsed = [para]
                            newState = ParseState(state.wf, state.sl, state.wfCorrStart,
                                                  state.stemCorrStart, state.corrLength,
                                                  state.inflLevels, curLevel, state.curStemPos,
                                                  state.curPos, state.derivsUsed + newDerivsUsed,
                                                  infl)
                            resultingStates += self.investigate_state(newState, replacementsAllowed=replacementsAllowed)
                        return resultingStates
                elif state.curStemPos == 0 and len(state.inflLevels) <= 0:
                    # find derivational inflexions
                    resultingStates = []
                    if self.verbose > 1:
                        print('Looking for derivational inflexions...')
                    for infl, para in self.find_inflexions(state, state.sl.paradigm, findDerivations=True):
                        newDerivsUsed = []
                        if '#deriv' in para:
                            newDerivsUsed = [para]
                        newState = ParseState(state.wf, state.sl, state.wfCorrStart,
                                              state.stemCorrStart, state.corrLength,
                                              state.inflLevels, 0, state.curStemPos,
                                              state.curPos, state.derivsUsed + newDerivsUsed,
                                              infl)
                        resultingStates += self.investigate_state(newState, replacementsAllowed=replacementsAllowed)
                    if len(resultingStates) > 0:
                        if self.verbose > 1:
                            print(len(resultingStates), 'derivational inflexions found.')
                        if state.wf[state.curPos] == state.sl.stem[state.curStemPos]:
                            newState = ParseState(state.wf, state.sl, state.wfCorrStart,
                                                  state.stemCorrStart, state.corrLength,
                                                  state.inflLevels, -1, state.curStemPos,
                                                  state.curPos, state.derivsUsed)
                            newState.curPos += 1
                            newState.curStemPos += 1
                            resultingStates += self.investigate_state(newState, replacementsAllowed=replacementsAllowed)
                        return resultingStates
                if state.stemCorrStart <= state.curStemPos <\
                                state.stemCorrStart + state.corrLength:
                    if state.curPos != state.wfCorrStart + state.curStemPos -\
                            state.stemCorrStart:
                        return []
                elif state.curPos >= len(state.wf) or\
                     state.curStemPos >= len(state.sl.stem):
                    self.raise_error('Stem or wordform ended unexpectedly: stem=' +
                                     state.sl.stem + ', wf=' + state.wf + '.')
                    return []
                elif (state.wf[state.curPos] != state.sl.stem[state.curStemPos]
                      and (state.wf[state.curPos] != self.WILDCARD and state.sl.stem[state.curStemPos] != self.WILDCARD)):
                    return []
                state.curPos += 1
                state.curStemPos += 1
            else:
                curPart = state.inflLevels[state.curLevel]['curPart']
                curPos = state.inflLevels[state.curLevel]['curPos']
                curInfl = state.inflLevels[state.curLevel]['curInfl']
                if curPart >= len(curInfl.flexParts[0]):
                    state.curLevel -= 1
                    continue
                fp = curInfl.flexParts[0][curPart]
                # print(fp.flex, curPart, curPos)
                # if curPos > 0 and curPos >= len(fp.flex):
                if fp.flex == '.' or fp.flex == '[.]':
                    bSwicthToUpperLevel = self.swicth_to_upper_level(state)
                    if not (state.curStemPos < 2 and state.sl.stem.startswith('.') and
                            curPart == 0 and state.curPos <= -2):
                        state.inflLevels[state.curLevel]['curPart'] += 1
                        state.inflLevels[state.curLevel]['curPos'] = 0
                    if bSwicthToUpperLevel:
                        state.curLevel -= 1
                    continue
                elif fp.flex == '<.>':
                    curLevel = state.curLevel + 1
                    state.inflLevels[state.curLevel]['curPart'] += 1
                    state.inflLevels[state.curLevel]['curPos'] = 0
                    if len(state.inflLevels) > curLevel:
                        state.curLevel = curLevel
                        continue
                    else:
                        resultingStates = []
                        for pl in curInfl.subsequent:
                            # print(pl.name)
                            for infl, para in self.find_inflexions(state, pl.name):
                                newDerivsUsed = []
                                if '#deriv' in para:
                                    newDerivsUsed = [para]
                                newState = ParseState(state.wf, state.sl, state.wfCorrStart,
                                                      state.stemCorrStart, state.corrLength,
                                                      state.inflLevels, curLevel, state.curStemPos,
                                                      state.curPos, state.derivsUsed + newDerivsUsed, infl, pl)
                                resultingStates += self.investigate_state(newState, replacementsAllowed=replacementsAllowed)
                        return resultingStates
                elif curPos >= len(fp.flex):   # or fp.glossType == paradigm.GLOSS_EMPTY:
                    state.inflLevels[state.curLevel]['curPart'] += 1
                    state.inflLevels[state.curLevel]['curPos'] = 0
                    continue
                else:
                    if (curPos >= len(fp.flex)
                            or state.curPos >= len(state.wf)
                            or (fp.flex[curPos] != state.wf[state.curPos]
                                and fp.flex[curPos] != self.WILDCARD and state.wf[state.curPos] != self.WILDCARD)):
                        return []
                    state.curPos += 1
                    state.inflLevels[state.curLevel]['curPos'] += 1
                    continue
        if self.verbose > 1:
            print('End of loop:')
            print(state)
            print('Trying to get a wordform...')
            print('Inflexions:\n' + '---\n'.join(str(l['curInfl']) for l in state.inflLevels))
        wf = self.get_wordforms(state, replacementsAllowed=replacementsAllowed)
        if wf is None:
            return []
        return wf

    def get_hosts(self, word, cliticSide=None, includeSrcWord=True):
        """
        Find all possible ways of splitting the word into a host and clitic(s).
        Return a list of tuples (Clitic object of None, remaining part of
        the string). If cliticSide is not None, search only for the clitics
        specified by that argument (proclitics or enclitics).
        If there are multiple clitics, list firsth the proclitics and then the
        enclitics.
        """
        if includeSrcWord:
            hostsAndClitics = [(None, word)]
        else:
            hostsAndClitics = []
        for cl in self.g.clitics:
            if (cl.side == SIDE_ENCLITIC and
                    cliticSide != SIDE_PROCLITIC and
                    word.endswith(cl.stem) and
                    len(word) > len(cl.stem)):
                host = word[:-len(cl.stem)]
                if not cl.is_compatible_str(host):
                    continue
                curHost = host
                curCl = cl
                if len(host) > 1:
                    # Try chopping further clitics
                    furtherHostsAndClitics = self.get_hosts(host,
                                                            cliticSide=SIDE_ENCLITIC,
                                                            includeSrcWord=False)
                    if len(furtherHostsAndClitics) > 0:
                        for furtherCl, furtherHost in furtherHostsAndClitics:
                            hostsAndClitics.append((furtherCl + [curCl], furtherHost))
                    else:
                        hostsAndClitics.append(([curCl], curHost))
                else:
                    hostsAndClitics.append(([curCl], curHost))
            if (cl.side == SIDE_PROCLITIC and
                    cliticSide != SIDE_ENCLITIC and
                    word.startswith(cl.stem) and
                    len(word) > len(cl.stem)):
                host = word[len(cl.stem):]
                if not cl.is_compatible_str(host):
                    continue
                curHost = host
                curCl = cl
                if len(host) > 1:
                    # Try chopping further clitics
                    furtherHostsAndClitics = self.get_hosts(host, cliticSide=cliticSide, includeSrcWord=False)
                    if len(furtherHostsAndClitics) > 0:
                        for furtherCl, furtherHost in furtherHostsAndClitics:
                            hostsAndClitics.append(([curCl] + furtherCl, furtherHost))
                    else:
                        hostsAndClitics.append(([curCl], curHost))
                else:
                    hostsAndClitics.append(([curCl], curHost))
        return hostsAndClitics

    def find_stems(self, word, replacementsAllowed=0):
        """
        Find all possible stems in the given token.
        Return a list of corresponding state instances.
        """
        states = []
        if self.parsingMethod == 'hash':
            for l in range(len(word)):
                for r in range(l + 1, min(len(word) + 1, l + self.MAX_STEM_START_LEN + 1)):
                    possibleStem = word[l:r]
                    try:
                        suitableSubLex = self.stemStarters[possibleStem]
                    except KeyError:
                        continue
                    if self.verbose > 0:
                        print('Trying to analyze:', l, r, possibleStem)
                    for sl in suitableSubLex:
                        if self.verbose > 1:
                            print(sl)
                        state = ParseState(word, sl, l, sl.stem.find(possibleStem), r - l)
                        states.append(state)
        elif self.parsingMethod == 'fst':
            suitableSubLex = self.stemFst.transduce(word, replacementsAllowed=replacementsAllowed)
            for l, r, sl, repl in suitableSubLex:
                # print(word, sl.stem, replacementsAllowed, l, r)
                # print(replacementsAllowed, r - l + 1, self.MIN_REPLACEMENT_STEM_LEN, sl.stem)
                if self.verbose > 1:
                    print('FST: found a stem, parameters:',
                          l, sl.stem, word[l:r+1], sl.stem.find(word[l:r+1]), r - l + 1, repl)
                wordReplaced = word
                addLen = 0
                for action, i in repl:
                    if i < 0 or i >= len(wordReplaced):
                        continue
                    if action == 'swap' and i < len(wordReplaced) - 1:
                        wordReplaced = wordReplaced[:i] + wordReplaced[i + 1] + wordReplaced[i] + wordReplaced[i + 2:]
                    elif action == 'del':
                        wordReplaced = wordReplaced[:i] + wordReplaced[i+1:]
                        addLen -= 1
                    elif action == 'ins':
                        wordReplaced = wordReplaced[:i] + self.WILDCARD + wordReplaced[i:]
                        addLen += 1
                    elif action == 'sub':
                        wordReplaced = wordReplaced[:i] + self.WILDCARD + wordReplaced[i+1:]
                # print(wordReplaced, sl.stem.find(wordReplaced[l:r+1]))
                if replacementsAllowed > 0 and r - l + 1 + addLen < self.MIN_REPLACEMENT_STEM_LEN:
                    continue
                if replacementsAllowed <= 0 or wordReplaced == word:
                    state = ParseState(wordReplaced, sl, l, sl.stem.find(wordReplaced[l:r+1]), r - l + 1)
                else:
                    matchPosition = -1
                    substringReplaced = re.escape(wordReplaced[l:r + 1 + addLen]).replace(self.WILDCARD, '.')
                    m = re.search(substringReplaced, sl.stem)
                    if m is not None:
                        matchPosition = m.start(0)
                    state = ParseState(wordReplaced, sl, l, matchPosition, r - l + 1 + addLen)
                    # print('FST: found a stem, parameters:',
                    #       l, sl.stem, wordReplaced[l:r + 1 + addLen], matchPosition, r - l + 1 + addLen, word, repl, wordReplaced)
                states.append(state)
        return states

    def is_bad_analysis(self, analyses, i_ana):
        """
        Check if the analysis with the index i_ana in the list of
        analyses is conditionally or unconditionally bad, based on
        the checks in bad_analyses.txt.
        """
        # First, check the unconditional templates
        for badAna in self.g.badAnalyses:
            if self.analysis_conforms(analyses[i_ana], badAna):
                return True

        # Then, check the unconditional templates
        for badAna in self.g.badAnalysesConditional:
            badAnaRemove = badAna['remove']
            badAnaIfExists = badAna['if_exists']
            if (self.analysis_conforms(analyses[i_ana], badAnaRemove)
                    and any(i != i_ana and self.analysis_conforms(analyses[i], badAnaIfExists)
                            for i in range(len(analyses)))):
                return True
        return False

    def investigate_states(self, states, replacementsAllowed=0):
        """
        Investigate all states corresponding to the stems found by the stem FST.
        Return a set of all possible analyses.
        """
        analyses = []
        if self.verbose > 0:
            print('Start investigating states...')
        for state in states:
            analyses += self.investigate_state(state, replacementsAllowed=replacementsAllowed)
        analysesSet = set()
        for i in range(len(analyses)):
            ana = analyses[i]
            if self.is_bad_analysis(analyses, i):
                continue
            enhancedAnas = self.apply_lex_rules(ana)
            if len(enhancedAnas) <= 0:
                analysesSet.add(ana)
            else:
                analysesSet |= enhancedAnas
        for ana in analysesSet:
            ana.expand_lex_morphs()
        return analysesSet

    def parse_host(self, word, replacementsAllowed=0):
        """
        Return a list of Wordform objects, each representing a possible
        analysis of the word string, assuming it has no clitics.
        """
        # t1 = time.time()
        analyses = []
        if self.verbose > 0:
            print(word, ': start searching for sublexemes...')

        # First, try finding stems in a straightforward, deterministic way
        states = self.find_stems(word, replacementsAllowed=0)
        analysesSet = self.investigate_states(states, replacementsAllowed=0)

        if len(analysesSet) <= 0 and replacementsAllowed > 0 and len(word) >= self.MIN_REPLACEMENT_WORD_LEN:
            # If this failed, try finding stems with some replacements allowed
            if self.rxNoReplacements is None or self.rxNoReplacements.search(word) is None:
                states = self.find_stems(word, replacementsAllowed=replacementsAllowed)
                analysesSet = self.investigate_states(states, replacementsAllowed=replacementsAllowed)

        # t2 = time.time()
        # print(t2 - t1, 'seconds for analyzing.')
        return analysesSet

    def apply_lex_rules(self, ana):
        possibleEnhancements = set()
        if ana.lemma in self.g.lexRulesByLemma:
            for rule in self.g.lexRulesByLemma[ana.lemma]:
                newAna = rule.apply(ana)
                if newAna is not None:
                    possibleEnhancements.add(newAna)
        if ana.stem in self.g.lexRulesByStem:
            for rule in self.g.lexRulesByStem[ana.stem]:
                newAna = rule.apply(ana)
                if newAna is not None:
                    possibleEnhancements.add(newAna)
        return possibleEnhancements

    def parse(self, word, printOut=False, replacementsAllowed=0):
        """
        Return a list of Wordform objects, each representing a possible
        analysis of the word string.
        """
        analyses = []
        word = Parser.rxCleanToken.sub('', word)
        if self.REMEMBER_PARSES:
            try:
                analyses = self.dictParses[word]
                if self.verbose > 0:
                    print(word, 'was found in the cache.')
                return analyses
            except KeyError:
                pass
        if len(word) <= 0 or len(word) > Parser.MAX_TOKEN_LENGTH:
            return analyses

        if self.verbose > 0:
            print(word, ': start searching for clitics...')
        hostsAndClitics = self.get_hosts(word)
        if self.verbose > 1:
            print(len(hostsAndClitics), 'possible variants of splitting into a host and a clitic.')
        for clitics, host in hostsAndClitics:
            hostAnalyses = self.parse_host(host, replacementsAllowed=replacementsAllowed)
            if len(hostAnalyses) <= 0:
                continue
            for wf in hostAnalyses:
                if clitics is not None:
                    wf.wf = word
                    for cl in clitics:
                        if cl.is_compatible(wf):
                            # Lemma
                            wf.add_lemma(cl, Inflexion(self.g, {}))
                            # Grammatical tags, if present
                            wf.add_gramm(None, cl)
                            # Additional fields
                            wf.add_other_data(None, cl)
                            # Gloss
                            if cl.side == SIDE_PROCLITIC:
                                wf.gloss = cl.gloss + '=' + wf.gloss
                                wf.wfGlossed = cl.stemParts + '=' + wf.wfGlossed
                            else:
                                wf.gloss += '=' + cl.gloss
                                wf.wfGlossed += '=' + cl.stemParts
                analyses.append(wf)
        if printOut:
            if len(analyses) <= 0:
                print(word + ': no possible analyses found.')
            else:
                print(word + ':', len(analyses), 'analyses:\n')
                for ana in analyses:
                    print('****************\n')
                    print(ana)
        if self.REMEMBER_PARSES:
            self.dictParses[word] = analyses
        return analyses

    @staticmethod
    def ana2xml(token, analyses, glossing=False):
        r = '<w>'
        for ana in sorted(set(ana.to_xml(glossing=glossing) for ana in analyses)):
            r += ana
        return r + token + '</w>'

    def parse_freq_list(self, fnameIn, sep=':', fnameParsed='', fnameUnparsed='',
                        maxLines=None, glossing=False, replacementsAllowed=0):
        """
        Analyze a frequency list of tokens. Write analyses to fnameParsed
        and unanalyzed tokens to fnameUnparsed. Return total number of tokens
        and the rate of the parsed tokens (taking their frequencies into account).
        If maxLines is not None, process only the first maxLines of the
        frequency list.
        """
        if len(fnameParsed) <= 0:
            fnameParsed = fnameIn + '-parsed.txt'
        if len(fnameUnparsed) <= 0:
            fnameUnparsed = fnameIn + '-unparsed.txt'
        try:
            fIn = open(fnameIn, 'r', encoding='utf-8-sig')
            lines = [(x[0].strip(), int(x[1].strip()))
                     for x in [line.split(sep) for line in fIn if len(line) > 2]]
            fIn.close()
        except IOError:
            self.raise_error('The frequency list could not be opened.')
            return 0, 0.0
        except ValueError:
            self.raise_error('Wrong format of the frequency list.')
            return 0, 0.0
        if maxLines is not None:
            lines = lines[:maxLines]
        parsedTokenFreqs = 0
        unparsedTokenFreqs = 0
        fParsed = open(fnameParsed, 'w', encoding='utf-8')
        fUnparsed = open(fnameUnparsed, 'w', encoding='utf-8')
        for (token, freq) in sorted(lines, key=lambda x: (-x[1], x[0])):
            analyses = self.parse(token, replacementsAllowed=replacementsAllowed)
            if len(analyses) <= 0:
                fUnparsed.write(token + '\n')
                unparsedTokenFreqs += freq
            else:
                fParsed.write(Parser.ana2xml(token, analyses, glossing=glossing) + '\n')
                parsedTokenFreqs += freq
        fParsed.close()
        fUnparsed.close()
        return len(lines), parsedTokenFreqs / (parsedTokenFreqs + unparsedTokenFreqs)

    def parse_txt(self, fnameIn, fnameOut='', encoding='utf-8-sig',
                  glossing=False, replacementsAllowed=0):
        """
        Analyze a text file fnameIn. Write the processed text to fnameOut.
        Return total number of tokens and number of the parsed tokens.
        """
        self.REMEMBER_PARSES = True
        if len(fnameOut) <= 0:
            fnameOut = fnameIn + '-processed.xml'
        try:
            fIn = open(fnameIn, 'r', encoding=encoding)
            text = fIn.read()
            processedText = '<text>\n'
            fIn.close()
        except IOError:
            self.raise_error('The text file ' + fnameIn + ' could not be opened.')
            return 0, 0
        rawTokens = text.split()
        wordsAnalyzed = totalWords = 0
        for token in rawTokens:
            if len(token) <= 0:
                continue
            m = self.rxTokenSearch.search(token)
            processedText += ' '
            if m is None:
                processedText += token
                continue
            puncl = m.group(1)
            wf = m.group(2)
            puncr = m.group(3)
            processedText += puncl
            if len(wf) > 0:
                anas = self.parse(wf.lower(), replacementsAllowed=replacementsAllowed)
                if len(anas) > 0:
                    wordsAnalyzed += 1
                processedText += Parser.ana2xml(wf, anas, glossing=glossing)
                totalWords += 1
            processedText += puncr + '\n'
        processedText += '</text>'
        fOut = open(fnameOut, 'w', encoding='utf-8')
        fOut.write(processedText)
        fOut.close()
        return totalWords, wordsAnalyzed
