import sys
import time
import os
from .morph_parser import Parser
from .grammar import Grammar
from .wordform import Wordform


class Analyzer:
    """
    Main class that contains top-level functions needed to
    load the rules and analyze words.
    """
    def __init__(self, verbose_grammar=False):
        self.verboseGrammar = verbose_grammar
        self.g = Grammar(verbose=self.verboseGrammar)   # Empty grammar
        self.m = None                                   # Morphological parser
        self.paradigmFile = 'paradigms.txt'
        self.lexFile = 'lexemes.txt'
        self.lexRulesFile = 'lex_rules.txt'
        self.derivFile = 'derivations.txt'
        self.conversionFile = 'stem_conversions.txt'
        self.cliticFile = 'clitics.txt'
        self.delAnaFile = 'bad_analyses.txt'
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
        paradigmFiles = self.collect_filenames(self.paradigmFile)
        lexFiles = self.collect_filenames(self.lexFile)
        lexRulesFiles = self.collect_filenames(self.lexRulesFile)
        derivFiles = self.collect_filenames(self.derivFile)
        conversionFiles = self.collect_filenames(self.conversionFile)
        cliticFiles = self.collect_filenames(self.cliticFile)
        delAnaFiles = self.collect_filenames(self.delAnaFile)

        if self.parsedFile is None or len(self.parsedFile) <= 0:
            self.parsedFile = self.freqListFile + '-parsed.txt'
        if self.unparsedFile is None or len(self.unparsedFile) <= 0:
            self.unparsedFile = self.freqListFile + '-unparsed.txt'

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

    def analyze_wordlist(self, freqListFile=None, parsedFile=None, unparsedFile=None, verbose=False):
        """
        Analyze a frequency list in a file. Write output to files with lists
        of analyzed and unanalyzed words. Use default filenames if none are
        specified as arguments. Return some statistics.
        """
        if freqListFile is None:
            freqListFile = self.freqListFile
        if parsedFile is None:
            parsedFile = self.parsedFile
        if unparsedFile is None:
            unparsedFile = self.unparsedFile

        t1 = time.time()
        self.initialize_parser(verbose=verbose)
        initTime = time.time() - t1
        if verbose:
            print('Parser initialized in', initTime, 'seconds.')

        t1 = time.time()
        nTypes, parsedRate = self.m.parse_freq_list(freqListFile,
                                                    sep=self.freqListSeparator,
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
        analyses = self.m.parse(word.lower())
        if len(analyses) <= 0:
            analyses = [Wordform(self.g, wf=word)]
        else:
            for ana in analyses:
                ana.wf = word       # Reverse lowering if needed.
        return analyses

    def analyze_words(self, words):
        """
        Analyze a single word or a list of words. Return either a list of
        Wordform objects (possible analyses of the word) or a list of lists
        of Wordform objects (all analyses for each of the words in the list).
        """
        self.initialize_parser()
        if type(words) == str:
            return self.__analyze_word__(words)
        elif type(words) == list:
            return [self.__analyze_word__(w) for w in words]
        return []
