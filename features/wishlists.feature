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

Scenario: Create a wishlist
    When I visit the "Home Page"
    And I set the "Name" to "Graduation"
    And I set the "Customer Id" to "3"
    And I press the "Create" button
    Then I should see the message "Success"
    When I copy the "Id" field
    And I press the "Clear" button
    Then the "Id" field should be empty
    And the "Name" field should be empty
    When I paste the "Id" field
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "Graduation" in the "Name" field
    And I should see "3" in the "Customer Id" field

Scenario: Create a wishlist with an invalid customer id
    When I visit the "Home Page"
    And I set the "Name" to "Graduation"
    And I set the "Customer Id" to "abc"
    And I press the "Create" button
    Then I should see the message "Invalid Wishlist: customer_id must be an integer"
    And the "Id" field should be empty

Scenario: Create a wishlist without a name
    When I visit the "Home Page"
    And I set the "Customer Id" to "3"
    And I press the "Create" button
    Then I should see the message "Invalid Wishlist: name must be a non-empty string"
    And the "Id" field should be empty

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

Scenario: Update a wishlist
    When I visit the "Home Page"
    And I set the "Id" to the id of the "Birthday" wishlist
    And I press the "Retrieve" button
    Then I should see "Birthday" in the "Name" field
    When I change "Name" to "Birthday Party"
    And I press the "Update" button
    Then I should see the message "Success"
    When I copy the "Id" field
    And I press the "Clear" button
    And I paste the "Id" field
    And I press the "Retrieve" button
    Then I should see "Birthday Party" in the "Name" field

Scenario: List all wishlists
    When I visit the "Home Page"
    And I press the "Clear" button
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Birthday" in the results
    And I should see "Christmas" in the results
    And I should see "Wedding" in the results

Scenario: Query wishlists by customer
    When I visit the "Home Page"
    And I set the "Customer Id" to "1"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Birthday" in the results
    And I should see "Christmas" in the results
    And I should not see "Wedding" in the results

Scenario: Query wishlists by name
    When I visit the "Home Page"
    And I set the "Name" to "Wedding"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Wedding" in the results
    And I should not see "Birthday" in the results
    And I should not see "Christmas" in the results

Scenario: Query a customer who has no wishlists
    When I visit the "Home Page"
    And I set the "Customer Id" to "999"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should not see "Birthday" in the results
    And I should not see "Christmas" in the results
    And I should not see "Wedding" in the results
