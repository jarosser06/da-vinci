REST API Backend
================

This example demonstrates building a REST API backend using Da Vinci with AWS Lambda and API Gateway.

Overview
--------

We'll create a REST API for a product catalog with endpoints for:

- ``GET /products`` - List all products
- ``GET /products/{id}`` - Get product by ID
- ``POST /products`` - Create new product
- ``PUT /products/{id}`` - Update product
- ``DELETE /products/{id}`` - Delete product

Table Definition
----------------

.. code-block:: python

   from da_vinci.core.orm.table_object import (
       TableObject,
       TableObjectAttribute,
       TableObjectAttributeType,
   )

   class ProductTable(TableObject):
       table_name = "products"
       partition_key_attribute = "product_id"

       global_secondary_indexes = [
           {
               "index_name": "category_index",
               "partition_key": "category",
               "sort_key": "name",
           }
       ]

       attributes = [
           TableObjectAttribute(
               name="product_id",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="name",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="description",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="price",
               attribute_type=TableObjectAttributeType.NUMBER,
           ),
           TableObjectAttribute(
               name="category",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="in_stock",
               attribute_type=TableObjectAttributeType.BOOLEAN,
               default=True,
           ),
       ]

API Handler
-----------

.. code-block:: python

   import json
   import uuid
   from typing import Any
   from da_vinci.core.orm.client import TableClient, TableScanDefinition
   from tables import ProductTable


   class ProductAPI:
       """REST API for product management"""

       def __init__(self):
           self.client = TableClient(ProductTable)

       def handle_get(self, event: dict, context: Any) -> dict:
           """Handle GET requests"""
           product_id = event.get("pathParameters", {}).get("id")

           if product_id:
               # Get single product
               product = self.client.get(product_id)
               if not product:
                   return {
                       "statusCode": 404,
                       "body": json.dumps({"error": "Product not found"})
                   }
               return {
                   "statusCode": 200,
                   "body": json.dumps(product.to_dict(json_compatible=True))
               }
           else:
               # List all products
               category = event.get("queryStringParameters", {}).get("category")

               if category:
                   products = list(self.client.query(
                       index_name="category_index",
                       partition_key_value=category
                   ))
               else:
                   products = list(self.client.scan())

               return {
                   "statusCode": 200,
                   "body": json.dumps({
                       "products": [p.to_dict(json_compatible=True) for p in products]
                   })
               }

       def handle_post(self, event: dict, context: Any) -> dict:
           """Handle POST requests"""
           try:
               body = json.loads(event.get("body", "{}"))
           except json.JSONDecodeError:
               return {
                   "statusCode": 400,
                   "body": json.dumps({"error": "Invalid JSON"})
               }

           # Create product
           product = ProductTable(
               product_id=str(uuid.uuid4()),
               name=body["name"],
               description=body.get("description", ""),
               price=body["price"],
               category=body["category"],
               in_stock=body.get("in_stock", True),
           )

           self.client.put(product)
           return {
               "statusCode": 201,
               "body": json.dumps(product.to_dict(json_compatible=True))
           }

       def handle_put(self, event: dict, context: Any) -> dict:
           """Handle PUT requests"""
           product_id = event["pathParameters"]["id"]

           try:
               body = json.loads(event.get("body", "{}"))
           except json.JSONDecodeError:
               return {
                   "statusCode": 400,
                   "body": json.dumps({"error": "Invalid JSON"})
               }

           product = self.client.get(product_id)
           if not product:
               return {
                   "statusCode": 404,
                   "body": json.dumps({"error": "Product not found"})
               }

           # Update fields
           if "name" in body:
               product.name = body["name"]
           if "description" in body:
               product.description = body["description"]
           if "price" in body:
               product.price = body["price"]
           if "category" in body:
               product.category = body["category"]
           if "in_stock" in body:
               product.in_stock = body["in_stock"]

           self.client.put(product)
           return {
               "statusCode": 200,
               "body": json.dumps(product.to_dict(json_compatible=True))
           }

       def handle_delete(self, event: dict, context: Any) -> dict:
           """Handle DELETE requests"""
           product_id = event["pathParameters"]["id"]

           product = self.client.get(product_id)
           if not product:
               return {
                   "statusCode": 404,
                   "body": json.dumps({"error": "Product not found"})
               }

           self.client.delete(product_id)
           return {
               "statusCode": 204,
               "body": ""
           }


   # Lambda handler
   api = ProductAPI()

   def handler(event: dict, context: Any) -> dict:
       """Lambda function handler"""
       method = event.get("httpMethod", "GET")

       if method == "GET":
           return api.handle_get(event, context)
       elif method == "POST":
           return api.handle_post(event, context)
       elif method == "PUT":
           return api.handle_put(event, context)
       elif method == "DELETE":
           return api.handle_delete(event, context)
       else:
           return {
               "statusCode": 405,
               "body": json.dumps({"error": "Method not allowed"})
           }

Infrastructure
--------------

.. code-block:: python

   from aws_cdk import aws_apigateway as apigw
   from aws_cdk import aws_lambda as lambda_
   from da_vinci_cdk.application import Application
   from da_vinci_cdk.stack import Stack
   from tables import ProductTable


   class ApiStack(Stack):
       def __init__(self, scope, construct_id, **kwargs):
           super().__init__(scope, construct_id, **kwargs)

           # Create Lambda function
           api_function = lambda_.Function(
               self, "ProductAPI",
               runtime=lambda_.Runtime.PYTHON_3_11,
               handler="api.handler",
               code=lambda_.Code.from_asset("./lambda"),
           )

           # Create API Gateway
           api = apigw.RestApi(
               self, "ProductsApi",
               rest_api_name="Products API",
               description="REST API for product catalog"
           )

           # Add Lambda integration
           integration = apigw.LambdaIntegration(api_function)

           # /products endpoint
           products = api.root.add_resource("products")
           products.add_method("GET", integration)
           products.add_method("POST", integration)

           # /products/{id} endpoint
           product = products.add_resource("{id}")
           product.add_method("GET", integration)
           product.add_method("PUT", integration)
           product.add_method("DELETE", integration)


   # Table Stack
   class ProductTableStack(Stack):
       """Stack for Product table"""
       def __init__(self, app_name, deployment_id, scope, stack_name):
           super().__init__(app_name, deployment_id, scope, stack_name)
           self.table = DynamoDBTable.from_orm_table_object(
               table_object=ProductTable, scope=self
           )

   # Application
   app = Application(
       app_name="product-api",
       deployment_id="dev",
       app_entry=abspath(dirname(__file__)),
   )

   app.add_uninitialized_stack(ProductTableStack)
   app.add_uninitialized_stack(ApiStack)

   app.synth()

Usage Example
-------------

.. code-block:: bash

   # Create product
   curl -X POST https://api.example.com/products \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Laptop",
       "description": "15-inch laptop",
       "price": 999.99,
       "category": "electronics"
     }'

   # List all products
   curl https://api.example.com/products

   # Get product by ID
   curl https://api.example.com/products/abc-123

   # Update product
   curl -X PUT https://api.example.com/products/abc-123 \
     -H "Content-Type: application/json" \
     -d '{"price": 899.99}'

   # Delete product
   curl -X DELETE https://api.example.com/products/abc-123

   # List products by category
   curl https://api.example.com/products?category=electronics

Key Concepts
------------

**Lambda Integration**
   Lambda functions handle HTTP requests and return responses with statusCode and body.

**HTTP Methods**
   Route requests based on HTTP method (GET, POST, PUT, DELETE).

**Path Parameters**
   Extract resource IDs from URL paths.

**Query Parameters**
   Use query strings for filtering and pagination.

**Error Handling**
   Return appropriate HTTP status codes (200, 404, 400, etc.).

**JSON Serialization**
   Use ``to_dict(json_compatible=True)`` to convert table objects to JSON-serializable dicts.
