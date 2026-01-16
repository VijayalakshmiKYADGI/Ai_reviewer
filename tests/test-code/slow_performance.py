def complex_logic(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                print("All positive")
                if x > 10:
                    print("X huge")
                else:
                    print("X small")
            else:
                print("Z negative")
                for i in range(10):
                    if i % 2 == 0:
                        print("Even")
                    else:
                        print("Odd")
        else:
            print("Y negative")
            while y < 0:
                y += 1
                if y == -5:
                    print("Halfway")
    else:
        print("X negative")
        if z < 0:
            print("Z also negative")
        elif z == 0:
            print("Z zero")
        else:
            print("Z positive")
            
    # More complexity
    result = 0
    for i in range(x):
        for j in range(y):
            for k in range(z):
                if (i + j + k) % 2 == 0:
                    result += 1
                elif (i * j) % 3 == 0:
                    result += 2
                else:
                    if k > 5:
                        result -= 1
                    else:
                        result += 3
    return result

def maintainability_nightmare():
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    f = 6
    # This function uses too many variables and operations
    return a+b+c+d+e+f * (a-b) / (c+d)
