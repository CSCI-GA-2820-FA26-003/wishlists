$(function () {

    // Base path of the Wishlists REST API. Sprint 4 moves it under /api,
    // so every call below builds its URL from this one constant.
    const BASE_URL = "/wishlists";

    // ****************************************
    //  U T I L I T Y   F U N C T I O N S
    // ****************************************

    // Updates the form with data from the response
    function update_form_data(res) {
        $("#wishlist_id").val(res.id);
        $("#wishlist_name").val(res.name);
        $("#wishlist_customer_id").val(res.customer_id);
    }

    // Clears all form fields
    function clear_form_data() {
        $("#wishlist_name").val("");
        $("#wishlist_customer_id").val("");
    }

    // Reads the Customer Id field. A whole number is sent as a number, which
    // is what the API expects. Anything else is sent unchanged, so the service
    // rejects it with its own message instead of the page guessing a value.
    function read_customer_id() {
        let text = $("#wishlist_customer_id").val().trim();
        return /^-?\d+$/.test(text) ? parseInt(text, 10) : text;
    }

    // Updates the flash message area
    function flash_message(message) {
        $("#flash_message").empty();
        $("#flash_message").append(message);
    }

    // ****************************************
    // Create a Wishlist
    // ****************************************

    // (added by the Create story)

    // ****************************************
    // Update a Wishlist
    // ****************************************

    $("#update-btn").click(function () {

        let wishlist_id = $("#wishlist_id").val();
        let name = $("#wishlist_name").val();
        let customer_id = read_customer_id();

        // Items are managed through their own endpoints, so only the
        // wishlist's own fields are sent
        let data = {
            "name": name,
            "customer_id": customer_id
        };

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "PUT",
            url: `${BASE_URL}/${wishlist_id}`,
            contentType: "application/json",
            data: JSON.stringify(data)
        })

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Retrieve a Wishlist
    // ****************************************

    $("#retrieve-btn").click(function () {

        let wishlist_id = $("#wishlist_id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `${BASE_URL}/${wishlist_id}`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        // On a 404 the service's own message is shown and the form is left as it was
        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Delete a Wishlist
    // ****************************************

    // (added by the Delete story)

    // ****************************************
    // Clear the form
    // ****************************************

    $("#clear-btn").click(function () {
        $("#wishlist_id").val("");
        $("#flash_message").empty();
        clear_form_data()
    });

    // ****************************************
    // Search for Wishlists
    // ****************************************

    // (added by the List and Query stories)

    // ****************************************
    // Wishlist Items
    // ****************************************

    // (added by the Add Item and Purchase stories)

})
