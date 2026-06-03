Start by computing the merge base between `HEAD` and `{{base_branch}}`'s upstream (for example with `git merge-base HEAD "$(git rev-parse --abbrev-ref "{{base_branch}}@{upstream}")"`).
Then review `git diff` against that SHA so the findings match what would actually merge into `{{base_branch}}`.
