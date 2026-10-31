Feature: Reminder before a push

  Scenario Outline: The reminder warns and never blocks
    Given a project <state>
    When I run the quality check status
    Then it <outcome>
    And the exit code is 0

    Examples:
      | state                                  | outcome                                |
      | never checked                          | warns that no check exists             |
      | whose last check failed                | warns that the last check failed       |
      | checked 21 commits ago                 | warns that the check is 21 commits old |
      | checked 8 days ago                     | warns that the check is 8 days old     |
      | checked 3 commits ago, 2 days ago      | prints nothing                         |
      | checked, followed by its record commit | prints nothing                         |

  Scenario: Limits from the project settings
    Given a project checked 6 commits ago with "max_commits = 5" in "[tool.qualitycheck]"
    When I run the quality check status
    Then it warns that the check is 6 commits old

  Scenario: Unknown settings are rejected
    Given a project with "max_comits = 5" in "[tool.qualitycheck]"
    When I run the quality check status
    Then it fails naming "max_commits" and "max_days"
