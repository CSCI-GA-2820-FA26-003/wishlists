Feature: The wishlist service back-end
    As an eCommerce manager
    I need a RESTful wishlist service with an administration page
    So that I can keep track of my customers' wishlists

Background:
    Given the following wishlists
        | name      | customer_id |
        | Birthday  | 1           |
        | Christmas | 1           |
        | Wedding   | 2           |

Scenario: An administrator opens the wishlist management page
    When I visit the "Home Page"
    Then I should see "Wishlist Admin" in the title
    And I should not see "404 Not Found"

Scenario: Read a wishlist
    When I visit the "Home Page"
    And I set the "Id" to the id of the "Birthday" wishlist
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "Birthday" in the "Name" field
    And I should see "1" in the "Customer Id" field

Scenario: Read a wishlist that does not exist
    When I visit the "Home Page"
    And I set the "Name" to "Untouched"
    And I set the "Id" to "0"
    And I press the "Retrieve" button
    Then I should see the message "was not found"
    And I should see "Untouched" in the "Name" field
