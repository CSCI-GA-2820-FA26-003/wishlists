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
        update_item_data(res.items && res.items.length ? res.items[0] : null);
    }

    function update_item_data(item) {
        $("#wishlist_item_id").val(item ? item.id : "");
        $("#wishlist_item_product_id").val(item ? item.product_id : "");
        $("#wishlist_item_note").val(item ? item.note : "");
        $("#wishlist_item_purchased").val(item ? String(item.purchased) : "");
    }

    // Clears all form fields
    function clear_form_data() {
        $("#wishlist_name").val("");
        $("#wishlist_customer_id").val("");
        update_item_data(null);
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
        $("#flash_message").text(message);
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

    $("#add-item-btn").click(function () {
        const wishlist_id = $("#wishlist_id").val().trim();
        const product_id = $("#wishlist_item_product_id").val().trim();

        if (!/^\d+$/.test(wishlist_id) || !Number.isSafeInteger(Number(wishlist_id))) {
            flash_message("Enter a wishlist ID before adding an item.");
            return;
        }
        if (!/^-?\d+$/.test(product_id) || !Number.isSafeInteger(Number(product_id))) {
            flash_message("Product ID must be an integer.");
            return;
        }

        $("#add-item-btn").prop("disabled", true);
        flash_message("");
        $.ajax({
            type: "POST",
            url: BASE_URL + "/" + wishlist_id + "/items",
            contentType: "application/json",
            data: JSON.stringify({
                product_id: Number(product_id),
                note: $("#wishlist_item_note").val()
            })
        }).done(function (res) {
            update_item_data(res);
            flash_message("Success");
        }).fail(function (res) {
            const message = res.responseJSON && res.responseJSON.message;
            flash_message(message || "Could not add the item. Please try again.");
        }).always(function () {
            $("#add-item-btn").prop("disabled", false);
        });
    });

    // (Purchase is added by the Purchase story)

})
