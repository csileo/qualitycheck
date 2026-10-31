Feature: Each check recorded in the project's history

  Scenario: The result is committed and pushed
    Given a clean project with a remote
    When I run the quality check
    Then the last commit is "chore: record quality check result" and touches "docs/audit/" only
    And the remote has that commit

  Scenario Outline: A dirty tree is refused
    Given a clean project with <change>
    When I run the quality check
    Then it refuses to run, naming the uncommitted changes
    And no file changed

    Examples:
      | change            |
      | a modified file   |
      | an untracked file |

  Scenario: Offline, the push only warns
    Given a clean project whose remote cannot be reached
    When I run the quality check
    Then the result is "PASS" and the exit code 0
    And a warning says the result was not pushed
    And the record commit is kept locally
