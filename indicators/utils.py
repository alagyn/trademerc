def minimax(i):
    mn = i[0]
    mx = i[0]
    for x in i:
        if x > mx:
            mx = x
        if x < mn:
            mn = x

    return mn, mx
