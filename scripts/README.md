# Scripts

This folder contains utility scripts used for development, testing, and repository maintenance.

## Structure

```
scripts/
├── local/  # ignored by .gitignore
├── README.md
└── update_tests.sh
```

### update_tests.sh

This script runs the full test suite for the project using xclingo and stores the outputs as pickle files.

1. Executes a predefined set of .lp test cases
2. Generates corresponding .pickle result files
3. Ensures consistency of outputs across changes
4. Optionally enables tracing for selected tests

**Usage**

Run from the repository root:


```bash
bash scripts/update_tests.sh
```
