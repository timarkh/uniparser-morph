import copy
import json
import re
from .paradigm import Paradigm


def deriv_for_paradigm(g, paradigm):
    """
    Generate a Derivation object for the given paradigm.
    """
    derivLinks = {}     # recurs_class -> set of Derivation names
    maxRecursClass = 0
    for derivLink in paradigm.derivLinks:
        recursClass, derivLink = get_recurs_class(g, derivLink)
        # print(recursClass, derivLink['value'])
        if maxRecursClass < recursClass:
            maxRecursClass = recursClass
        pName = fork_deriv(g, derivLink, paradigm.name)
        if len(pName) > 0:
            try:
                derivLinks[recursClass].add(pName)
            except KeyError:
                derivLinks[recursClass] = {pName}
    handle_recurs_classes(g, derivLinks, maxRecursClass)
    unifiedDerivContent = []
    for derivNamesSet in derivLinks.values():
        for derivName in derivNamesSet:
            unifiedDerivContent.append({'name': 'paradigm',
                                        'value': derivName,
                                        'content': []})
    if len(unifiedDerivContent) <= 0:
        return
    unifiedName = '#deriv#paradigm#' + paradigm.name
    unifiedDeriv = Derivation(g, {'name': 'deriv-type', 'value': unifiedName,
                                  'content': unifiedDerivContent})
    g.derivations[unifiedName] = unifiedDeriv


def fork_deriv(g, derivLink, paradigmName):
    """
    Create a new derivation with customized properties on the basis
    of an existing one.
    Return the name of the resulting derivation.
    """
    derivName = derivLink['value']
    try:
        newDeriv = copy.deepcopy(g.derivations['#deriv#' + derivName])
    except KeyError:
        g.raise_error('No derivation named ' + derivName)
        return ''
    existingParadigms = newDeriv.find_property('paradigm')
    if len(existingParadigms) <= 0:
        newDeriv.add_property('paradigm', paradigmName)
    if derivLink['content'] is not None:
        for propName in {obj['name'] for obj in derivLink['content']}:
            newDeriv.del_property(propName)
        for obj in derivLink['content']:
            newDeriv.add_property(obj['name'], obj['value'])
    newDerivName = newDeriv.dictDescr['value'] + '#paradigm#' + paradigmName
    newDeriv.dictDescr['value'] = newDerivName
    g.derivations[newDerivName] = newDeriv
    return newDerivName


def get_recurs_class(g, derivLink):
    """Find the recurs_class property in the contents.
    Return its value and the dictionary with recurs_value removed."""
    recursClass = 0
    if derivLink['content'] is None or len(derivLink['content']) <= 0:
        return 0, derivLink
    newDerivLink = copy.deepcopy(derivLink)
    for iObj in range(len(newDerivLink['content']))[::-1]:
        obj = newDerivLink['content'][iObj]
        if obj['name'] == 'recurs_class':
            try:
                recursClass = int(obj['value'])
            except ValueError:
                g.raise_error('Incorrect recurs_class value: ' +
                                            obj['value'])
            newDerivLink['content'].pop(iObj)
    return recursClass, newDerivLink


def handle_recurs_classes(g, derivLinks, maxRecursClass):
    """
    For every derivation in the dictionary, add links to the derivations
    with recurs_class less than recurs_class of that derivation.
    """
    links = []
    restrictedDerivs = set([re.sub('#paradigm#[^#]+$', '', dv)
                            for s in derivLinks.values() for dv in s])
    prevDerivLinks = set()
    for recursClass in range(maxRecursClass + 1):
        try:
            curDerivLinks = derivLinks[recursClass]
            restrictedDerivs -= set([re.sub('#paradigm#[^#]+$', '', dv)
                                     for dv in prevDerivLinks])
            curRestrictedDerivs = copy.deepcopy(restrictedDerivs)
            prevDerivLinks = curDerivLinks
        except KeyError:
            # print('No recurs_class ' + str(recursClass))
            continue
        linksExtension = []
        for derivName in curDerivLinks:
            try:
                deriv = g.derivations[derivName]
            except KeyError:
                g.raise_error('No derivation named ' + derivName)
                continue
            for link in links:
                deriv.add_dict_property(link)
            deriv.restrictedDerivs = curRestrictedDerivs
            if recursClass < maxRecursClass:
                newLink = {'name': 'paradigm', 'value': derivName,
                           'content': [copy.deepcopy(p)
                                       for p in deriv.find_property('paradigm')]}
                for link in links:
                    newLink['content'].append(copy.deepcopy(link))
                linksExtension.append(newLink)
        links += linksExtension


def add_restricted(g, recursCtr, restrictedDerivs):
    recursCtr = recursCtr.copy()
    for rd in restrictedDerivs:
        recursCtr[rd] = g.RECURS_LIMIT + 1
    return recursCtr


def extend_leaves(g, data, sourceParadigm, recursCtr=None,
                  removeLong=False, depth=0):
    # recursCtr: derivation name -> number of times it has been used
    if recursCtr is None:
        recursCtr = {}
    depth += 1
    data2add = []
    # print(json.dumps(recursCtr, indent=1))
    # print(len(recursCtr), max([0] + recursCtr.values()))
    for iObj in range(len(data))[::-1]:
        obj = data[iObj]
        if obj['name'] != 'paradigm':
            continue
        elif obj['value'].startswith('#deriv#'):
            shortName = re.sub('#paradigm#[^#]+$', '',
                               obj['value'], flags=re.U)
            try:
                recursCtr[shortName] += 1
            except KeyError:
                recursCtr[shortName] = 1
            if recursCtr[shortName] > g.RECURS_LIMIT or \
                    depth > g.DERIV_LIMIT:
                if removeLong:
                    data.pop(iObj)
                continue
            try:
                deriv = g.derivations[obj['value']]
            except KeyError:
                continue
            recursCtrNext = add_restricted(g, recursCtr, deriv.restrictedDerivs)
            extend_leaves(g, obj['content'], sourceParadigm,
                          recursCtrNext, removeLong, depth)
        else:
            # print obj['value']
            if depth > g.DERIV_LIMIT or obj['value'] == sourceParadigm:
                continue
            try:
                deriv = g.derivations['#deriv#paradigm#' + obj['value']]
            except KeyError:
                continue
            subsequentDerivs = copy.deepcopy(deriv.find_property('paradigm'))
            # print(json.dumps(subsequentDerivs, indent=1))
            recursCtrNext = add_restricted(g, recursCtr, deriv.restrictedDerivs)
            extend_leaves(g, subsequentDerivs, sourceParadigm,
                          recursCtrNext, True, depth)
            data2add += subsequentDerivs
    data += data2add


class Derivation:
    """
    An auxiliary class where derivations are represented by dictionaries.
    After priorities are handled, all derivations should be transformed into
    paradigms.
    """

    def __init__(self, g, dictDescr, errorHandler=None):
        self.g = g
        self.dictDescr = copy.deepcopy(dictDescr)
        if self.dictDescr['content'] is None:
            self.dictDescr['content'] = []
        if errorHandler is None:
            self.errorHandler = self.g.errorHandler
        else:
            self.errorHandler = errorHandler
        self.restrictedDerivs = set()

    def raise_error(self, message, data=None):
        if self.errorHandler is not None:
            self.errorHandler.raise_error(message, data)

    def content(self):
        return self.dictDescr['content']

    def find_property(self, propName):
        return [el for el in self.content() if el['name'] == propName]

    def add_property(self, name, value):
        self.dictDescr['content'].append({'name': name, 'value': value,
                                          'content': []})

    def add_dict_property(self, dictProperty):
        self.dictDescr['content'].append(copy.deepcopy(dictProperty))

    def del_property(self, propName):
        for iObj in range(len(self.dictDescr['content']))[::-1]:
            obj = self.dictDescr['content'][iObj]
            if obj['name'] == propName:
                self.dictDescr['content'].pop(iObj)

    def __str__(self):
        return json.dumps(self.dictDescr, ensure_ascii=False, indent=2)

    def build_links(self):
        """Add the links from all subsequent derivations to self."""
        newDerivLinks = []
        for derivLink in self.find_property('paradigm'):
            if (not derivLink['value'].startswith('#deriv#')) or\
                (derivLink['content'] is not None and
                 len(derivLink['content']) > 0):
                newDerivLinks.append(derivLink)
                continue
            newDerivLink = copy.deepcopy(derivLink)
            try:
                targetDeriv = self.g.derivations[newDerivLink['value']]
            except KeyError:
                self.raise_error('No derivation named ' + newDerivLink['value'])
                continue
            newDerivLink['content'] = \
                copy.deepcopy(targetDeriv.find_property('paradigm'))
            newDerivLinks.append(newDerivLink)
        self.del_property('paradigm')
        for newDerivLink in newDerivLinks:
            self.add_dict_property(newDerivLink)

    def extend_leaves(self):
        """
        For the leaves in the subsequent derivation tree, which are
        real paradigms, add their subsequent derivations, if needed.
        """
        m = re.search('#deriv#paradigm#([^#]+$)', self.dictDescr['value'],
                      flags=re.U)
        if m is None:
            return
        paradigmName = m.group(1)
        recursCtr = {}
        for derivName in self.restrictedDerivs:
            recursCtr[derivName] = self.g.RECURS_LIMIT + 1
        extend_leaves(self.g, self.dictDescr['content'], paradigmName, recursCtr)

    def to_paradigm(self):
        """
        Create a paradigm from self.dictDescr and return it.
        """
        return Paradigm(self.g, self.dictDescr, self.errorHandler)
