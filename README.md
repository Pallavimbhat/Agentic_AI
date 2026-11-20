# Agentic AI – 14 Labs Dynamic Workbench

A Python-based implementation of 14 practical labs exploring agentic AI concepts, covering tool integration, reusable skills, memory, workflow orchestration, parallel execution, research workflows, governance and application development.

The project is structured as a modular workbench, with each lab demonstrating a specific concept through working implementations, input-driven execution and test cases.

---

## Overview

This workbench brings together different aspects of agentic AI development in a single project environment. Each lab builds on a specific concept and demonstrates how it can be implemented using Python and supporting technologies.

The implementations range from basic tool-using agents to multi-stage workflows, engineering analysis and an integrated helpdesk application.

The objective is to understand the underlying architecture, implementation techniques and practical considerations involved in building agent-based systems.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Data Storage | SQLite, JSON |
| API Development | FastAPI, HTTP Requests |
| Data Processing | Regular Expressions, CSV, AST |
| Concurrency | Python Concurrent Futures |
| Workflow Management | Graph-based execution, Dependency Validation |
| Testing | Python Unit Testing |
| Integration | Connector Registry, Tool Registry |
| Application Architecture | Modular and Reusable Components |

## Lab Modules

The workbench consists of 14 independent lab implementations.

| Lab | Module | Key Implementation |
|---|---|---|
| 01 | Agent vs Chatbot | Rule-based request routing and tool invocation |
| 02 | Tool-Using Agent | Calculator, database, file operations and HTTP API |
| 03 | Reusable Skills | Modular skill registration and execution |
| 04 | Agent Memory and Retrieval | Persistent, user-scoped memory using SQLite |
| 05 | Agent Connectors | Connector registry and database/workspace integration |
| 06 | Agent Runtime | Execution lifecycle, tracking and runtime logging |
| 07 | Agentic Node Graph | Dependency-based workflow execution |
| 08 | Parallel Specialist Workers | Concurrent text analysis and result aggregation |
| 09 | Deep Research Agent | Evidence retrieval and structured research generation |
| 10 | Cloud Operations Agent | Log analysis, severity classification and recommendations |
| 11 | Agentic SDLC Factory | Requirement-to-release planning workflow |
| 12 | Safety, Evaluation and Governance | Validation, cost checks, audit logging and human approval |
| 13 | Engineering Agent | Sensor data processing and threshold-based analysis |
| 14 | Capstone Project Studio | Integrated helpdesk workflow with ticket management and audit records |

## Key Implementation Details

### 1. Modular Agent Architecture
Individual lab implementations are organised into separate modules, allowing functionality to be developed, tested and executed independently.

### 2. Tool and Skill Management
Tools and reusable skills are registered and invoked through dedicated registries. This separates capability implementation from request-handling logic.

### 3. Persistent Memory
SQLite-backed storage enables information to be retained and retrieved across interactions, with memory records associated with individual user identifiers.

### 4. Workflow Orchestration
Graph-based execution manages task dependencies and execution order. Validation mechanisms help identify invalid dependencies and cycles.

### 5. Parallel Execution
Specialist workers process different aspects of an input concurrently, and their outputs are combined into a structured response.

### 6. Governance and Monitoring
Validation checks, execution logs, cost constraints, evaluation thresholds and human approval mechanisms provide basic governance over agent operations.

### 7. Integrated Application
The capstone implementation combines FAQ retrieval, ticket creation, ticket lookup, reusable triage logic and audit logging into a single workflow.

## Project Structure

```text
Agentic_AI_14_Labs_Dynamic_Workbench/
│
├── Project_source_code/
│   │
│   ├── lab1/
│   ├── lab2/
│   ├── lab3/
│   ├── lab4/
│   ├── lab5/
│   ├── lab6/
│   ├── lab7/
│   ├── lab8/
│   ├── lab9/
│   ├── lab10/
│   ├── lab11/
│   ├── lab12/
│   ├── lab13/
│   ├── lab14/
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── DEMO_ALL_14_LABS.py
│
└── README.md
```

*Note: The structure above presents the main lab organisation; supporting modules, databases and configuration files are maintained within the project.*

## Installation and Setup

### Prerequisites

- Python 3.10 or later
- pip
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Pallavimbhat/Agentic_AI.git
```

### 2. Navigate to the Source Directory

```bash
cd Agentic_AI/Project_source_code
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment:

**Windows:**
```cmd
venv\Scripts\activate
```

**Linux / macOS:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## Running the Labs

The project includes a central demonstration runner for executing individual lab implementations.

To execute a particular lab:

```bash
python DEMO_ALL_14_LABS.py --lab 1
```

Replace the lab number to execute another module.

For example:

```bash
python DEMO_ALL_14_LABS.py --lab 5
```

```bash
python DEMO_ALL_14_LABS.py --lab 10
```

```bash
python DEMO_ALL_14_LABS.py --lab 14
```

Each lab accepts its respective input and produces an output demonstrating the implemented functionality.

## Testing

The project includes dedicated test modules covering agent functionality, application integration and individual lab implementations.

Tests can be executed using Python's unittest framework where the corresponding test modules are configured for discovery.

Example:

```bash
python -m unittest discover -s tests -v
```

## Implementation Scope

The workbench demonstrates practical agentic AI concepts through Python-based implementations. Some components use rule-based processing, while others demonstrate concurrency, persistence and structured workflow execution.

A few implementation boundaries are important:

- The Lab 5 connector layer is an internal MCP-style abstraction, not a full implementation using the official MCP SDK.
- Lab 8 uses concurrent Python specialist workers rather than autonomous LLM agents.
- Lab 9 performs research using a local evidence corpus and supplied sources; it does not perform live web research.
- Lab 10 analyses logs and recommends corrective actions but does not directly modify cloud infrastructure.
- Lab 11 generates SDLC planning artifacts rather than deploying production software.
- Lab 12 incorporates human approval and governance checks without automatically deploying changes.
- Lab 13 uses illustrative sensor thresholds, which are not certified engineering operating limits.

## Contributors

Developed as an academic project by:

- Rashmi Halkarni
- Pallavi Bhat
- Arya Mane
- Amarnath Kakatikar

**Department of Computer Science Engineering**  
KLE Technological University  
Dr. M. S. Sheshagiri Campus, Belagavi

**Academic Year:** 2026–27

---

*This repository documents the implementation and practical exploration of agentic AI concepts across 14 laboratory modules.*
