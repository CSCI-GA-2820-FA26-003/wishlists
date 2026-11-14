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

Scenario: Delete a wishlist
    When I visit the "Home Page"
    And I set the "Id" to the id of the "Wedding" wishlist
    And I press the "Retrieve" button
    Then I should see "Wedding" in the "Name" field
    When I copy the "Id" field
    And I press the "Delete" button
    Then I should see the message "Wishlist has been Deleted!"
    When I press the "Clear" button
    And I paste the "Id" field
    And I press the "Retrieve" button
    Then I should see the message "was not found"

Scenario: Deleting a wishlist clears the form
    When I visit the "Home Page"
    And I set the "Id" to the id of the "Wedding" wishlist
    And I press the "Retrieve" button
    Then I should see the message "Success"
    When I press the "Delete" button
    Then I should see the message "Wishlist has been Deleted!"
    And the "Id" field should be empty
    And the "Name" field should be empty
    And the "Customer Id" field should be empty

Scenario: Delete a wishlist that does not exist
    When I visit the "Home Page"
    And I set the "Id" to "0"
    And I set the "Name" to "Old wishlist"
    And I set the "Customer Id" to "3"
    And I press the "Delete" button
    Then I should see the message "Wishlist has been Deleted!"
    And the "Id" field should be empty
    And the "Name" field should be empty
    And the "Customer Id" field should be empty

Scenario: Deleting a wishlist with an invalid id preserves the form
    When I visit the "Home Page"
    And I set the "Id" to "abc"
    And I set the "Name" to "Untouched"
    And I press the "Delete" button
    Then I should see the message "Not Found"
    And I should see "abc" in the "Id" field
    And I should see "Untouched" in the "Name" field

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
