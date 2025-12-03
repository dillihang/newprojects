from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)


items_dict = {1: "apple", 2: "banana", 3: "strawberry", 4: "cranberry"}

@app.route("/status")
def status():
    
    timestamp = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    return jsonify({"status": "ok", "timestamp": timestamp}), 200


@app.route("/items", methods=["GET", "POST", "DELETE"])
def handle_items():
   
    if request.method == "GET":
        return jsonify(items_dict), 200

  
    client_data = request.get_json(silent=True)
    if not client_data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

   
    if request.method == "POST":
        if "id" not in client_data or "name" not in client_data:
            return jsonify({"error": "JSON must include 'id' and 'name'"}), 400
        
        item_id = client_data["id"]
        item_name = client_data["name"]

        items_dict[item_id] = item_name
        return jsonify({"message": "Item created", "data": client_data}), 201

    
    if request.method == "DELETE":
        if "id" not in client_data:
            return jsonify({"error": "JSON must include 'id'"}), 400

        item_id = client_data["id"]

        if item_id not in items_dict:
            return jsonify({"error": "Item not found"}), 404

        removed_item = items_dict.pop(item_id)
        return jsonify({"message": "Item deleted", "removed": removed_item}), 200


@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    
    if item_id in items_dict:
        return jsonify({"id": item_id, "name": items_dict[item_id]}), 200
    else:
        return jsonify({"error": "Item not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)
