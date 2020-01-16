set -e
for f in tests/*.py; do
    echo Running $f
    out=$(mktemp)
    bombast --seed 0 --iters 3 $f $out
    expected=$(mktemp)
    actual=$(mktemp)
    python3 $f > $expected
    python3 $out > $actual
    diff $expected $actual
    rm obfuscated.py
done
