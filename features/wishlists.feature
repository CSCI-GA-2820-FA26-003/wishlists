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
