Results from running analyses and collecting statistics from the Tressa (which is just the HEAD) branch of the 70 sample
repositories as forked by https://github.com/TressaOrg. These projects were chosen because they matched the same
projects used by Casalanuovo et al. in their
[Assert Use in GitHub Projects](http://web.cs.ucdavis.edu/~filkov/papers/assert-main.pdf) paper (with the exception of the
Xen repository, which we chose simply because we have some previous experience looking at assertions in Xen).

Complete repo-specific results appear here in .csv files, and in a truncated form as a graph in the .png files.
They are named according to *repo_analysis*.[csv|png]. For analyses that involved assertion-events (that is, either
an addition, removal, or change of an assertion) there are columns specific to adding, removing, and also a combination of
the two.

These are the analyses currently represented:
* **activity**: the number of assertion events for each predicate (texutally compared)
* **names**: the number of assertion events for each assertion function (e.g., ASSERT, assert, BUG_ON, LD_ASSERT, ...)
* **distance**: the 'frequency' of assert-event-containing commits in *Commit units*. i.e., The number of commits between assertion-commits
* **time**: the 'frequency' of assert-event-containing commits in *author_time Days*. i.e., the number of days that go by without an assertion-commit. I took the time zones into consideration for this one, and I used author_time (as opposed to commit_time, which changes, for instance, on rebase), but something fishy is going on (or people have their clocks set up wrong), since there are occasional instances of negative time.
