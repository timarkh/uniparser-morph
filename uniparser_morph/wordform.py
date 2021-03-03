import copy
from .common_functions import wfPropertyFields, check_compatibility, join_stem_flex


class Wordform:
    propertyFields = wfPropertyFields
    printableOtherFields = {'trans_ru', 'trans_en', 'trans_de', 'lex2', 'gramm2',
                            'trans_ru2', 'trans_en2', 'trans_de2', 'root'}
    verbosity = 0
    
    def __init__(self, g, sublex=None, flex=None, wf=None, errorHandler=None):
        self.g = g
        if errorHandler is None:
            self.errorHandler = self.g.errorHandler
        else:
            self.errorHandler = errorHandler
        self.wf = wf
        self.wfGlossed = ''
        self.gloss = ''
        self.lemma = ''
        self.gramm = ''
        self.stem = ''
        self.otherData = []     # list of tuples (name, value)
        if sublex is None or flex is None:
            return
        if flex.stemNum is not None and len(flex.stemNum) > 0 and 1 < sublex.lex.num_stems() <= max(flex.stemNum):
            self.raise_error('Incorrect stem number: lexeme ' +
                             sublex.lex.lemma + ', inflexion ' +
                             flex.flex)
            return
        # elif flex.stemNum is None and sublex.lex.num_stems() > 1:
        #     self.raise_error('Unspecified stem number: lexeme ' +
        #                      sublex.lex.lemma + ', inflexion ' +
        #                      flex.flex)
        #     return

        elif len(flex.flexParts) > 1:
            self.raise_error('The inflexion ' + flex.flex +
                             ' is not fully compiled.')
            return
        elif not check_compatibility(sublex, flex):
            return
        self.add_gramm(sublex, flex)
        self.build_value(sublex, flex)
        self.add_lemma(sublex.lex, flex)
        self.add_other_data(sublex.lex, flex)
        self.otherData = copy.deepcopy(sublex.lex.otherData)

    def raise_error(self, message, data=None):
        if self.errorHandler is not None:
            self.errorHandler.raise_error(message, data)

    def add_lemma(self, lex, flex):
        if flex.lemmaChanger is None:
            self.lemma = lex.lemma
            return
        suitableSubLex = [sl for sl in lex.subLexemes
                          if flex.lemmaChanger.stemNum is None or
                             len(sl.numStem & flex.lemmaChanger.stemNum) > 0]
        if len(suitableSubLex) <= 0:
            if lex.num_stems() == 1:
                suitableSubLex = lex.subLexemes
        if len(suitableSubLex) <= 0:
            self.raise_error('No stems available to create the new lemma ' +
                             flex.lemmaChanger.flex)
            self.lemma = ''
            return
        if len(suitableSubLex) > 1:
            if self.verbosity > 0:
                self.raise_error('Several stems available to create the new lemma ' +
                                 flex.lemmaChanger.flex)
        wfLemma = Wordform(suitableSubLex[0], flex.lemmaChanger,
                           self.errorHandler)
        self.lemma = wfLemma.wf

    def add_gramm(self, sublex, flex):
        self.stem = sublex.stem
        if not flex.replaceGrammar:
            self.gramm = sublex.gramm
            if len(sublex.gramm) > 0 and len(flex.gramm) > 0:
                self.gramm += ','
            self.gramm += flex.gramm
        else:
            self.gramm = flex.gramm
    
    def add_other_data(self, lex, flex):
        if flex.keepOtherData:
            self.otherData = copy.deepcopy(lex.otherData)

    def get_lemma(self, lex, flex):
        # TODO: lemma changers
        self.lemma = lex.lemma

    def build_value(self, sublex, flex):
        subLexStem = sublex.stem
        if flex.startWithSelf and not subLexStem.startswith('.'):
            subLexStem = '.' + subLexStem
        self.wf, self.wfGlossed, self.gloss = join_stem_flex(subLexStem,
                                                             sublex.gloss,
                                                             flex)

    def to_xml(self, glossing=True):
        """
        Return an XML representation of the analysis in the format of
        Russian National Corpus.
        If glossing is True, include the glossing information.
        """
        r = '<ana lex="' + self.lemma + '" gr="' + self.gramm + '"'
        if glossing:
            r += ' parts="' + self.wfGlossed + '" gloss="' + self.gloss + '"'
        for field, value in self.otherData:
            if field in Wordform.printableOtherFields:
                r += ' ' + field + '="' + value.replace('"', "'") + '"'
        return r + '></ana>'

    def to_json(self, glossing=True):
        """
        Return a JSON representation of the analysis.
        If glossing is True, include the glossing information.
        """
        r = {
            'wf': self.wf,
            'lemma': self.lemma,
            'gramm': [tag for tag in self.gramm.split(',') if len(tag) > 0]
        }
        if glossing:
            r['wfGlossed'] = self.wfGlossed
            r['gloss'] = self.gloss
        for field, value in self.otherData:
            if field in Wordform.printableOtherFields:
                r[field] = value
        return r

    def __repr__(self):
        r = '<Wordform object>\n'
        if self.wf is not None:
            r += self.wf + '\n'
        if self.lemma is None:
            self.lemma = ''
        if self.gramm is None:
            self.gramm = ''
        r += self.lemma + '; ' + self.gramm + '\n'
        r += self.wfGlossed + '\n'
        r += self.gloss + '\n'
        for field, value in self.otherData:
            r += field + '\t' + value + '\n'
        return r

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if self.wf != other.wf or self.lemma != other.lemma:
            return False
        return str(self) == str(other)

    def __ne__(self, other):
        return not self.__eq__(other)
