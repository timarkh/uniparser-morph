import sys
from .morph_parser import Parser
import time


def analyze(g,
            freqListFile,
            parsedFile,
            unparsedFile,
            parserVerbosity=0,
            freqListSeparator='\t',
            glossing=True,
            parsingMethod='fst'):
    print('\n\n**** Starting parser... ****\n')
    t1 = time.time()
    m = Parser(g=g,
               verbose=parserVerbosity,
               parsingMethod=parsingMethod)
    m.fill_stems()
    if parsingMethod == 'fst':
        m.fill_affixes()
    print('Parser initialized in', time.time() - t1, 'seconds.')
    t1 = time.time()

    m.verbose = 0

    nTokens, parsedRate = m.parse_freq_list(freqListFile,
                                            sep=freqListSeparator,
                                            fnameParsed=parsedFile,
                                            fnameUnparsed=unparsedFile,
                                            glossing=glossing,
                                            maxLines=10000000000)
    print('Frequency list processed,', parsedRate * 100, '% tokens parsed.')
    print('Average speed:', nTokens / (time.time() - t1), 'tokens per second.')


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
