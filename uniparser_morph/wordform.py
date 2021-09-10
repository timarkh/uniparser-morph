import copy
import re
from .common_functions import wfPropertyFields, check_compatibility, join_stem_flex


class Wordform:
    rxLexTag = re.compile(',?\\bLEX:([^,:]*):([^,:]*)')
    rxLexTagOtherField = re.compile('^([^=]+)=(.*)')
    propertyFields = wfPropertyFields
    printableOtherFields = {'trans_ru', 'trans_en', 'trans_de', 'lex2', 'gramm2',
                            'trans_ru2', 'trans_en2', 'trans_de2', 'root', 'stamm',
                            'id', 'sem', 'sem2'}
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
        self.subwords = []      # Wordform objects, one for additional incorporated word
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
        if flex.otherData is not None:
            for k, v in flex.otherData:
                if k not in Wordform.printableOtherFields or len(v) <= 0:
                    continue
                bFound = False
                for i in range(len(self.otherData)):
                    if self.otherData[i][0] != k:
                        continue
                    bFound = True
                    if k == 'id':
                        self.otherData[i] = ('id', ','.join(_ for _ in sorted(set(self.otherData[i][1].split(',')) | set(v.split(',')))))
                    else:
                        self.otherData[i] = (self.otherData[i][0], self.otherData[i][1] + '; ' + v)
                if not bFound:
                    self.otherData.append((k, v))

    def expand_lex_morphs(self):
        """
        Find tags that look like LEX:xxx:yyy and expand them. They
        come from inflexions which actually contain items that require
        separate lemmata, POS tags and, possibly, other fields, such as
        intraclitics. Depending on self.g.COMPLEX_WF_AS_BAGS parameter value,
        either concatenate lemma, gramm etc. fields with the data taken
        from LEX:xxx:yyy as strings, or append them as list elements.
        """
        lexTags = self.rxLexTag.findall(self.gramm)
        if len(lexTags) <= 0:
            return
        self.gramm = self.rxLexTag.sub('', self.gramm)
        for lemma, gramm in lexTags:
            gramm = gramm.replace(';', ',')
            lex2add = Wordform(g=self.g, wf='')
            lex2add.lemma = lemma
            for tag in gramm.split(','):
                m = self.rxLexTagOtherField.search(tag)
                if m is not None:
                    if m.group(1) not in ('wf', 'lemma', 'gramm', 'stem', 'gloss', 'parts', 'wfGlossed'):
                        lex2add.otherData.append((m.group(1), m.group(2)))
                else:
                    if len(lex2add.gramm) > 0:
                        lex2add.gramm += ','
                    lex2add.gramm += tag.strip()
            self.subwords.append(lex2add)

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

    def append_subword_data(self):
        """
        If COMPLEX_WF_AS_BAGS is set, append lemma, tags and other
        data from the subwords as strings, concatenating them with
        + or , signs. Return concatenated strings.
        """
        gramm = self.gramm.strip()
        lemma = self.lemma.strip()
        otherData = self.otherData
        if self.g.COMPLEX_WF_AS_BAGS and len(self.subwords) > 0:
            otherData = copy.deepcopy(otherData)
            for sw in self.subwords:
                lemma += '+' + sw.lemma
                if len(gramm) > 0 and len(sw.gramm) > 0:
                    gramm += ','
                gramm += sw.gramm
                for field, value in sw.otherData:
                    bAdded = False
                    for i in range(len(otherData)):
                        if otherData[i][0] == field:
                            bAdded = True
                            otherData[i] = (field, otherData[i][1] + ' + ' + value)
                            break
                    if not bAdded:
                        otherData.append((field, value))
        return lemma, gramm, otherData

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
        lemma = self.lemma.strip()
        otherData = self.otherData
        if len(self.subwords) > 0 and self.g.COMPLEX_WF_AS_BAGS:
            lemma, gramm, otherData = self.append_subword_data()
        if sort_tags:
            gramm = ','.join(tag for tag in sorted(self.gramm.split(','))
                             if len(tag) > 0)
        r = '<ana lex="' + lemma + '" gr="' + gramm + '"'
        if glossing:
            r += ' parts="' + self.wfGlossed + '" gloss="' + self.gloss + '"'
        for field, value in otherData:
            if field in Wordform.printableOtherFields:
                r += ' ' + field + '="' + value.replace('"', "'") + '"'
        if len(self.subwords) > 0 and not self.g.COMPLEX_WF_AS_BAGS:
            return r + '></ana>' + ''.join(sw.to_xml(glossing=False, sort_tags=sort_tags)
                                           for sw in self.subwords)
        return r + '></ana>'

    def to_json(self, glossing=True, sort_tags=False):
        """
        Return a JSON representation of the analysis.
        If glossing is True, include the glossing information.
        If categories.json was supplied, transform gramm tag string
        into a dictionary {category: value(s)}
        """
        if self.lemma is None:
            self.lemma = ''
        if self.gramm is None:
            self.gramm = ''
        gramm = self.gramm.strip()
        lemma = self.lemma.strip()
        otherData = self.otherData
        if len(self.subwords) > 0 and self.g.COMPLEX_WF_AS_BAGS:
            lemma, gramm, otherData = self.append_subword_data()
        r = {
            'wf': self.wf,
            'lemma': lemma
        }
        if sort_tags:
            r['gramm'] = [tag for tag in sorted(gramm.split(','))
                          if len(tag) > 0]
        else:
            r['gramm'] = [tag for tag in gramm.split(',')
                          if len(tag) > 0]
        if self.g.categories is not None and len(self.g.categories) > 0:
            gramm = {}
            for tag in r['gramm']:
                cat = 'unassigned'
                if tag in self.g.categories:
                    cat = self.g.categories[tag]
                if cat in gramm and len(gramm[cat]) > 0:
                    gramm[cat] += ','
                else:
                    gramm[cat] = ''
                gramm[cat] += tag
            r['gramm'] = gramm
        if glossing:
            r['wfGlossed'] = self.wfGlossed
            r['gloss'] = self.gloss
        for field, value in otherData:
            if field in Wordform.printableOtherFields:
                r[field] = value
        if len(self.subwords) > 0 and not self.g.COMPLEX_WF_AS_BAGS:
            r['subwords'] = [sw.to_json(glossing=False, sort_tags=sort_tags)
                             for sw in self.subwords]
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
        if len(self.subwords) > 0:
            r += '*** SUBWORDS ***\n'
            for sw in self.subwords:
                r += str(sw) + '-------------------\n'
        return r

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if self.wf != other.wf or (type(self.lemma) == str and self.lemma != other.lemma):
            return False
        return str(self) == str(other)

    def __ne__(self, other):
        return not self.__eq__(other)
