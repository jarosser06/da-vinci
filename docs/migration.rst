Migration Guide
===============

This guide helps you migrate between major versions of Da Vinci.

Version 3.0.0
-------------

**Release Date:** 2024-11-20

Breaking Changes
~~~~~~~~~~~~~~~~

Version 3.0 includes several breaking changes. Review this section carefully before upgrading.

**Installation Changes**

Private PyPI repository required:

.. code-block:: bash

   # Old (v2.x)
   pip install da-vinci da-vinci-cdk

   # New (v3.x)
   pip install --extra-index-url https://packages.davinciproject.dev/simple/ da-vinci da-vinci-cdk

**API Changes**

Refer to the CHANGELOG.md for a complete list of API changes.

Migration Steps
~~~~~~~~~~~~~~~

1. **Update Dependencies**

   Update your ``pyproject.toml`` or ``requirements.txt``:

   .. code-block:: toml

      [tool.uv]
      index-url = "https://pypi.org/simple"

      [[tool.uv.index]]
      name = "davinciproject"
      url = "https://packages.davinciproject.dev/simple/"

2. **Review Code**

   Check your code for usage of deprecated APIs.

3. **Test Thoroughly**

   Run your test suite to catch any breaking changes.

4. **Deploy Incrementally**

   Deploy to a test environment first, then staging, then production.

Version 2.0.0
-------------

Migrating from 1.x to 2.0.

**Breaking Changes**

- Updated Python version requirements
- Changes to table object API
- CDK construct refactoring

See CHANGELOG.md for complete details.

General Migration Tips
----------------------

**Pin Your Versions**

Always pin to specific MAJOR.MINOR versions:

.. code-block:: bash

   da-vinci==3.0.*
   da-vinci-cdk==3.0.*

**Test in Stages**

1. Update dependencies in a branch
2. Run tests locally
3. Deploy to development environment
4. Verify functionality
5. Deploy to staging
6. Deploy to production

**Use Semantic Versioning**

- PATCH updates (3.0.1 → 3.0.2): Safe to update
- MINOR updates (3.0.0 → 3.1.0): Safe, new features added
- MAJOR updates (2.0.0 → 3.0.0): Review carefully, breaking changes

Getting Help
------------

If you encounter issues during migration:

- Check the `CHANGELOG.md` for detailed changes
- Review the GitHub issues for known problems
- Open a new issue if you find a bug
