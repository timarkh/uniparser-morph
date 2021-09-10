import time
import os
import html
from .morph_parser import Parser
from .grammar import Grammar
from .wordform import Wordform
from .cg_disambiguate import CGDisambiguator


class Analyzer:
    """
    Main class that contains top-level functions needed to
    load the rules and analyze words.
    """
    def __init__(self, verbose_grammar=False):
        self.verboseGrammar = verbose_grammar
        self.g = Grammar(verbose=self.verboseGrammar)   # Empty grammar
        self.m = None                                   # Morphological parser
        self.disambiguator = CGDisambiguator(self.g)    # Constraint Grammar disambiguator
        self.paradigmFile = 'paradigms.txt'
        self.lexFile = 'lexemes.txt'
        self.lexRulesFile = 'lex_rules.txt'
        self.derivFile = 'derivations.txt'
        self.conversionFile = 'stem_conversions.txt'
        self.cliticFile = 'clitics.txt'
        self.delAnaFile = 'bad_analyses.txt'
        self.categoriesFile = 'categories.json'
        self.freqListFile = 'wordlist.csv'
        self.freqListSeparator = '\t'
        self.parserVerbosity = 0
        self.parsingMethod = 'fst'
        self.errorFile = None
        self.parsedFile = 'analyzed.txt'
        self.unparsedFile = 'unanalyzed.txt'
        self.glossing = True
        self.xmlOutput = True
        self.partialCompile = True
        self.minFlexLen = 4
        self.maxCompileTime = 60
        self.flattenSubwords = False

    def collect_filenames(self, s):
        """
        Check if the string s contains a name of a file or a directory.
        If the latter is true, return the list of .txt and .yaml files
        in the subtree. Otherwise, return [s].
        """
        filenames = []
        if os.path.isdir(s):
            for root, dirs, files in os.walk(s):
                for fname in files:
                    if not fname.lower().endswith(('.txt', '.yaml')):
                        continue
                    filenames.append(os.path.join(root, fname))
        else:
            if os.path.exists(s):
                filenames = [s]
        return filenames

    def load_grammar(self, verbose=False):
        """
        Load dictionaries and rules to be used for parsing.
        If verbose == True, print messages.
        """
        t1 = time.time()
        self.m = None       # Reset parser
        self.g.PARTIAL_COMPILE = self.partialCompile
        self.g.MIN_FLEX_LENGTH = self.minFlexLen
        self.g.MAX_COMPILE_TIME = self.maxCompileTime
        self.g.COMPLEX_WF_AS_BAGS = self.flattenSubwords
        paradigmFiles = self.collect_filenames(self.paradigmFile)
        lexFiles = self.collect_filenames(self.lexFile)
        lexRulesFiles = self.collect_filenames(self.lexRulesFile)
        derivFiles = self.collect_filenames(self.derivFile)
        conversionFiles = self.collect_filenames(self.conversionFile)
        cliticFiles = self.collect_filenames(self.cliticFile)
        delAnaFiles = self.collect_filenames(self.delAnaFile)
        categoriesFiles = self.collect_filenames(self.categoriesFile)

        if self.parsedFile is None or len(self.parsedFile) <= 0:
            self.parsedFile = self.freqListFile + '-parsed.txt'
        if self.unparsedFile is None or len(self.unparsedFile) <= 0:
            self.unparsedFile = self.freqListFile + '-unparsed.txt'

        n = self.g.load_categories(categoriesFiles)
        if verbose:
            print('Categories for', n, 'tags loaded.')
        n = self.g.load_stem_conversions(conversionFiles)
        if verbose:
            print(n, 'stem conversions loaded.')
        n = self.g.load_paradigms(paradigmFiles, compileParadigms=False)
        if verbose:
            print(n, 'paradigms loaded.')
        n = self.g.load_lexemes(lexFiles)
        if verbose:
            print(n, 'lexemes loaded.')
        n = self.g.load_lex_rules(lexRulesFiles)
        if verbose:
            print(n, 'lexical rules loaded.')
        n = self.g.load_derivations(derivFiles)
        if verbose:
            print(n, 'derivations loaded.')
        n = self.g.load_clitics(cliticFiles)
        if verbose:
            print(n, 'clitics loaded.')
        n = self.g.load_bad_analyses(delAnaFiles)
        if verbose:
            print(n, 'bad analyses loaded.')
        self.g.compile_all()
        if verbose:
            print('Paradigms and lexemes loaded and compiled in', time.time() - t1, 'seconds.')

    def initialize_parser(self, verbose=False):
        """
        If the parser has not been initialized yet, initialize it.
        """
        if verbose:
            print('\n\n**** Starting parser... ****\n')
        if self.m is not None:
            if verbose:
                print('\n\nParser already initialized.\n')
        else:
            self.m = Parser(g=self.g,
                            verbose=self.parserVerbosity,
                            parsingMethod=self.parsingMethod)
            self.m.fill_stems()
            if self.parsingMethod == 'fst':
                self.m.fill_affixes()

    def analyze_wordlist(self, freqListFile=None, parsedFile=None, unparsedFile=None,
                         freqListSeparator=None, verbose=False):
        """
        Analyze a frequency list in a file. Write output to files with lists
        of analyzed and unanalyzed words. Use default filenames if none are
        specified as arguments. Return some statistics.
        """
        self.g.COMPLEX_WF_AS_BAGS = self.flattenSubwords
        if freqListFile is None:
            freqListFile = self.freqListFile
        if parsedFile is None:
            parsedFile = self.parsedFile
        if unparsedFile is None:
            unparsedFile = self.unparsedFile
        if freqListSeparator is None:
            freqListSeparator = self.freqListSeparator

        t1 = time.time()
        self.initialize_parser(verbose=verbose)
        initTime = time.time() - t1
        if verbose:
            print('Parser initialized in', initTime, 'seconds.')

        t1 = time.time()
        nTypes, parsedRate = self.m.parse_freq_list(freqListFile,
                                                    sep=freqListSeparator,
                                                    fnameParsed=parsedFile,
                                                    fnameUnparsed=unparsedFile,
                                                    glossing=self.glossing,
                                                    maxLines=10000000000)
        anaTime = time.time() - t1
        if verbose:
            print('Frequency list processed,', parsedRate * 100, '% tokens parsed.')
            print('Average speed:', nTypes / anaTime, 'tokens per second.')
        stats = {
            'init_time': initTime,
            'analysis_time': anaTime,
            'types_processed': nTypes,
            'words_per_second': nTypes / anaTime,
            'percent_parsed_tokens': parsedRate * 100
        }
        return stats

    def __analyze_word__(self, word):
        """
        Analyze a single word. Return either a list of its analyses
        or a list with a single Wordform object that has only the wf
        property filled. Assume the parser has already been initialized.
        """
        self.g.COMPLEX_WF_AS_BAGS = self.flattenSubwords
        analyses = self.m.parse(word.lower())
        if len(analyses) <= 0:
            analyses = [Wordform(self.g, wf=word)]
        else:
            for ana in analyses:
                ana.wf = word       # Reverse lowering if needed.
            if format == 'xml':
                analyses = '<w>' + ''.join(ana.to_xml(glossing=self.glossing)
                                           for ana in analyses) +\
                           html.escape(word) + '</w>'
        if format == 'json':
            analyses = [ana.to_json() for ana in analyses]
        return analyses

    def analyze_words_nodisamb(self, words):
        """
        Analyze a single word or a (possibly nested) list of words. Return either a list of
        analyses (all possible analyses of the word) or a nested list of lists
        of analyses with the same depth as the original list.
        The analyses are Wordform objects.
        Do not perform disambiguation.
        """
        self.initialize_parser()
        if type(words) == str:
            return self.__analyze_word__(words)
        elif type(words) == list:
            return [self.analyze_words_nodisamb(w) for w in words]
        return []

    def analyses_to_xml(self, analyses):
        """
        Transform all lists of Wordform objects in a (possibly nested) list
        Modify the analyses list, do not return anything.
        """
        for i in range(len(analyses)):
            if type(analyses[i]) == list:
                if len(analyses[i]) <= 0:
                    continue
                elif all(type(ana) == Wordform for ana in analyses[i]):
                    analyses[i] = '<w>' + ''.join(ana.to_xml(glossing=self.glossing)
                                                  for ana in analyses[i]) + \
                                  html.escape(analyses[i][0].wf) + '</w>'
                else:
                    self.analyses_to_xml(analyses[i])
            elif type(analyses[i]) == Wordform:
                # This should not happen, but just in case
                analyses[i] = '<w>' + analyses[i].to_xml(glossing=self.glossing) + \
                              html.escape(analyses[i].wf) + '</w>'

    def analyses_to_json(self, analyses):
        """
        Transform all Wordform objects in a (possibly nested) list
        into dictionaries.
        Modify the analyses list, do not return anything.
        """
        for i in range(len(analyses)):
            if type(analyses[i]) == list:
                self.analyses_to_json(analyses[i])
            else:
                analyses[i] = analyses[i].to_json(glossing=self.glossing)

    def gramm_to_conll(self, objAna):
        pos = ''
        gramm = ''
        if type(objAna['gramm']) == dict:
            # categories.json was used
            if 'pos' in objAna['gramm']:
                pos = objAna['gramm']['pos']
                del objAna['gramm']['pos']
            elif 'POS' in objAna['gramm']:
                pos = objAna['gramm']['POS']
                del objAna['gramm']['POS']
            gramm = '|'.join(k + '=' + v for k, v in objAna['gramm'].items())
        else:
            gramm = ','.join(tag for tag in sorted(objAna['gramm']))
        return pos, gramm

    def analyses_to_conll(self, analyses):
        """
        Return a CoNLL-like representation of the analysis. Each token occupies
        one line, different annotation types go into different columns.
        Sentences are separated by blank lines.
        Only works if analyses contains either one word (list of Wordform objects),
        or one sentence (list of words), or a list of sentences.
        If there are ambiguous analyses, their annotation values are flattened
        and concatenated with |.
        If categories.json was supplied, POS tags go to POS column, and all the rest
        goes to Tags column in the form Category=Value.
        Return analyses as one concatenated multi-line string.
        """
        wf = ''
        if any(type(ana) == Wordform for ana in analyses):
            # Analyses for one token
            lemma = set()
            pos = set()
            gramm = set()
            parts = set()
            gloss = set()
            for ana in analyses:
                if type(ana) != Wordform:
                    continue
                wf = ana.wf.replace('\t', '\\t').replace('\n', '\\n')
                objAna = ana.to_json(glossing=self.glossing)
                lemma.add(objAna['lemma'])
                if self.glossing:
                    parts.add(objAna['wfGlossed'])
                    gloss.add(objAna['gloss'])
                curPos, curGramm = self.gramm_to_conll(objAna)
                if len(curPos) > 0:
                    pos.add(curPos)
                gramm.add(curGramm)
                if 'subwords' in objAna:
                    for sw in objAna['subwords']:
                        lemma.add(sw['lemma'])
                        curPos, curGramm = self.gramm_to_conll(sw)
                        if len(curPos) > 0:
                            pos.add(curPos)
                        gramm.add(curGramm)
            lemma = '|'.join(l for l in sorted(lemma)).replace('\t', '\\t').replace('\n', '\\n')
            pos = '|'.join(l for l in sorted(pos)).replace('\t', '\\t').replace('\n', '\\n')
            gramm = ' | '.join(l for l in sorted(gramm)).replace('\t', '\\t').replace('\n', '\\n')
            if len(lemma) <= 0:
                lemma = '_'
            if len(pos) <= 0:
                pos = '_'
            if len(gramm) <= 0:
                gramm = '_'
            if self.glossing:
                parts = '|'.join(l for l in sorted(parts)).replace('\t', '\\t').replace('\n', '\\n')
                gloss = '|'.join(l for l in sorted(gloss)).replace('\t', '\\t').replace('\n', '\\n')
                if len(parts) <= 0:
                    parts = '_'
                if len(gloss) <= 0:
                    gloss = '_'
            sAna = wf + '\t' + lemma + '\t' + pos + '\t' + gramm
            if self.glossing:
                sAna += '\t' + parts + '\t' + gloss
            sAna += '\n'
            return sAna
        elif len(analyses) <= 0:
            return ''
        sAna = ''
        sentIndex = 1
        for i in range(len(analyses)):
            if type(analyses[0]) != list or len(analyses[i]) <= 0:
                continue
            if type(analyses[i][0]) == Wordform:
                sAna += str(sentIndex) + '\t' + self.analyses_to_conll(analyses[i])
                sentIndex += 1
            elif type(analyses[i][0]) == list:
                sentIndex = 1
                sAna += self.analyses_to_conll(analyses[i]) + '\n'
        return sAna

    def analyze_words(self, words, cgFile='', format=None, disambiguate=True):
        """
        Analyze a single word or a (possibly nested) list of words. Return either a list of
        analyses (all possible analyses of the word) or a nested list of lists
        of analyses with the same depth as the original list.
        If format is None, the analyses are Wordform objects.
        If format == 'xml', the analyses for each word are united into an XML string.
        If format == 'json', the analyses are JSON objects (dictionaries).
        If format == 'conll', the result is one multi-line CoNLL-like string.
        Perform CG3 disambiguation if disambiguate == True and there is a CG3 file.
        """
        analyses = self.analyze_words_nodisamb(words)
        if disambiguate and len(cgFile) > 0 and os.path.exists(cgFile):
            self.disambiguator.disambiguate_analyses(analyses, cgFile)
        if format == 'xml':
            self.analyses_to_xml(analyses)
        elif format == 'json':
            self.analyses_to_json(analyses)
        elif format == 'conll':
            analyses = self.analyses_to_conll(analyses)
        return analyses
