# Subjective Language Detection Guide

Documentation should be objective, factual, and demonstrative. This guide helps identify and remove subjective or marketing language from da_vinci documentation.

## Why Objective Language Matters

**Technical documentation is not marketing**
- Users want facts, not opinions
- Features should speak for themselves
- Claims should be verifiable
- Comparisons should be specific

**Objective language builds trust**
- Users can verify statements
- No exaggeration or overselling
- Clear expectations
- Professional tone

## Categories of Subjective Language

### 1. Subjective Adverbs

These words make claims about ease or quality that vary by user experience.

**Words to Flag**

- easily
- simply
- quickly
- obviously
- clearly
- straightforwardly
- effortlessly
- seamlessly
- trivially

**Examples**

❌ **Bad**: "You can easily create DynamoDB tables with Da Vinci."
✅ **Good**: "You can create DynamoDB tables by defining a TableObject class."

❌ **Bad**: "Simply add a table to your application."
✅ **Good**: "Add a table to your application with `app.add_table(TableObject)`."

❌ **Bad**: "The framework seamlessly integrates with AWS services."
✅ **Good**: "The framework integrates with DynamoDB, EventBridge, and Lambda."

❌ **Bad**: "You can quickly deploy using CDK."
✅ **Good**: "Deploy using `cdk deploy --all`."

### 2. Subjective Adjectives

These words express opinions about quality without objective criteria.

**Words to Flag**

- powerful
- elegant
- beautiful
- amazing
- incredible
- awesome
- excellent
- great
- fantastic
- revolutionary
- cutting-edge

**Examples**

❌ **Bad**: "Da Vinci provides a powerful abstraction over DynamoDB."
✅ **Good**: "Da Vinci provides type-safe Python classes for DynamoDB operations."

❌ **Bad**: "The elegant API makes development a breeze."
✅ **Good**: "The API provides methods for get, put, delete, scan, and query operations."

❌ **Bad**: "An amazing feature of the framework is automatic resource creation."
✅ **Good**: "The framework automatically creates DynamoDB tables from table definitions."

❌ **Bad**: "This revolutionary approach eliminates boilerplate."
✅ **Good**: "This approach generates DynamoDB API calls from table object definitions."

### 3. Comparative Statements Without Context

Comparisons should include specifics about what is being compared.

**Patterns to Flag**

- "better than..."
- "more efficient than..."
- "faster than..."
- "easier than..."
- "superior to..."

**Examples**

❌ **Bad**: "Da Vinci is better than using boto3 directly."
✅ **Good**: "Da Vinci generates boto3 API calls from Python class definitions, reducing the code needed for DynamoDB operations."

❌ **Bad**: "This approach is more efficient."
✅ **Good**: "This approach reduces the number of API calls from 3 to 1."

❌ **Bad**: "Da Vinci makes deployment faster."
✅ **Good**: "Da Vinci generates CDK infrastructure from table definitions, eliminating manual CloudFormation configuration."

### 4. Vague Benefit Claims

Claims should be specific and measurable.

**Patterns to Flag**

- "improves developer experience"
- "makes things easier"
- "simplifies development"
- "reduces complexity"
- "enhances productivity"

**Examples**

❌ **Bad**: "Da Vinci improves developer experience."
✅ **Good**: "Da Vinci provides type hints, autocomplete, and compile-time validation for DynamoDB operations."

❌ **Bad**: "The framework reduces complexity."
✅ **Good**: "The framework eliminates the need to write boto3 DynamoDB API calls for standard operations."

❌ **Bad**: "This simplifies development."
✅ **Good**: "This eliminates 50+ lines of boto3 boilerplate per table."

### 5. Emotional or Excitement Language

Documentation should maintain professional tone.

**Patterns to Flag**

- Exclamation marks (except in command output examples)
- "Wow", "Great!", "Awesome!"
- "You'll love..."
- "This is exciting..."

**Examples**

❌ **Bad**: "Da Vinci is an exciting new framework!"
✅ **Good**: "Da Vinci is a framework for AWS-native Python applications."

❌ **Bad**: "You'll love how easy table definitions are!"
✅ **Good**: "Table definitions use Python classes with type-safe attributes."

❌ **Bad**: "Check out this amazing feature!"
✅ **Good**: "The framework supports automatic index creation from table definitions."

### 6. Superlatives Without Data

Superlatives require supporting evidence.

**Words to Flag**

- best
- fastest
- most
- least
- greatest
- ultimate

**Examples**

❌ **Bad**: "Da Vinci is the best way to build on AWS."
✅ **Good**: "Da Vinci provides Python classes for DynamoDB, EventBridge, and Lambda integration."

❌ **Bad**: "This is the fastest way to deploy."
✅ **Good**: "Deploy with `cdk deploy --all`."

❌ **Bad**: "The most efficient pattern for table access."
✅ **Good**: "Access tables using TableClient with get, put, and query methods."

### 7. Marketing Buzzwords

Avoid marketing language in technical documentation.

**Words to Flag**

- game-changing
- next-generation
- enterprise-grade
- world-class
- state-of-the-art
- best-in-class
- industry-leading

**Examples**

❌ **Bad**: "Da Vinci provides enterprise-grade table management."
✅ **Good**: "Da Vinci provides table definitions with type validation and automatic infrastructure generation."

❌ **Bad**: "A next-generation approach to DynamoDB."
✅ **Good**: "An approach that generates DynamoDB resources from Python classes."

### 8. Assumed User Feelings

Don't assume what users will think or feel.

**Patterns to Flag**

- "you'll find that..."
- "you'll appreciate..."
- "you'll notice..."
- "you'll see that..."

**Examples**

❌ **Bad**: "You'll find that table definitions are intuitive."
✅ **Good**: "Table definitions use Python classes with attributes for each field."

❌ **Bad**: "You'll appreciate the automatic resource creation."
✅ **Good**: "Tables are automatically created in CDK from table definitions."

## Detection Process

### Step 1: Automated Scanning

Use grep or search patterns to find problematic words:

```bash
# Search for subjective adverbs
grep -n "easily\|simply\|quickly\|obviously\|clearly" docs/*.rst

# Search for subjective adjectives
grep -n "powerful\|elegant\|amazing\|incredible" docs/*.rst

# Search for exclamation marks
grep -n "!" docs/*.rst
```

### Step 2: Context Analysis

For each flagged word:

1. **Read the sentence in context**
2. **Determine if it makes a subjective claim**
3. **Check if the claim is verifiable**
4. **Propose objective alternative**

### Step 3: Replacement Guidelines

**Remove the subjective word**
- Often the sentence works without it

**Replace with specific details**
- What exactly does it do?
- What is the measurable outcome?
- What are the concrete benefits?

**Show, don't tell**
- Demonstrate capability with examples
- Let the code speak for itself

## Common Acceptable Uses

### Technical Terms

Some words that seem subjective are actually technical terms:

✅ **Acceptable**: "strongly typed" (technical term)
✅ **Acceptable**: "eventually consistent" (AWS term)
✅ **Acceptable**: "highly available" (when backed by AWS SLA)

### Comparisons with Data

Comparisons are acceptable with specific data:

✅ **Acceptable**: "This reduces API calls from 10 to 2"
✅ **Acceptable**: "This approach uses 50% less code than boto3"
✅ **Acceptable**: "Costs are reduced by eliminating cross-region data transfer"

### User Actions

Instructions can use common phrases:

✅ **Acceptable**: "You can create tables..."
✅ **Acceptable**: "To deploy, run..."
✅ **Acceptable**: "This allows you to..."

## Revision Examples

### Example 1: Overview Section

**Before**
```
Da Vinci is a powerful framework that makes building AWS applications easy.
You'll love how seamlessly it integrates with DynamoDB, providing an elegant
abstraction over boto3. Simply define your tables and Da Vinci handles
everything else automatically.
```

**After**
```
Da Vinci is a framework for building Python applications on AWS. It generates
DynamoDB API calls from Python class definitions and creates infrastructure
from table definitions. Define tables using TableObject classes, and the
framework generates both runtime operations and CDK infrastructure.
```

### Example 2: Feature Description

**Before**
```
The amazing table client provides powerful methods for database operations.
You can easily query, scan, and update records with just a few lines of code.
It's incredibly efficient and makes DynamoDB development a breeze!
```

**After**
```
The TableClient provides methods for DynamoDB operations: get(), put(),
delete(), scan(), and query(). These methods accept table objects and return
typed results, eliminating the need for boto3 dictionary manipulation.
```

### Example 3: Getting Started

**Before**
```
Getting started with Da Vinci is super easy! You'll quickly see how powerful
this framework is. Simply install the packages and you're ready to build
amazing applications in no time.
```

**After**
```
Install da-vinci and da-vinci-cdk packages. Define a TableObject class with
attributes. Create an Application instance and add tables. Deploy with
`cdk deploy --all`.
```

## Audit Checklist

When reviewing documentation, check for:

- [ ] No subjective adverbs (easily, simply, quickly, etc.)
- [ ] No subjective adjectives (powerful, elegant, amazing, etc.)
- [ ] No marketing buzzwords (game-changing, next-generation, etc.)
- [ ] No vague benefit claims
- [ ] No emotional language or exclamation marks
- [ ] No assumptions about user feelings
- [ ] Comparisons include specific data
- [ ] All claims are verifiable
- [ ] Features are demonstrated, not praised
- [ ] Professional, technical tone throughout

## Reporting Format

```markdown
### File: docs/overview.rst

#### Issue: Subjective Adverb (Line 42)
**Severity**: Medium
**Current**: "You can easily create tables with Da Vinci."
**Suggested**: "You can create tables by defining TableObject classes."
**Reason**: "Easily" is subjective and varies by user experience

#### Issue: Subjective Adjective (Line 67)
**Severity**: Medium
**Current**: "Da Vinci provides a powerful abstraction."
**Suggested**: "Da Vinci provides Python classes for DynamoDB operations."
**Reason**: "Powerful" is subjective; state specific capabilities instead
```

## Best Practices

1. **Let code examples speak**: Show capabilities through working examples
2. **State facts**: What does it do, not how great it is
3. **Be specific**: Replace vague claims with measurable outcomes
4. **Stay professional**: Technical documentation, not marketing copy
5. **Verify claims**: Everything should be demonstrable
6. **Use active voice**: Clear, direct statements
7. **Focus on capabilities**: What users can build, not how they'll feel
