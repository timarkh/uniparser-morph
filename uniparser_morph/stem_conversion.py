from .reduplication import Replacement


class StemConversion:
    def __init__(self, dictDescr, errorHandler=None):
        self.stemConversions = {} #{source stem number -> {destination stem number ->
                                  # [replacementObject1, ...]}}
        self.errorHandler = errorHandler
        try:
            self.name = dictDescr['value']
            replacements = dictDescr['content']
        except KeyError:
            self.raise_error('Wrong stem conversion: ', dictDescr)
            return
        stemBase = -1
        dictsNewStem = []
        for obj in replacements:
            if obj['name'] == 'stem-base':
                try:
                    stemBase = int(obj['value'])
                except:
                    self.raise_error('Wrong base stem number: ', dictDescr)
                    return
            elif obj['name'] == 'new-stem' and 'content' in obj:
                try:
                    newStem = int(obj['value'])
                except:
                    self.raise_error('Wrong new stem number: ', dictDescr)
                    return
                dictsNewStem.append((obj['content'], newStem))
        for obj, newStem in dictsNewStem:
            self.add_conversion(obj, stemBase, newStem)

    def raise_error(self, message, data=None):
        if self.errorHandler is not None:
            self.errorHandler.RaiseError(message, data)

    def add_conversion(self, arrDictDescr, stemBase, newStem):
        for repl in arrDictDescr:
            try:
                if repl['name'] != 'replace':
                    self.raise_error('Incorrect field in a stem conversion description: ',
                                     repl)
                    continue
                self.add_operation(stemBase, newStem, Replacement(repl))
            except KeyError:
                self.raise_error('Error in a stem conversion description: ',
                                 repl)
    
    def add_operation(self, stemBase, newStem, repl):
        try:
            dictBase = self.stemConversions[stemBase]
        except KeyError:
            self.stemConversions[stemBase] = {}
            dictBase = self.stemConversions[stemBase]
        try:
            dictNew = dictBase[newStem]
        except KeyError:
            dictBase[newStem] = []
            dictNew = dictBase[newStem]
        dictNew.append(repl)

    def convert(self, stems):
        """Fill in the gaps in the stems description (list of tuples).
        The input is changed."""
        for stemBase in sorted(self.stemConversions):
            if stemBase < 0 or stemBase >= len(stems):
                break
            for newStem in sorted(self.stemConversions[stemBase]):
                # if there is no such stem, add it to the list
                for i in range(len(stems), newStem+1):
                    stems.append(())
                # explicitly written stems have higher priority and shouldn't
                # be owerwritten
                if len(stems[newStem]) <= 0:
                    stems[newStem] = self.convert_one(stems[stemBase],
                                                 self.stemConversions[stemBase][newStem])
##                    print stems[newStem]

    def convert_one(self, stemBaseVars, stemConversion):
        newStemVars = []
        for stem in stemBaseVars:
            for rule in stemConversion:
                stem = rule.convert(stem)
            newStemVars.append(stem)
        return tuple(newStemVars)
