Feature: One local quality check

  Scenario: A clean project passes
    Given the project "test-cases/projects/clean/input"
    When I run the quality check
    Then the result is "PASS" and the exit code 0
    And "docs/qualitycheck/" holds "report.md", "history.csv", "coverage.xml", "htmlcov/" and "bandit.html"
    And the report header gives the tested commit, the date, "PASS" and the last passing commit

  Scenario Outline: Each gate fails the check
    Given the project "test-cases/projects/<case>/input"
    When I run the quality check
    Then the result is "FAIL" and the exit code 1
    And the report names the failed gate "<gate>"

    Examples:
      | case           | gate            |
      | failing-test   | tests           |
      | bug            | bugs            |
      | vulnerability  | vulnerabilities |
      | unmaintainable | maintainability |
      | duplication    | duplication     |
      | complex        | complexity      |
      | low-coverage   | coverage        |

  Scenario: Smells are reported, not gated
    Given the project "test-cases/projects/smell/input"
    When I run the quality check
    Then the result is "PASS" and the exit code 0
    And the report lists the smell

  Scenario: The complexity limit comes from ruff
    Given the project "test-cases/projects/complex/input" with ruff's max-complexity set to 20
    When I run the quality check
    Then the result is "PASS" and the exit code 0

  Scenario: The last passing commit survives a failure
    Given a project whose last check passed
    And a commit that breaks a test
    When I run the quality check
    Then the report header gives "FAIL" and the earlier passing commit with its date
    And "history.csv" has one more row
