# Documentation Audit

**Description**: Audit documentation for code example accuracy and objective language. Use when reviewing or validating Sphinx documentation.

## When to Use This Skill

- Reviewing documentation before release
- Validating code examples against implementation
- Ensuring objective, factual documentation language
- Checking for outdated or incorrect examples
- Maintaining documentation quality standards

## Quick Reference

### Audit Types
- **Code Example Validation**: Verify all code examples match actual implementation
- **Subjective Language Detection**: Flag subjective or marketing language
- **API Accuracy**: Ensure documented APIs exist and work as described
- **Import Path Verification**: Validate all import statements are correct

### Common Issues to Check
- Outdated code examples
- Incorrect import paths
- Non-existent APIs or methods
- Subjective adjectives (e.g., "easily", "simply", "powerful")
- Marketing language instead of technical documentation
- Missing error handling in examples

## Resource Guides

### 📖 [Code Example Validation](resources/code-validation.md)
Comprehensive guide for validating code examples against actual implementation.

**Use when**: Checking if documentation code examples are accurate and working.

### 📖 [Subjective Language Detection](resources/subjective-language.md)
Guide for identifying and removing subjective or marketing language from documentation.

**Use when**: Reviewing documentation for objective, factual language.

### 📖 [Common Documentation Issues](resources/common-issues.md)
Common documentation problems specific to da_vinci framework.

**Use when**: Performing a comprehensive documentation audit.

## Audit Process

### Phase 1: Code Example Validation

1. **Extract all code examples** from documentation files
   - Look for `.. code-block:: python` in RST files
   - Identify complete examples vs. snippets

2. **Validate imports** against actual package structure
   - Check `from da_vinci.core.orm.table_object import ...`
   - Check `from da_vinci.core.orm.client import ...`
   - Check `from da_vinci_cdk.application import ...`
   - Use serena MCP to find actual symbols and validate paths

3. **Verify class definitions and attributes**
   - Check `TableObject` subclass examples
   - Verify attribute names match `TableObjectAttribute` schema
   - Validate `TableObjectAttributeType` values exist
   - Check `partition_key_attribute`, `sort_key_attribute` usage
   - Verify `global_secondary_indexes`, `local_secondary_indexes` structure

4. **Validate API methods**
   - Check `TableClient` methods: `get()`, `put()`, `delete()`, `scan()`, `query()`
   - Verify method signatures and parameters
   - Check `TableScanDefinition` usage
   - Validate Application CDK construct methods

5. **Test example completeness**
   - Ensure examples have all required imports
   - Check that examples can theoretically run
   - Verify no undefined variables or missing context

### Phase 2: Subjective Language Detection

1. **Scan for subjective adjectives/adverbs**
   - "easily", "simply", "just", "obviously", "clearly"
   - "powerful", "elegant", "beautiful", "amazing"
   - "best", "better", "great", "excellent"
   - "effortlessly", "seamlessly", "straightforward"

2. **Check for marketing language**
   - Superlatives without data
   - Emotional appeals
   - Vague benefit claims
   - Comparisons without specifics

3. **Flag ambiguous statements**
   - "This makes things easier" → How? Quantify.
   - "Da Vinci is powerful" → State specific capabilities.
   - "You can quickly build..." → Remove "quickly", state what you can build.

4. **Verify factual accuracy**
   - All claims should be verifiable
   - Features should be demonstrated, not praised
   - Benefits should be concrete and measurable

### Phase 3: Cross-Reference Implementation

1. **Use serena MCP tools to validate**
   - `find_symbol` to locate classes and methods
   - `get_symbols_overview` to check module structure
   - `search_for_pattern` to find usage examples in tests

2. **Check against actual code**
   - Read actual implementation files
   - Compare method signatures
   - Verify default values and parameter types
   - Check for deprecated APIs

3. **Validate against tests**
   - Look at test files for correct usage patterns
   - Ensure documentation matches test expectations
   - Use tests as source of truth for API behavior

## Reporting Format

### Example Report Structure

```markdown
# Documentation Audit Report

## Executive Summary
- Files audited: X
- Code examples validated: Y
- Issues found: Z
- Critical issues: N

## Code Example Issues

### File: docs/quickstart.rst

#### Issue 1: Incorrect Import Path (Line 26)
**Severity**: Critical
**Current**: `from da_vinci.core.orm.table_object import TableObject`
**Issue**: Import path is correct
**Action**: Verified - No issue

#### Issue 2: Missing Parameter (Line 84)
**Severity**: High
**Current**: `self.table_client.put(user)`
**Issue**: Method signature verified, usage is correct
**Action**: Verified - No issue

## Subjective Language Issues

### File: docs/overview.rst

#### Issue 1: Subjective Adverb (Line 45)
**Severity**: Medium
**Current**: "You can easily create DynamoDB tables..."
**Suggested**: "You can create DynamoDB tables..."
**Reason**: "Easily" is subjective and adds no technical value

#### Issue 2: Marketing Language (Line 102)
**Severity**: Low
**Current**: "Da Vinci provides a powerful abstraction..."
**Suggested**: "Da Vinci provides an abstraction..."
**Reason**: "Powerful" is subjective; let capabilities speak for themselves

## Recommendations

1. Update import examples in quickstart.rst
2. Remove subjective language from overview.rst
3. Add missing error handling examples in tables.rst
4. Verify all CDK examples against latest cdk package
```

## Key Principles

1. **Implementation is Source of Truth**: Always validate against actual code, not assumptions
2. **Use MCP Tools**: Leverage serena for symbol lookup and code navigation
3. **Objective Language Only**: Documentation should be factual and demonstrative
4. **Complete Examples**: Code examples should be runnable or clearly marked as snippets
5. **Version-Aware**: Check documentation matches current version of framework
6. **Test-Driven Validation**: Use test files as examples of correct usage

## Automation Opportunities

- Create scripts to extract and validate code examples
- Build linter for subjective language patterns
- Integrate with CI to catch documentation issues early
- Use AST parsing to validate Python code examples
