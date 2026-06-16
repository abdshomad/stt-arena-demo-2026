# Issue 004: Playwright Dropdown Select Option Mismatch

## Symptoms
The automated Playwright UI test suite timed out and crashed at step 3 while attempting to choose candidate models in the Comparative Arena tab.
```
playwright._impl._errors.TimeoutError: Locator.select_option: Timeout 30000ms exceeded.
Call log:
  - waiting for locator("select").nth(1)
  - attempting select option action
    - did not find some options
```

## Root Cause
The test script attempted to choose the second fighter model in the dropdown list using `value="whisper-cpp"`. However, the candidate models metadata defined the model ID as `whisper.cpp`. The HTML `<select>` element rendered options mapping their values directly from the model ID, making `whisper.cpp` the actual option value. Playwright timed out because it was searching for a non-existent option value `whisper-cpp`.

## Resolution
Modified the Playwright test script at `scratch/run_ui_tests.py` to use `value="whisper.cpp"` instead of `value="whisper-cpp"`, matching the correct option value defined in the candidate models.
