# Contributing to DairyGuard

Thank you for helping. Three kinds of contribution help most:

1. **Data.** Growth curves of milk or chilled food under changing temperatures, plate counts, or calorimetry.
   Use the [offer data or lab access](https://github.com/CopyNinja07-07/dairyguard/issues/new?template=offer-data.yml) form.
   Full credit is given in every result that uses your data.
2. **Bug reports.** Use the bug form, with the command you ran and the log file if you can share it.
3. **Code.** Fork, branch, and open a pull request against `main`.

## Before you open a pull request

```bash
pip install -r requirements.txt && pip install --no-deps -e .
make test          # all tests must pass; they also compile the firmware and run the browser kernel
```

- Keep each pull request to one change, and add or update a test for it.
- Every number shown in the book, the white papers, the README or the website is written from result files
  by script. Change the script, not the number.
- Label simulated results as simulation.
- Follow the [rules fixed in advance](ROADMAP.md#rules-fixed-in-advance): data are split by study and batch
  before any result is looked at, and new models are compared with DairyGuard Kinetic on the same unseen data.

## Licence

By contributing you agree that your contribution is released under the [MIT licence](LICENSE).
ComBase records remain subject to the ComBase terms of use.
