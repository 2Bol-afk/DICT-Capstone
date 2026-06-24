# Task 2: Add Farmer CRUD and Farm-Farmer Assignment Endpoints

## Status
DONE

## Changes Made

### 1. Added Pydantic Models (main.py, lines 235-240)
- `FarmerIn`: model for creating/updating farmers with `name` field
- `FarmAssignIn`: model for assigning farms to farmers with optional `farmer_id`

### 2. Added 6 New API Endpoints (main.py, lines 356-409)

1. **GET /farmers** - List all farmers with farm counts
2. **POST /farmers** - Create a new farmer with name validation
3. **PUT /farmers/{farmer_id}** - Update farmer name with validation
4. **DELETE /farmers/{farmer_id}** - Delete farmer and unlink farms
5. **GET /farmers/by-name/{name}** - Get farmer with all associated farms
6. **PUT /farms/{farm_id}/farmer** - Assign/unassign farm to/from farmer

### 3. Implementation Details
- All endpoints use the db.py functions added in Task 1
- Proper HTTP status codes: 200 for success, 404 for not found, 409 for conflict
- Farmer names must be unique (enforced at create and update)
- Farm assignment supports null farmer_id to unassign
- Farmer by-name endpoint returns enriched farmer object with polygon-parsed farms and latest sensor data

## Verification
- main.py imports cleanly without errors
- Code follows existing patterns in the file
- All 6 endpoints placed before app.mount() as required
- Consistent with existing error handling and response patterns

## Commit
```
747c05f feat: add farmer CRUD endpoints and farm-farmer assignment
```

## Test Plan
The endpoints are ready for functional testing:
- Create farmer endpoint validates name uniqueness
- Update/delete endpoints check farmer existence
- Farm assignment validates both farm and farmer existence
- Error responses follow HTTP standards (409 for conflicts, 404 for missing)
