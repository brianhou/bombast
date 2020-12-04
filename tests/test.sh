set -ex

for f in tests/*.py; do
    echo Running $f
    g=$(mktemp)
    bombast --seed 0 --iters 3 $f $g
    diff <(python3 $f) <(python3 $g)
done
