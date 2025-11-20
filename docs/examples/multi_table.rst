Multi-Table Relationships
==========================

This example demonstrates working with multiple related tables in Da Vinci.

Overview
--------

We'll build a blog system with:

- Users table
- Posts table (belongs to user)
- Comments table (belongs to post)
- Relationships between tables

Table Definitions
-----------------

.. code-block:: python

   from da_vinci.core.orm.table_object import (
       TableObject,
       TableObjectAttribute,
       TableObjectAttributeType,
   )

   class UserTable(TableObject):
       table_name = "users"
       partition_key_attribute = "user_id"

       attributes = [
           TableObjectAttribute(
               name="user_id",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="username",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="email",
               attribute_type=TableObjectAttributeType.STRING,
           ),
       ]

   class PostTable(TableObject):
       table_name = "posts"
       partition_key_attribute = "post_id"

       global_secondary_indexes = [
           {
               "index_name": "user_posts_index",
               "partition_key": "user_id",
               "sort_key": "created_at",
           }
       ]

       attributes = [
           TableObjectAttribute(
               name="post_id",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="user_id",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="title",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="content",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="created_at",
               attribute_type=TableObjectAttributeType.DATETIME,
           ),
       ]

   class CommentTable(TableObject):
       table_name = "comments"
       partition_key_attribute = "comment_id"

       global_secondary_indexes = [
           {
               "index_name": "post_comments_index",
               "partition_key": "post_id",
               "sort_key": "created_at",
           }
       ]

       attributes = [
           TableObjectAttribute(
               name="comment_id",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="post_id",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="user_id",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="content",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="created_at",
               attribute_type=TableObjectAttributeType.DATETIME,
           ),
       ]

Service Implementation
----------------------

.. code-block:: python

   import uuid
   from datetime import UTC, datetime
   from da_vinci.core.orm.client import TableClient
   from tables import UserTable, PostTable, CommentTable


   class BlogService:
       def __init__(self):
           self.user_client = TableClient(UserTable)
           self.post_client = TableClient(PostTable)
           self.comment_client = TableClient(CommentTable)

       def create_post(self, user_id: str, title: str, content: str):
           """Create a new post"""
           post = PostTable(
               post_id=str(uuid.uuid4()),
               user_id=user_id,
               title=title,
               content=content,
               created_at=datetime.now(UTC),
           )
           self.post_client.put(post)
           return post

       def get_user_posts(self, user_id: str):
           """Get all posts by a user"""
           return list(self.post_client.query(
               index_name="user_posts_index",
               partition_key_value=user_id
           ))

       def add_comment(self, post_id: str, user_id: str, content: str):
           """Add a comment to a post"""
           comment = CommentTable(
               comment_id=str(uuid.uuid4()),
               post_id=post_id,
               user_id=user_id,
               content=content,
               created_at=datetime.now(UTC),
           )
           self.comment_client.put(comment)
           return comment

       def get_post_comments(self, post_id: str):
           """Get all comments for a post"""
           return list(self.comment_client.query(
               index_name="post_comments_index",
               partition_key_value=post_id
           ))

       def get_post_with_details(self, post_id: str):
           """Get post with author and comments"""
           post = self.post_client.get(post_id)
           author = self.user_client.get(post.user_id)
           comments = self.get_post_comments(post_id)

           return {
               "post": post,
               "author": author,
               "comments": comments,
           }

Usage Example
-------------

.. code-block:: python

   service = BlogService()

   # Create a user
   user = service.user_client.put(UserTable(
       user_id="user-1",
       username="alice",
       email="alice@example.com"
   ))

   # Create posts
   post1 = service.create_post(
       user_id=user.user_id,
       title="My First Post",
       content="Hello, world!"
   )

   post2 = service.create_post(
       user_id=user.user_id,
       title="Second Post",
       content="More content here"
   )

   # Add comments
   service.add_comment(
       post_id=post1.post_id,
       user_id=user.user_id,
       content="Great post!"
   )

   # Get user's posts
   user_posts = service.get_user_posts(user.user_id)
   print(f"User has {len(user_posts)} posts")

   # Get post with full details
   details = service.get_post_with_details(post1.post_id)
   print(f"Post: {details['post'].title}")
   print(f"Author: {details['author'].username}")
   print(f"Comments: {len(details['comments'])}")

Key Concepts
------------

**Foreign Keys**
   Use string attributes (``user_id``, ``post_id``) to reference other tables.

**GSI for Relationships**
   Create GSIs with foreign keys as partition keys to query related items.

**Service Aggregation**
   Service layer aggregates data from multiple tables.

**Denormalization**
   Consider duplicating data when read patterns require it.
