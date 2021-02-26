import time
import os
import grammar
from analyze import analyze


class Analyzer:
    """
    Main class that contains top-level functions needed to
    load the rules and analyze words.
    """
    def __init__(self, verbose_grammar=False):
        self.verboseGrammar = verbose_grammar
        self.g = grammar.Grammar(verbose=self.verboseGrammar)   # Empty grammar
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

    def analyze_wordlist(self, freqListFile=None, parsedFile=None, unparsedFile=None):
        """
        Analyze a frequency list in a file. Write output to files with lists
        of analyzed and unanalyzed words. Use default filenames if none are
        specified as arguments.
        """
        if freqListFile is None:
            freqListFile = self.freqListFile
        if parsedFile is None:
            parsedFile = self.parsedFile
        if unparsedFile is None:
            unparsedFile = self.unparsedFile

        analyze(self.g,
                freqListFile,
                parsedFile,
                unparsedFile,
                parserVerbosity=self.parserVerbosity,
                freqListSeparator=self.freqListSeparator,
                glossing=self.glossing,
                parsingMethod=self.parsingMethod)


if __name__ == '__main__':
    a = Analyzer()
    a.analyze_wordlist()
