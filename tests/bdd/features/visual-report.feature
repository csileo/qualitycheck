Feature: A report readable at a glance, as on Sonar

  Scenario: The report opens on the dashboard
    Given the project "test-cases/projects/clean/input"
    When I run the quality check
    Then "report.md" shows, right after its header, the images "quality-gate", "reliability", "security", "maintainability", "coverage", "duplications", "security-hotspots" and "activity"
    And each of them is in "docs/qualitycheck-report/images/" and has an alternative text
    And the "quality-gate" image says "Passed"

  Scenario: A failed gate fails the Quality Gate and names its condition
    Given the project "test-cases/projects/vulnerability/input"
    When I run the quality check
    Then the "quality-gate" image says "Failed" and names "vulnerabilities"
    And the "security" image shows the rating "C" and a "Failed" badge

  Scenario: Each tile leads to its findings
    Given the project "test-cases/projects/clean/input"
    When I run the quality check
    Then each tile of "report.md" links to a section of "report.md"

  Scenario: The images are published with the report
    Given a clean project with a remote
    When I run the quality check
    Then the branch "qualitycheck-report" holds "images/"
    And every image "report.md" links is on that branch

  Scenario: The activity follows the history
    Given a clean project with a remote, checked twice
    When I run the quality check
    Then the "activity" image draws 3 checks

  Scenario Outline: Reliability is rated by its worst bug
    Given bugs of the ruff families "<families>"
    When the report is drawn
    Then the reliability rating is "<rating>"

    Examples:
      | families | rating |
      |          | A      |
      | B        | C      |
      | F        | D      |
      | B, PLE   | D      |

  Scenario Outline: Security is rated by its worst vulnerability
    Given vulnerabilities of severity and confidence "<findings>"
    When the report is drawn
    Then the security rating is "<rating>" and the security hotspots are <hotspots>

    Examples:
      | findings                 | rating | hotspots |
      |                          | A      | 0        |
      | LOW/HIGH                 | A      | 1        |
      | MEDIUM/HIGH              | C      | 0        |
      | HIGH/MEDIUM, MEDIUM/HIGH | D      | 0        |
      | HIGH/HIGH                | E      | 0        |

  Scenario Outline: Maintainability is rated by the technical debt ratio
    Given <smells> smells in <lines> lines of code
    When the report is drawn
    Then the debt ratio is "<ratio>" and the maintainability rating "<rating>"

    Examples:
      | smells | lines | ratio | rating |
      | 0      | 1000  | 0.0%  | A      |
      | 300    | 1000  | 5.0%  | A      |
      | 360    | 1000  | 6.0%  | B      |
      | 1200   | 1000  | 20.0% | C      |
      | 3000   | 1000  | 50.0% | D      |
      | 3600   | 1000  | 60.0% | E      |
      | 5      | 0     | n/a   | n/a    |

  Scenario Outline: Duplications are a percentage of the lines of code
    Given duplicated blocks covering <duplicated> lines in <lines> lines of code
    When the report is drawn
    Then the duplications are "<percent>"

    Examples:
      | duplicated | lines | percent |
      | 0          | 1000  | 0.0%    |
      | 12         | 1000  | 1.2%    |
      | 1500       | 1000  | 100.0%  |
      | 0          | 0     | n/a     |

  Scenario: A missing tool shows its tile as n/a
    Given measures where bandit is missing
    When the report is drawn
    Then the "security" image shows "n/a" without rating
    And the "quality-gate" image names "vulnerabilities" with "bandit is missing"

  Scenario: Without fail_under, coverage has no requirement
    Given measures with a coverage of 76.4% and no fail_under
    When the report is drawn
    Then the "coverage" image shows "76.4%" without "Failed" badge
    And the "activity" image draws no threshold line
