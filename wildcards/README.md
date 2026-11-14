# Wildcards

Drop plain `.txt` files here, one entry per line. Write `__name__` in any Atlas prompt and it becomes a random line of `name.txt`.

* `__adjective__` → `wildcards/adjective.txt`
* `__character/profession__` → `wildcards/character/profession.txt` (or just `__profession__` when the name is unique)
* Lines starting with `#` and empty lines are ignored.
* A line can contain other wildcards (`a __adjective__ __profession__`), resolved up to 6 levels deep.
* Every occurrence is drawn separately, so two `__color__` can differ.
* The node's **seed** drives the draw: same seed, same words.
* The first Atlas node that receives the text resolves it. Later nodes only see plain words.
* Unknown names are left untouched (and reported in `info`), so another wildcard tool further down can still use them.
* No restart needed: edit a file, queue again.
