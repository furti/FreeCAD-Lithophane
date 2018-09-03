class Matcher(object):
    def __init__(self, expected=None):
        self.expected = expected
    
    def matches(self, actual):
        raise NotImplementedError('Base classes must override this method!')
    
    def expectedMessage(self):
        return str(self.expected)
    
    def describeActual(self, actual):
        return str(actual)

def assertThat(actual, matcher):
    if not matcher.matches(actual):
        message = '\nExpected: %s\nBut got:  %s' % (matcher.expectedMessage(), matcher.describeActual(actual))

        raise AssertionError(message)

class NotNoneMatcher(Matcher):
    def matches(self, actual):
        return actual is not None
    
    def expectedMessage(self):
        return 'an object that is not None'

def isNotNone():
    return NotNoneMatcher()

class EqualToMatcher(Matcher):
    def matches(self, actual):
        return actual == self.expected

def isEqualTo(expected):
    return EqualToMatcher(expected)

def isrue():
    return EqualToMatcher(True)

def isFalse():
    return EqualToMatcher(False)

class HasAttributeValueMatcher(Matcher):

    def matches(self, actual):
        attributeName = self.expected[0]
        attributeValue = self.expected[1]

        if not hasattr(actual, attributeName):
            self.attributeAvailable = False

            return False
        
        self.attributeAvailable = True

        return getattr(actual, attributeName) == attributeValue
    
    def expectedMessage(self):
        return 'Object with attribute [%s]=%s' % self.expected
    
    def describeActual(self, actual):
        attributeName = self.expected[0]
        
        if not self.attributeAvailable:
            return '%s with no attribute of name [%s]' % (actual, attributeName)

        return '%s with attribute [%s]=%s' % (actual, attributeName, getattr(actual, attributeName))

class HasAttributeMatcher(Matcher):

    def matches(self, actual):
        return hasattr(actual, self.expected)
    
    def expectedMessage(self):
        return 'Object with attribute [%s]' % (self.expected)
    
def hasAttributeOfValue(attributeName, expectedValue):
    return HasAttributeValueMatcher((attributeName, expectedValue))

def hasAttribute(attributeName):
    return HasAttributeMatcher(attributeName)

class IsOfTypeMatcher(Matcher):

    def matches(self, actual):
        if not hasattr(actual, 'TypeId'):
            return False
        
        return actual.TypeId == self.expected
    
    def expectedMessage(self):
        'Object with TypeId of [%s]' % (self.expected)
    
    def describeActual(self, actual):
        if not hasattr(actual, 'TypeId'):
            return '%s with no TypeId' % (actual)
        
        return '%s with TypeId=%s' % (actual, actual.TypeId)

def isOfType(expectedType):
    return IsOfTypeMatcher(expectedType)

class TwodimensionalVectorListMatcher(Matcher):
    def __init__(self, expected, tolerance):
        super(TwodimensionalVectorListMatcher, self).__init__(expected)

        self.tolerance = tolerance

        self.numberOfLinesMismatch = None
        self.numberOfRowsMismatch = None
        self.vectorMismatch = None

    def matches(self, actual):
        actualLineCount = len(actual)
        expectedLineCount = len(self.expected)

        if actualLineCount != expectedLineCount:
            self.numberOfLinesMismatch = (actualLineCount, expectedLineCount)

            return False
        
        for lineIndex, expectedLine in enumerate(self.expected):
            actualLine = actual[lineIndex]

            actualRowCount = len(actualLine)
            expectedRowCount = len(expectedLine)

            if actualRowCount != expectedRowCount:
                self.numberOfRowsMismatch = (lineIndex, actualRowCount, expectedRowCount)

                return False
            
            for rowIndex, expectedVector in enumerate(expectedLine):
                actualVector = actualLine[rowIndex]

                if not actualVector.isEqual(expectedVector, self.tolerance):
                    self.vectorMismatch = (lineIndex, rowIndex, actualVector, expectedVector)

                    return False

        return True
    
    def expectedMessage(self):
        return 'multidimensional list of vectors'
    
    def describeActual(self, actual):
        if self.numberOfLinesMismatch is not None:
            return 'Number of lines differ %s:%s' % (self.numberOfLinesMismatch[0], self.numberOfLinesMismatch[1])

        if self.numberOfRowsMismatch is not None:
            return 'Number of rows %s:%s differ in line %s' % (self.numberOfRowsMismatch[1], self.numberOfRowsMismatch[2], self.numberOfRowsMismatch[0])
        
        if self.vectorMismatch is not None:
            return 'actual: %s expected: %s differ at %s:%s' % (self.vectorMismatch[2], self.vectorMismatch[3], self.vectorMismatch[0], self.vectorMismatch[1])

def matchesTowdimensionalListOfVectors(expected, tolerance=0.1):
    return TwodimensionalVectorListMatcher(expected, tolerance)
