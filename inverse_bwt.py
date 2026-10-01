import sys


def inverse_bwt(transform):
    # Pair each char with its index, sort to get the first column;
    # stable sort maps i-th occurrence in last column to i-th in first.
    first = sorted(range(len(transform)), key=lambda i: (transform[i], i))
    i = transform.index('$')
    text = []
    for _ in range(len(transform)):
        i = first[i]
        text.append(transform[i])
    return ''.join(text)


if __name__ == '__main__':
    data = sys.stdin.read() if len(sys.argv) < 2 else open(sys.argv[1]).read()
    print(inverse_bwt(data.strip()))
