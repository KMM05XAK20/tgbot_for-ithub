value = {
    'a'  '1': 2,
    'a' '2': 50,
    'a' '333': 777
}

print(value)

res = (item for item in range(800))

print(value['a333'] in res)
print(list(res))
