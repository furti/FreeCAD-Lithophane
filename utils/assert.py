class Matcher():
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

def istNotNone():
    return NotNoneMatcher()

class EqualToMatcher(Matcher):
    def matches(self, actual):
        return actual == self.expected

def isEqualTo(expected):
    return EqualToMatcher(expected)

def isTrue():
    return EqualToMatcher(True)

def isFalse():
    return EqualToMatcher(False)

class HasAttributeValueMatcher(Matcher):

    def matches(self, actual):
        attributeName = self.expected[0]
        attributeValue = self.expected[1]

        print(hasattr(actual, attributeName))

        if not hasattr(actual, attributeName):
            self.attributeAvailable = False

            return False
        
        self.attributeAvailable = True

        return actual[attributeName] == attributeValue
    
    def expectedMessage(self):
        return 'Object with attribute [%s]=%s' % self.expected
    
    def describeActual(self, actual):
        attributeName = self.expected[0]
        
        if not self.attributeAvailable:
            return '%s with no attribute of name [%s]' % (actual, attributeName)

        return '%s with attribute [%s]=%s' % (actual, attributeName, actual[attributeName])

def hasAttributeOfValue(attributeName, expectedValue):
    return HasAttributeValueMatcher((attributeName, expectedValue))