def largest(numbers):
    biggest = 0
    for n in numbers:
        if n > biggest:
            biggest = n
    return biggest
