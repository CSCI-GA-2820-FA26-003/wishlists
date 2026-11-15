Feature: Manage items from the wishlist admin page
    As an eCommerce manager
    I need to add products to a customer's wishlist and mark them as purchased
    So that I can maintain its items from the page

Background:
    Given the following wishlists
        | name      | customer_id |
        | Birthday  | 1           |
        | Christmas | 2           |

Scenario: Add an item using a wishlist ID
    When I visit the "Home Page"
    And I set the "Id" to the id of the "Birthday" wishlist
    And I set the "Item Product Id" to "456"
    And I set the "Item Note" to "red one"
    And I press the "Add Item" button
    Then I should see the message "Success"
    And I should see "456" in the "Item Product Id" field
    And I should see "red one" in the "Item Note" field
    And I should see "false" in the "Item Purchased" field

Scenario: Clear the item fields after adding an item
    When I visit the "Home Page"
    And I set the "Id" to the id of the "Birthday" wishlist
    And I set the "Item Product Id" to "456"
    And I press the "Add Item" button
    Then I should see the message "Success"
    When I press the "Clear" button
    Then the "Item Id" field should be empty
    And the "Item Product Id" field should be empty
    And the "Item Note" field should be empty
    And the "Item Purchased" field should be empty

Scenario: A wishlist ID is required to add an item
    When I visit the "Home Page"
    And I set the "Item Product Id" to "456"
    And I press the "Add Item" button
    Then I should see the message "Enter a wishlist ID"
    And the "Item Id" field should be empty

Scenario Outline: Reject an invalid product ID
    When I visit the "Home Page"
    And I set the "Id" to the id of the "Birthday" wishlist
    And I set the "Item Product Id" to "<product_id>"
    And I press the "Add Item" button
    Then I should see the message "Product ID must be an integer"
    And the "Item Id" field should be empty

    Examples:
        | product_id |
        | abc        |
        | 1.5        |

Scenario: A product ID is required to add an item
    When I visit the "Home Page"
    And I set the "Id" to the id of the "Birthday" wishlist
    And I press the "Add Item" button
    Then I should see the message "Product ID must be an integer"
    And the "Item Id" field should be empty

Scenario: Keep the input when the wishlist does not exist
    When I visit the "Home Page"
    And I set the "Id" to "0"
    And I set the "Item Product Id" to "456"
    And I set the "Item Note" to "red one"
    And I press the "Add Item" button
    Then I should see the message "was not found"
    And I should see "456" in the "Item Product Id" field
    And I should see "red one" in the "Item Note" field
    And the "Item Id" field should be empty

Scenario: Add an item to a wishlist
    When I visit the "Home Page"
    And I set the "Id" to the id of the "Birthday" wishlist
    And I press the "Retrieve" button
    Then I should see the message "Success"
    When I set the "Item Product Id" to "456"
    And I set the "Item Note" to "red one"
    And I press the "Add Item" button
    Then I should see the message "Success"
    And I should see "456" in the "Item Product Id" field
    And I should see "false" in the "Item Purchased" field
    When I press the "Clear" button
    And I set the "Id" to the id of the "Birthday" wishlist
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "456" in the "Item Product Id" field
    And I should see "red one" in the "Item Note" field
    And I should see "false" in the "Item Purchased" field

Scenario: Retrieve the first item and clear it for an empty wishlist
    Given the following items
        | wishlist | product_id | note    |
        | Birthday | 456        | red one |
        | Birthday | 789        | blue    |
    When I visit the "Home Page"
    And I set the "Id" to the id of the "Birthday" wishlist
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "456" in the "Item Product Id" field
    And I should see "false" in the "Item Purchased" field
    When I set the "Id" to the id of the "Christmas" wishlist
    And I press the "Retrieve" button
    Then I should see "Christmas" in the "Name" field
    And the "Item Id" field should be empty
    And the "Item Product Id" field should be empty
    And the "Item Note" field should be empty
    And the "Item Purchased" field should be empty

Scenario: Mark a wishlist item as purchased
    Given the following items
        | wishlist | product_id | note    |
        | Birthday | 456        | red one |
    When I visit the "Home Page"
    And I set the "Id" to the id of the "Birthday" wishlist
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "456" in the "Item Product Id" field
    And I should see "false" in the "Item Purchased" field
    When I press the "Purchase" button
    Then I should see the message "Success"
    And I should see "true" in the "Item Purchased" field
    When I copy the "Id" field
    And I press the "Clear" button
    Then the "Item Purchased" field should be empty
    When I paste the "Id" field
    And I press the "Retrieve" button
    Then I should see "456" in the "Item Product Id" field
    And I should see "true" in the "Item Purchased" field

Scenario: An item cannot be purchased through another wishlist
    Given the following items
        | wishlist | product_id | note    |
        | Birthday | 456        | red one |
    When I visit the "Home Page"
    And I set the "Id" to the id of the "Birthday" wishlist
    And I press the "Retrieve" button
    Then I should see "false" in the "Item Purchased" field
    When I set the "Id" to the id of the "Christmas" wishlist
    And I press the "Purchase" button
    Then I should see the message "was not found in this wishlist"
    When I press the "Clear" button
    And I set the "Id" to the id of the "Birthday" wishlist
    And I press the "Retrieve" button
    Then I should see "false" in the "Item Purchased" field
