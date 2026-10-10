# Wishlists

A Wishlist REST API project for NYU CSCI-GA.2820-003, DevOps and Agile Methodologies.

We are building a service where customers can create named wishlists and keep track of products they want to buy. A customer can have more than one wishlist.

The project uses Python, Flask, SQLAlchemy, and PostgreSQL. The database models and create-wishlist endpoint are implemented. Other Sprint 1 endpoints are still in progress.

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

The development container installs the Python dependencies and uses `/app` as the project directory. Docker Compose also starts a PostgreSQL container and configures the database connection.

Run the commands below in the development container's terminal.

## Running the Service

```bash
honcho start
```

VS Code is configured to forward port `8080`. Open <http://localhost:8080/> to access the service. If VS Code assigns a different local port, use the address shown in the Ports tab.

The root endpoint currently returns a starter message. Stop the server with `Ctrl+C`.

## Tests and Code Checks

Run the tests and coverage check:

```bash
make test
```

The required coverage is 95%. The command fails if any test fails or coverage is below that threshold.

Run the code checks:

```bash
make lint
```

This runs Flake8 and Pylint. Check their output for errors and warnings.

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

The database generates the wishlist ID. A new wishlist starts with no items. A customer can have multiple wishlists, including wishlists with the same name.

Example request:

```bash
curl -i -X POST http://localhost:8080/wishlists \
  -H 'Content-Type: application/json' \
  -d '{"name": "Birthday", "customer_id": 123}'
```

The expected response is `201 Created`, with a `Location` header pointing to the new wishlist, such as `http://localhost:8080/wishlists/7`. The JSON body includes the generated ID, submitted name and customer ID, and an empty `items` list.

Missing required fields or an invalid name or customer ID return `400 Bad Request`. Requests containing items also return `400`; items must be added separately. A `text/plain` request returns `415 Unsupported Media Type`. Errors are returned as JSON, and invalid requests do not create a wishlist.

## Project Layout

| Path | Contents |
| --- | --- |
| `service/models/` | Wishlist and Item models, shared database methods |
| `service/routes.py` | API routes |
| `service/common/` | Error handlers, logging, and HTTP status constants |
| `tests/test_wishlist.py` and `tests/test_item.py` | Model tests |
| `tests/test_routes.py` | API tests |
| `tests/factories.py` | Test data factories |
| `.devcontainer/` | Development container and PostgreSQL configuration |
| `Pipfile` and `Pipfile.lock` | Python dependencies |
| `Makefile` | Development commands |

## License

Based on the NYU DevOps project template by John Rofrano.

Copyright (c) 2016, 2025 John Rofrano. All rights reserved.

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE).
