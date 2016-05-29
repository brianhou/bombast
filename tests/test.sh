for f in tests/*.py; do
    echo Running $f
    bombast --seed 0 --iters 3 $f
done
