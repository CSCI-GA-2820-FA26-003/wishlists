# Wishlists

Wishlist service for NYU CSCI-GA.2820-003, DevOps and Agile Methodologies. Customers can create named wishlists to keep track of products they want to buy.

Built with Flask, SQLAlchemy, and PostgreSQL.

## Local Setup

You will need Git, Docker Desktop, and VS Code with the Dev Containers extension.

1. Start Docker Desktop.
2. Clone the repository:

   ```bash
   git clone https://github.com/CSCI-GA-2820-FA26-003/wishlists.git
   cd wishlists
   ```

3. Open the `wishlists` folder in VS Code.
4. Open the Command Palette and select **Dev Containers: Reopen in Container**.
5. Wait for the container setup to finish, then open a terminal in VS Code.

The setup installs the Python dependencies and starts PostgreSQL in a separate container. Run the commands below in the development container's terminal, from `/app`.

## Running the Service

```bash
honcho start
```

Open <http://localhost:8080/>. If VS Code forwards a different local port, use the address in the Ports tab. Stop the server with `Ctrl+C`.

## Tests and Code Checks

Run all tests:

```bash
make test
```

Tests must pass with at least 95% coverage. They clear Wishlist and Item records in the configured database, so only run them against a development or test database.

Run the code checks:

```bash
make lint
```

This runs Flake8 and Pylint. Check the output for errors and warnings, even if the command finishes.

## Sprint 1 API

`POST /wishlists` is implemented. The other endpoints below are planned; `/` still returns the starter message.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Return service information as JSON |
| POST | `/wishlists` | Create an empty wishlist |
| GET | `/wishlists` | List wishlists |
| GET | `/wishlists/{id}` | Read a wishlist |
| PUT | `/wishlists/{id}` | Update a wishlist |
| DELETE | `/wishlists/{id}` | Delete a wishlist |

### Create a Wishlist

`POST /wishlists` accepts JSON with these fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | String | Yes | Cannot be empty or contain only whitespace |
| `customer_id` | Integer | Yes | Identifies the customer |

The database generates `id`. New wishlists start empty; omit `items` or send `[]`. A customer can have multiple wishlists with the same name.

Example request:

```bash
curl -i -X POST http://localhost:8080/wishlists \
  -H 'Content-Type: application/json' \
  -d '{"name": "Birthday", "customer_id": 123}'
```

Example response body (the generated ID will vary):

```json
{
  "id": 7,
  "name": "Birthday",
  "customer_id": 123,
  "items": []
}
```

The response status is `201 Created`. The `Location` header points to the new wishlist, for example `http://localhost:8080/wishlists/7`.

- `400 Bad Request`: missing or invalid required fields, or a non-empty `items` list. Adding items is a separate story.
- `415 Unsupported Media Type`: the request is not JSON, for example `Content-Type: text/plain`.

Errors return JSON and do not create a wishlist.

## Project Layout

| Path | Contents |
| --- | --- |
| `service/models/` | Wishlist and Item models |
| `service/routes.py` | API routes |
| `tests/` | Model and API tests, test data factories |
| `.devcontainer/` | Development container and PostgreSQL configuration |
| `Makefile` | Development commands |

## License

Based on the NYU DevOps project template by John Rofrano.

Copyright (c) 2016, 2025 John Rofrano. All rights reserved.

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE).
