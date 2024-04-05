## Cash Money

### Contributing:
* All commits must be on a feature branch. If you accidentally commit to main, don't worry,
it can be fixed.
* Please give branches short, but informative names.
* Use Pull-Requests to merge changes to main. Do not merge a PR without approval.
* Use squash-merges for your PRs when merging.

### Style Guidelines:
We use [YAPF](https://github.com/google/yapf) to autoformat the python code so
that you don't need to worry about style as much. I recommend using VSCode and
[this extension](https://marketplace.visualstudio.com/items?itemName=eeyore.yapf),
although there should be ways to get PyCharm to use it as well. Make sure you have
"format on save" enabled.

Aside from visual style, the only other important thing is to use type hints
for functions and class members. Feel free to type hint every variable if you
want, but functions and member variables are the important ones.