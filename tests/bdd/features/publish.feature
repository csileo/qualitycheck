Feature: Each check published without growing the repository

  Scenario: The result is published on its own branch
    Given a clean project with a remote
    When I run the quality check
    Then the branch "qualitycheck-report" holds one commit, "chore: record qualitycheck report", without parent
    And it holds "report.md", "history.csv", "coverage.xml", "htmlcov/" and "bandit.html"
    And the remote "qualitycheck-report" is that commit
    And the checked branch is unchanged

  Scenario: The history continues, the branch keeps one commit
    Given a clean project with a remote, checked twice
    When I run the quality check
    Then the branch "qualitycheck-report" holds one commit
    And its "history.csv" has 3 rows

  Scenario: The history continues from the remote
    Given a clean project whose remote "qualitycheck-report" holds 2 rows, unknown locally
    When I run the quality check
    Then its "history.csv" has 3 rows

  Scenario Outline: A dirty tree is refused
    Given a clean project with <change>
    When I run the quality check
    Then it refuses to run, naming the uncommitted changes
    And no file changed

    Examples:
      | change            |
      | a modified file   |
      | an untracked file |

  Scenario: The outputs must be ignored by git
    Given a clean project that does not ignore "docs/qualitycheck-report/"
    When I run the quality check
    Then it refuses to run, saying to add "docs/qualitycheck-report/" to ".gitignore"

  Scenario: Offline, the push only warns
    Given a clean project whose remote cannot be reached
    When I run the quality check
    Then the result is "PASS" and the exit code 0
    And a warning says the result was not pushed
    And the local branch "qualitycheck-report" holds the result
