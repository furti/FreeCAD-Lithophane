import threading

def numberOfConcurrentThreads():
    return 2

def computeAsync(startParameters, preparator, threadFactory, collector):
    threadDataList = preparator(startParameters, numberOfConcurrentThreads())
    threads = []
    resultList = []
    
    for threadData in threadDataList:
        thread = threadFactory(threadData)
        threads.append(thread)

        thread.start()
    
    # Wait until all threads have finished
    for thread in threads:
        thread.join()
        resultList.append(thread.getResult())
    
    return collector(resultList)

# Simple test case when directly called
if __name__ == "__main__":
    class TestThread(threading.Thread):
        def __init__(self, numbers):
            super(TestThread, self).__init__()
            self.numbers = numbers
        
        def run(self):
            self.result = sum(self.numbers)
        
        def getResult(self):
            return self.result

    def dataPreparator(startParameter, numberOfThreads):
        dataList = []
        
        for i in range(numberOfThreads):
            dataList.append([startParameter + i * 10, startParameter + (i + 1) * 10])
        
        return dataList
    
    def createTestThread(numbers):
        return TestThread(numbers)
    
    def sumsToString(sums):
        return ', '.join(str(s) for s in sums)
    
    #Should print "14, 34"
    print(computeAsync(2, dataPreparator, createTestThread, sumsToString))