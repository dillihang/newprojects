from flask import Flask, jsonify, request
from datetime import datetime
import uuid
import re

app = Flask(__name__)

inventory_dict = {}

@app.route("/status")
def status():
    """
    Health check endpoint for the API.
    
    Returns:
        JSON: API status and current timestamp
        
    Example:
        GET /status → {"status": "ok", "timestamp": "03/12/2025, 14:30:45"}
    """
    timestamp = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    return jsonify({"status": "ok", "timestamp": timestamp}), 200

@app.route("/inventory")
def inventory():
    """
    Retrieve all inventory items.
    
    Returns:
        JSON: List of all items with their details
        
    Example:
        GET /inventory → [
            {"item_id": "abc123", "item_name": "apple", "location": "A1", "quantity": 10},
            {"item_id": "def456", "item_name": "banana", "location": "B2", "quantity": 5}
        ]
    """
    all_items = []
    for item_id, item_data in inventory_dict.items():
        all_items.append({
            "item_id": item_id,
            "item_name": item_data["item_name"],
            "location": item_data["location"],
            "quantity": item_data["quantity"]
        })
    return jsonify(all_items), 200

@app.route("/inventory", methods=["POST"])
def add_to_inventory():
    """
    Create a new inventory item.
    
    Request Body (JSON):
        - name (str): Item name (1-100 characters, non-empty)
        - location (str): Storage location (format: A1-Z9)
        - quantity (int): Positive integer quantity
        
    Returns:
        JSON: Created item details with generated item_id
        
    Status Codes:
        201: Item created successfully
        400: Invalid input data
        
    Example:
        POST /inventory {"name": "apple", "location": "A1", "quantity": 10}
        → {"item_id": "abc123", "item_name": "apple", "location": "A1", "quantity": 10, "message": "Item created"}
    """
    client_data = request.get_json()

    if not client_data:
        return jsonify({"error": "No JSON data provided"}), 400

    quantity = client_data.get("quantity")
    location = client_data.get("location")  
    name = client_data.get("name")  # Changed from "item_name"

    if not all([quantity, location, name]):
        return jsonify({"error": "quantity, location, and name are required"}), 400

    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"error": "Quantity must be a positive integer"}), 400
    
    if not re.match(r"^[A-Z][0-9]$", location):
        return jsonify({"error": "Invalid location format"}), 400
    
    if not isinstance(name, str):
        return jsonify({"error": "Name must be a string"}), 400
    
    if not name.strip():
        return jsonify({"error": "Name cannot be empty"}), 400
    
    if len(name) > 100:
        return jsonify({"error": "Name too long (max 100 characters)"}), 400

    item_id = str(uuid.uuid4())[:8]

    inventory_dict[item_id] = {
        "item_name": name,
        "quantity": quantity,
        "location": location
    }
    
    return jsonify({
        "item_id": item_id,
        "item_name": name,
        "location": location,
        "quantity": quantity,
        "message": "Item created"
    }), 201

@app.route("/inventory/<string:item_id>", methods=["GET"])
def get_item_byid(item_id):
    """
    Retrieve a specific inventory item by ID.
    
    Path Parameters:
        item_id (str): Unique identifier of the item
        
    Returns:
        JSON: Item details if found
        
    Status Codes:
        200: Item found
        404: Item not found
        
    Example:
        GET /inventory/abc123 → {"item_id": "abc123", "item_name": "apple", "location": "A1", "quantity": 10}
    """
    if item_id in inventory_dict:
        item = inventory_dict[item_id]
        return jsonify({
            "item_id": item_id,
            "item_name": item["item_name"],
            "location": item["location"],
            "quantity": item["quantity"]
        }), 200
    return jsonify({"error": "Item Not Found"}), 404

@app.route("/inventory/<string:item_id>", methods=["DELETE"])
def delete_item(item_id):
    """
    Delete an inventory item by ID.
    
    Path Parameters:
        item_id (str): Unique identifier of the item to delete
        
    Returns:
        JSON: Deletion confirmation and deleted item data
        
    Status Codes:
        200: Item deleted successfully
        404: Item not found
        
    Example:
        DELETE /inventory/abc123 → {"message": "Item deleted", "deleted_item": {...}}
    """
    if item_id in inventory_dict:
        deleted_item = inventory_dict.pop(item_id)
        return jsonify({
            "message": "Item deleted",
            "deleted_item": deleted_item
        }), 200
    return jsonify({"error": "Item not found"}), 404

@app.route("/inventory/search")
def search_inventory():
    """
    Search for inventory items by location.
    
    Query Parameters:
        location (str): Storage location to filter by (required)
        
    Returns:
        JSON: List of items at the specified location
        
    Status Codes:
        200: Search completed (may return empty list)
        400: Missing location parameter
        
    Example:
        GET /inventory/search?location=A1 → [
            {"item_id": "abc123", "item_name": "apple", "quantity": 10},
            {"item_id": "def456", "item_name": "banana", "quantity": 5}
        ]
    """
    search_location = request.args.get("location")
    
    if not search_location:
        return jsonify({"error": "Location parameter required"}), 400
    
    results = []
    for item_id, item_data in inventory_dict.items():
        if item_data["location"] == search_location:
            results.append({
                "item_id": item_id,
                "item_name": item_data["item_name"],
                "quantity": item_data["quantity"]
            })
    
    if results:
        return jsonify(results), 200
    return jsonify({"message": "No items found in this location", "results": []}), 200

@app.route("/inventory/<string:item_id>", methods=["PATCH"])
def update_item(item_id):
    """
    Partially update an inventory item.
    
    Path Parameters:
        item_id (str): Unique identifier of the item to update
        
    Request Body (JSON, partial):
        - name (str, optional): New item name
        - location (str, optional): New storage location (A1-Z9)
        - quantity (int, optional): New positive quantity
        
    Returns:
        JSON: Update confirmation and updated item data
        
    Status Codes:
        200: Item updated successfully
        400: Invalid update data
        404: Item not found
        
    Example:
        PATCH /inventory/abc123 {"quantity": 20}
        → {"message": "Item updated", "updated_item": {...}}
    """
    client_data = request.get_json()
    
    if not client_data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    if item_id not in inventory_dict:
        return jsonify({"error": "Item not found"}), 404
    
    item = inventory_dict[item_id]
    
    # Update location if provided
    if "location" in client_data:
        new_location = client_data["location"]
        if not re.match(r"^[A-Z][0-9]$", new_location):
            return jsonify({"error": "Invalid location format"}), 400
        item["location"] = new_location
    
    # Update quantity if provided
    if "quantity" in client_data:
        new_quantity = client_data["quantity"]
        if not isinstance(new_quantity, int) or new_quantity <= 0:
            return jsonify({"error": "Quantity must be a positive integer"}), 400
        item["quantity"] = new_quantity
    
    # Update name if provided
    if "name" in client_data:
        new_name = client_data["name"]
        if not isinstance(new_name, str):
            return jsonify({"error": "Name must be a string"}), 400
        if not new_name.strip():
            return jsonify({"error": "Name cannot be empty"}), 400
        if len(new_name) > 100:
            return jsonify({"error": "Name too long (max 100 characters)"}), 400
        item["item_name"] = new_name
    
    return jsonify({
        "message": "Item updated",
        "updated_item": item
    }), 200

if __name__ == "__main__":
    app.run(debug=True)