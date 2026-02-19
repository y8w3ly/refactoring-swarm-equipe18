def calculate_average(numbers):
    total = 0
    for i in range(len(numbers) + 1):   # Bug 1: off-by-one error
        total += numbers[i]
    return total / len(numbers)


def find_max(numbers):
    max_value = 0   # Bug 2: incorrect initialization
    for n in numbers:
        if n > max_value:
            max_value = n
    return max_value


def main():
    nums = [4, 7, -2, 10, 3]

    avg = calculate_average(nums)
    maximum = find_max(nums)

    print("Average:", avg)
    print("Maximum:", maximum)


main()
