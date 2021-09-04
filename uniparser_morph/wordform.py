import copy
import re
from .common_functions import wfPropertyFields, check_compatibility, join_stem_flex


class Wordform:
    rxLexTag = re.compile(',?\\bLEX:([^,:]*):([^,:]*)')
    rxLexTagOtherField = re.compile('^([^=]+)=(.*)')
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

    def add_to_field(self, field, value):
        """
        Concatenate or append the string value to the specified
        field, depending on self.g.COMPLEX_WF_AS_BAGS parameter value.
        """
        print(field, value)
        if field in ('wf', 'wfGlossed', 'parts', 'gloss'):
            return
        elif field == 'lemma':
            # Lemma
            if self.g.COMPLEX_WF_AS_BAGS:
                self.lemma += '+' + value
            else:
                if type(self.lemma) != list:
                    self.lemma = [self.lemma]
                self.lemma.append(value)
        elif field == 'gramm':
            # Grammatical tags
            if self.g.COMPLEX_WF_AS_BAGS:
                if len(self.gramm) > 0 and len(value) > 0:
                    self.gramm += ','
                self.gramm += value
            else:
                if type(self.gramm) != list:
                    self.gramm = [self.gramm]
                self.gramm.append(value)
        else:
            # Additional fields
            bAdded = False
            for iField in self.otherData:
                curField, curValue = self.otherData[iField]
                if curField == field:
                    if self.g.COMPLEX_WF_AS_BAGS:
                        if len(curValue) > 0 and len(value) > 0:
                            curValue += ' + '
                        curValue += value
                    else:
                        if type(curValue) != list:
                            curValue = [curValue]
                        curValue.append(value)
                    self.otherData[iField] = (curField, curValue)
                    bAdded = True
            if not bAdded:
                if not self.g.COMPLEX_WF_AS_BAGS:
                    value = ['', value]
                self.otherData.append((field, value))

    def expand_lex_morphs(self):
        """
        Find tags that look like LEX:xxx:yyy and expand them. They
        come from inflexions which actually contain items that require
        separate lemmata, POS tags and, possibly, other fields, such as
        intraclitics. Depending on self.g.COMPLEX_WF_AS_BAGS parameter value,
        either concatenate lemma, gramm etc. fields with the data taken
        from LEX:xxx:yyy as strings, or append them as list elements.
        """
        lexemes2add = []
        lexTags = self.rxLexTag.findall(self.gramm)
        if len(lexTags) <= 0:
            return
        self.gramm = self.rxLexTag.sub('', self.gramm)
        for lemma, gramm in lexTags:
            gramm = gramm.replace(';', ',')
            lex2add = {'lemma': lemma, 'gramm': ''}
            for tag in gramm.split(','):
                m = self.rxLexTagOtherField.search(tag)
                if m is not None:
                    if m.group(1) not in ('wf', 'lemma', 'gramm', 'stem', 'gloss', 'parts', 'wfGlossed'):
                        lex2add[m.group(1)] = m.group(2)
                else:
                    if len(lex2add['gramm']) > 0:
                        lex2add['gramm'] += ','
                    lex2add['gramm'] += tag
            lexemes2add.append(lex2add)
        for lex2add in lexemes2add:
            for field, value in lex2add.items():
                self.add_to_field(field, value)

    def get_lemma(self, lex, flex):
        # TODO: lemma changers
        self.lemma = lex.lemma

    def build_value(self, sublex, flex):
        subLexStem = sublex.stemParts
        if flex.startWithSelf and not subLexStem.startswith('.'):
            subLexStem = '.' + subLexStem
        self.wf, self.wfGlossed, self.gloss = join_stem_flex(subLexStem,
                                                             sublex.gloss,
                                                             flex)

    def to_xml(self, glossing=True, sort_tags=False):
        """
        Return an XML representation of the analysis in the format of
        Russian National Corpus.
        If glossing is True, include the glossing information.
        """
        if self.lemma is None:
            self.lemma = ''
        if self.gramm is None:
            self.gramm = ''
        gramm = self.gramm.strip()
        if sort_tags:
            gramm = ','.join(tag for tag in sorted(self.gramm.split(','))
                             if len(tag) > 0)
        r = '<ana lex="' + self.lemma + '" gr="' + gramm + '"'
        if glossing:
            r += ' parts="' + self.wfGlossed + '" gloss="' + self.gloss + '"'
        for field, value in self.otherData:
            if field in Wordform.printableOtherFields:
                r += ' ' + field + '="' + value.replace('"', "'") + '"'
        return r + '></ana>'

    def to_json(self, glossing=True, sort_tags=False):
        """
        Return a JSON representation of the analysis.
        If glossing is True, include the glossing information.
        """
        if self.lemma is None:
            self.lemma = ''
        if self.gramm is None:
            self.gramm = ''
        r = {
            'wf': self.wf,
            'lemma': self.lemma
        }
        if sort_tags:
            r['gramm'] = [tag for tag in sorted(self.gramm.split(','))
                          if len(tag) > 0]
        else:
            r['gramm'] = [tag for tag in self.gramm.split(',')
                          if len(tag) > 0]
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
        r += str(self.lemma) + '; '
        if type(self.gramm) == str:
            r += ','.join(tag for tag in sorted(self.gramm.split(','))
                          if len(tag) > 0)\
                 + '\n'
        elif type(self.gramm) == list:
            r += "['"
            for gr in self.gramm:
                if len(r) > 2:
                    r += "', '"
                r += ','.join(tag for tag in sorted(gr.split(','))
                              if len(tag) > 0)
            r += "']\n"
        r += self.wfGlossed + '\n'
        r += self.gloss + '\n'
        for field, value in self.otherData:
            r += field + '\t' + str(value) + '\n'
        return r

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if self.wf != other.wf or (type(self.lemma) == str and self.lemma != other.lemma):
            return False
        return str(self) == str(other)

    def __ne__(self, other):
        return not self.__eq__(other)
