Feature: Link check

  Scenario: A broken link fails the check
    Given a clean project whose README links to a missing page
    When I run the quality check
    Then the result is "FAIL" and the report names the failed gate "links"

  Scenario: Ignored links are skipped
    Given a clean project whose README links to a missing page listed in ".lycheeignore"
    When I run the quality check
    Then the result is "PASS"

  Scenario: Without the network, the link check only warns
    Given a clean project whose README links to a missing page
    And no network, with lychee not downloaded yet
    When I run the quality check
    Then the result is "PASS" and the report warns that links were not checked
