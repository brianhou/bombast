x = 10
if x == 1:
    for e in range(x):
        print(e)
elif False:
    for e in range(x, x + 5):
        if e % 2 == 0:
            break
        else:
            continue
else:
    while x > 1:
        x -= 1

try:
    1 / 0
except ValueError as e:
    print("value")
except RuntimeError:
    print("runtime")
except:
    print("error")
finally:
    print("finally")

with open("test_control.txt", "w") as f:
    f.write("hi")
import os

os.remove("test_control.txt")
