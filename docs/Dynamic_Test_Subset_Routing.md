# Assignment 4.3 — Dynamic Test-Subset Routing

**Student:** Adwaith Shri Ram  
**USN:** 24BTRAO001  
**Project:** SmartCI  
**Topic:** Dynamic Test-Subset Routing

## 1. Aim

The aim of this lab is to avoid running every test after every code change. The selector examines the Git diff, identifies changed Python source files, follows the source-code import dependencies, and runs only the pytest files that may be affected.

The safety rule is important: if Git diff cannot be read, no Python source file changed, or no reliable test mapping is found, the selector runs the complete test suite.

## 2. Existing project

The SmartCI application already contains three source modules and their tests:

- `src/pricing.py` and `tests/test_pricing.py`
- `src/cart.py` and `tests/test_cart.py`
- `src/inventory.py` and `tests/test_inventory.py`

The cart module imports pricing functions. Therefore, a change in pricing can affect both pricing and cart behaviour.

## 3. How dynamic test routing works

1. **Extract the Git diff:** compare the current commit with its base commit and list changed files.
2. **Build the test-to-code map:** use Python's Abstract Syntax Tree (AST) to inspect import statements in source and test files.
3. **Apply change-impact analysis:** build reverse dependency links. If cart imports pricing, a pricing change also marks cart as impacted.
4. **Select tests:** choose test files importing any impacted module. If selection is uncertain, run all tests.

This lab implements deterministic Git-diff and static import/dependency analysis. Semantic embeddings and machine-learning-based flaky-test prediction are advanced extensions discussed in the module, not claimed as implemented by this basic selector.

## 4. Implementation

A new file, `scripts/select_tests.py`, performs the selection. It uses Python's built-in `ast`, `pathlib`, `subprocess`, and `os` modules, so no additional package is required.

The script:
- reads changed paths from Git;
- filters changed Python files under `src/`;
- parses imports from source modules and test modules;
- walks reverse dependencies to include indirectly affected modules;
- prints selected test paths to standard output for pytest;
- writes diagnostic messages to standard error;
- falls back to all tests whenever the diff or mapping is uncertain.

## 5. Local verification

Run these commands from the project root after activating the virtual environment:

```powershell
pip install -r requirements.txt
pytest -v
```

To demonstrate the routing after the selector has been committed, make a harmless comment change in `src/pricing.py`, then run:

```powershell
git add src/pricing.py
git commit -m "test: change pricing to verify selector"
python scripts/select_tests.py
```

Expected selected paths:

```text
tests/test_cart.py tests/test_pricing.py
```

The pricing test is selected because it directly imports pricing. The cart test is selected because cart imports pricing, so it is a transitive dependency. The inventory test is not selected because it does not depend on either module.

After recording the demonstration, restore the source file if the comment was only for testing:

```powershell
git reset --soft HEAD~1
git restore src/pricing.py
```

Only use the reset/restore commands for this temporary demonstration commit, after confirming that it is the latest commit and contains no other work you need to keep.

## 6. GitHub Actions integration

The workflow in `.github/workflows/ci.yml` now:
1. checks out the full Git history using `fetch-depth: 0`;
2. installs Python 3.12 and project dependencies;
3. runs `scripts/select_tests.py`;
4. stores its output as the step output named `tests`;
5. passes that list to pytest.

The expression `${{ steps.sel.outputs.tests }}` passes the selected test paths from the selector step to the test step. The workflow uses the pull request base SHA for pull requests and the previous push SHA for normal pushes.

## 7. Expected result

When `src/pricing.py` changes, the selector should choose:

- `tests/test_pricing.py`
- `tests/test_cart.py`

When only documentation changes, or when the Git diff cannot be determined, it should run all tests as a safe fallback.

## 8. Conclusion

Dynamic Test-Subset Routing reduces unnecessary test execution by connecting changed source files to the tests that depend on them. The implementation demonstrates direct and transitive dependency analysis and integrates the selector into GitHub Actions. The full test suite remains the fallback whenever selection cannot be trusted.

## 9. Screenshots to add to the final report

Add your own screenshots after running the workflow:

1. SmartCI project structure showing the new `scripts/select_tests.py`.
2. The selector source code open in VS Code.
3. Terminal output showing `tests/test_cart.py tests/test_pricing.py` after the pricing change.
4. GitHub Actions run showing the “Select affected tests” and “Run selected tests” steps.
5. Successful final GitHub Actions run with all selected tests passing.

Do not insert screenshots until you have captured the actual results from your machine or GitHub Actions.
