import re
import subprocess
import html
from .wordform import Wordform


class CGDisambiguator:
    rxCGWords = re.compile('"<[^<>]*>"\n(?:\t[^\n]*\n)*', flags=re.DOTALL)
    rxCGAna = re.compile('<ana_([0-9]+)> *([^\r\n]*)', flags=re.DOTALL)
    rxPunc = re.compile('^[^\\w]+$', flags=re.DOTALL)

    def __init__(self, g):
        self.g = g

    def translate2cg_word(self, analyses):
        """
        Translate a list of Wordform objects that represent possible
        analyses of one word into a readings list in the CG format.
        Return translated words as a string.
        """
        if len(analyses) <= 0:
            return ''
        wf = html.escape(analyses[0].wf).replace('\n', '\\n')     # wf is the same for all analyses
        if len(analyses) == 1 and len(analyses[0].lemma) <= 0:
            if self.rxPunc.search(analyses[0].wf) is not None:
                return '"<' + wf + '>"\n\t"' + wf + '" punct\n'
            return '"<' + wf + '>"\n'
        wordCG = '"<' + wf + '>"\n'
        for iAna in range(len(analyses)):
            lex = html.escape(analyses[iAna].lemma).replace('\n', '\\n')
            gr = ' '.join(html.escape(tag.strip())
                          for tag in analyses[iAna].gramm.split(',')).strip()
            wordCG += '\t"' + lex + '" <ana_' + str(iAna) + '>'
            if len(gr) > 0:
                wordCG += ' ' + gr
            wordCG += '\n'
        return wordCG

    def translate2cg(self, analyses):
        """
        Translate a (possibly nested) list of lists of Wordform objects into
        a flat readings list in the CG format. Put <SENT_BOUNDARY>
        where a list starts or ends.
        Return translated words as a string.
        """
        cgAnalyses = ''
        for i in range(len(analyses)):
            if type(analyses[i]) == list:
                if len(analyses[i]) <= 0:
                    continue
                elif all(type(ana) == Wordform for ana in analyses[i]):
                    cgAnalyses += self.translate2cg_word(analyses[i])
                else:
                    cgAnalyses += self.translate2cg(analyses[i]) + '"<SENT_BOUNDARY>"\n'
        return cgAnalyses

    def disambiguate_cg(self, cgAnalyses, cgFile):
        """
        Call the CG processor to disambiguate a string with analyses translated
        into the CG format.
        Return a disambiguated string.
        """
        try:
            proc = subprocess.Popen('cg3 -g "' + cgFile + '"',
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    shell=True)
            text, err = proc.communicate(cgAnalyses.encode('utf-8'))
            proc.wait()
            cgAnalysesDisamb = text.decode('utf-8').replace('\r', '\n').replace('\n\n', '\n')
            return cgAnalysesDisamb
        except OSError:
            return cgAnalyses

    def cg2uniparser_word(self, anaOrig, cgWord):
        """
        Modify the original analysis (as a list of Wordform objects)
        based on the disambiguated version in the CG format.
        Modify the original analysis, do not return anything.
        """
        if len(anaOrig) <= 0 or '" punct' in cgWord:
            return
        wf = anaOrig[0].wf
        remainingAna = {}  # number: CG analysis
        for iAna, disambTags in self.rxCGAna.findall(cgWord):
            iAna = int(iAna)
            remainingAna[iAna] = set([html.unescape(tag)
                                      for tag in disambTags.strip().split(' ')
                                      if len(tag) > 0])

        for iAna in range(len(anaOrig) - 1, -1, -1):
            if iAna not in remainingAna:
                del anaOrig[iAna]
                continue
            ana = anaOrig[iAna]
            disambTags = remainingAna[iAna]
            grammTags = [tag.strip() for tag in ana.gramm.split(',')]
            for iTag in range(len(grammTags) - 1, -1, -1):
                if grammTags[iTag] not in disambTags:
                    del grammTags[iTag]
            grammTags += [tag for tag in disambTags - set(grammTags)]
            ana.gramm = ','.join(grammTags)

        if len(anaOrig) <= 0:
            # If all analyses have been removed by CG
            anaOrig.append(Wordform(self.g, wf=wf))

    def cg2uniparser_words(self, analyses, cgWords, curWord=0):
        """
        Recursively translate the disambiguated analyses as list
        of words in CG format back by modifying the analyses list.
        Start from disambiguated word no. curWord.
        Modify analyses, return current CG word number.
        """
        while curWord < len(cgWords) and cgWords[curWord].startswith('"<SENT_BOUNDARY>"'):
            curWord += 1
        for i in range(len(analyses)):
            if curWord >= len(cgWords):
                # This should not happen
                break
            if type(analyses[i]) == list:
                if len(analyses[i]) <= 0:
                    continue
                elif all(type(ana) == Wordform for ana in analyses[i]):
                    self.cg2uniparser_word(analyses[i], cgWords[curWord])
                    curWord += 1
                    while curWord < len(cgWords) and cgWords[curWord].startswith('"<SENT_BOUNDARY>"'):
                        curWord += 1
                else:
                    curWord = self.cg2uniparser_words(analyses[i], cgWords, curWord=curWord)
        return curWord

    def cg2uniparser(self, analyses, cgAnalysesDisamb):
        """
        Translate the disambiguated analyses in CG format back
        by modifying the analyses list.
        Modify analyses, do not return anything.
        """
        cgWords = self.rxCGWords.findall(cgAnalysesDisamb)
        self.cg2uniparser_words(analyses, cgWords)

    def disambiguate_analyses(self, analyses, cgFile):
        """
        Disambiguate a (possibly nested) list of analysis by
        translating it into CG format and calling the cg executable.
        Only works if cg3 is installed (apt-get install cg3).
        Modify analyses, do not return anything.
        """
        cgAnalyses = self.translate2cg(analyses)
        cgAnalysesDisamb = self.disambiguate_cg(cgAnalyses, cgFile)
        self.cg2uniparser(analyses, cgAnalysesDisamb)
