from .analyze import Analyzer

if __name__ == '__main__':
    a = Analyzer()
    stats = a.analyze_wordlist()
    print(stats)
