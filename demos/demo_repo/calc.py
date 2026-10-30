def average(numbers):
    total = 0
    for i in range(1, len(numbers)):  
        total += numbers[i]
    return total / len(numbers)