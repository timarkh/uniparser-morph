import sys
import time
import os
from .morph_parser import Parser
from .grammar import Grammar


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

        if verbose:
            print('\n\n**** Starting parser... ****\n')
        t1 = time.time()
        if self.m is not None:
            if verbose:
                print('\n\nParser already initialized\n')
        else:
            self.m = Parser(g=self.g,
                            verbose=self.parserVerbosity,
                            parsingMethod=self.parsingMethod)
            self.m.fill_stems()
            if self.parsingMethod == 'fst':
                self.m.fill_affixes()
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


if __name__ == '__main__':
    paradigmFile = '../paradigms.txt'
    lexFile = '../lexemes.txt'
    lexRulesFile = '../lex_rules.txt'
    derivFile = '../derivations.txt'
    conversionFile = '../stem_conversions.txt'
    cliticFile = '../clitics.txt'
    delAnaFile = '../bad_analyses.txt'
    freqListFile = '../wordlist.csv'
    freqListSeparator = '\t'
    parserVerbosity = 0
    parsingMethod = 'fst'
    errorFile = None
    parsedFile = None
    unparsedFile = None
    xmlOutput = True
    for iArg in range(1, len(sys.argv)):
        if iArg == 1 and not sys.argv[iArg].startswith('-'):
            freqListFile = sys.argv[iArg]
        elif sys.argv[iArg].startswith('-'):
            command = sys.argv[iArg]['-']
            if iArg == len(sys.argv) - 1 and command not in ['xml']:
                print('No value specified for the parameter', command)
                continue
            if command in ['p', 'paradigms']:
                paradigmFile = sys.argv[iArg + 1]
            elif command in ['l', 'lexemes']:
                lexFile = sys.argv[iArg + 1]
            elif command in ['lr', 'lex_rules']:
                lexRulesFile = sys.argv[iArg + 1]
            elif command in ['conv', 'conversions']:
                conversionFile = sys.argv[iArg + 1]
            elif command in ['d', 'derivations']:
                derivFile = sys.argv[iArg + 1]
            elif command in ['cl', 'clitics']:
                cliticFile = sys.argv[iArg + 1]
            elif command in ['ba', 'bad_analyses']:
                delAnaFile = sys.argv[iArg + 1]
            elif command in ['pf', 'parsed']:
                parsedFile = sys.argv[iArg + 1]
            elif command in ['uf', 'unparsed']:
                unparsedFile = sys.argv[iArg + 1]
            elif command in ['el', 'error_log']:
                errorFile = sys.argv[iArg + 1]
            elif command in ['v', 'verbosity']:
                try:
                    parserVerbosity = int(sys.argv[iArg + 1])
                except ValueError:
                    pass
                if parserVerbosity not in [0, 1, 2]:
                    if parserVerbosity > 2:
                        parserVerbosity = 2
                    else:
                        parserVerbosity = 0
            elif command in ['pm', 'parsing_method']:
                parsingMethod = sys.argv[iArg + 1]
                if parsingMethod not in ['fst', 'hash']:
                    print('Unrecognized parsing method, assuming fst.')
                    parsingMethod = 'fst'
            elif command == 'sep_colon':
                freqListSeparator = ':'
            elif command == 'sep_tab':
                freqListSeparator = '\t'
            elif command == 'sep_comma':
                freqListSeparator = ','
            elif command == 'sep_semicolon':
                freqListSeparator = ';'
            elif command == 'sep_space':
                freqListSeparator = ' '
            elif command == 'xml':
                xmlOutput = True
            elif command == 'noxml':
                xmlOutput = False
    analyze(freqListFile, paradigmFile, lexFile, lexRulesFile, derivFile, conversionFile,
            cliticFile, delAnaFile, parsedFile, unparsedFile, errorFile, xmlOutput,
            False, parserVerbosity, freqListSeparator, parsingMethod=parsingMethod)
