# Playwright test selecting source type filter timeout

## Symptoms
Playwright test script timed out after 30000ms waiting for the selector `span:has-text("Engine:")` or `select:has-text("All Source Types")`.

## Root Cause
Upon initial load, the application defaults to the **GPU Cluster** tab. The filters select element only exists when the **Leaderboard** tab is selected and rendered in the DOM. Therefore, trying to locate and select an option from the filter element failed because it was not present.

## Resolution
Modified the test script to programmatically click on the `Leaderboard` button tab, wait for the transition (1000ms), and then locate the filter dropdown using:
```javascript
const sourceSelect = page.locator('span:has-text("Engine:")').locator('xpath=..').locator('select').first();
```
This successfully finds the select option and completes the test.
