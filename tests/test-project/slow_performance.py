import time

def complex_processing(data):
    """
    Function with high cyclomatic complexity and O(n^2) performance issues.
    """
    results = []
    
    # High complexity: deeply nested loops and conditions
    for i in range(len(data)):
        for j in range(len(data)): # O(n^2) loop
            if i != j:
                if data[i] > data[j]:
                    if data[i] % 2 == 0:
                        if data[j] % 2 != 0:
                            results.append(data[i] - data[j])
                        else:
                            results.append(data[i] + data[j])
                    else:
                        if data[j] > 5 and data[j] < 100:
                            time.sleep(0.1) # Intentional slow-down
                            results.append(data[i] * data[j])
                elif data[i] == data[j]:
                    if i > 0:
                        results.append(0)
                        results.append(0)
                        
    return results
