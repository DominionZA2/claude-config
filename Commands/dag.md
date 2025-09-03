# DAG Command

## Description
The DAG command instructs the LLM to open a DAG (Directed Acyclic Graph) file reference and execute the steps defined within it in the correct order based on dependencies.

## Usage
```
/dag <dag_file_path> [options]
```

## Parameters
- `<dag_file_path>`: Path to the DAG definition file (required)
- `[options]`: Optional parameters for execution control

## Options
- `--dry-run`: Show execution plan without running steps
- `--step <step_name>`: Execute only a specific step and its dependencies
- `--parallel`: Enable parallel execution of independent steps
- `--continue-on-error`: Continue execution even if a step fails
- `--verbose`: Show detailed execution logs

## DAG File Format
The DAG file should be in JSON or YAML format with the following structure:

### JSON Format
```json
{
  "name": "DAG Name",
  "description": "Description of the DAG",
  "steps": {
    "step1": {
      "description": "First step description",
      "command": "echo 'Step 1'",
      "dependencies": []
    },
    "step2": {
      "description": "Second step description", 
      "command": "echo 'Step 2'",
      "dependencies": ["step1"]
    },
    "step3": {
      "description": "Third step description",
      "command": "echo 'Step 3'",
      "dependencies": ["step1"]
    },
    "step4": {
      "description": "Final step",
      "command": "echo 'Step 4'", 
      "dependencies": ["step2", "step3"]
    }
  }
}
```

### YAML Format
```yaml
name: DAG Name
description: Description of the DAG
steps:
  step1:
    description: First step description
    command: echo 'Step 1'
    dependencies: []
  step2:
    description: Second step description
    command: echo 'Step 2' 
    dependencies:
      - step1
  step3:
    description: Third step description
    command: echo 'Step 3'
    dependencies:
      - step1
  step4:
    description: Final step
    command: echo 'Step 4'
    dependencies:
      - step2
      - step3
```

## Step Properties
Each step can have the following properties:
- `description`: Human-readable description of the step
- `command`: Command to execute (shell command, script path, or function call)
- `dependencies`: Array of step names that must complete before this step
- `timeout`: Maximum execution time in seconds (optional)
- `retry_count`: Number of retry attempts on failure (optional, default: 0)
- `working_directory`: Directory to execute the command in (optional)
- `environment`: Environment variables for the step (optional)
- `condition`: Boolean expression to determine if step should run (optional)

## Execution Logic

### 1. Parse DAG File
- Read and validate the DAG file format
- Check for circular dependencies
- Validate that all dependencies exist

### 2. Build Execution Plan
- Perform topological sort to determine execution order
- Identify steps that can run in parallel
- Calculate critical path

### 3. Execute Steps
- Execute steps in dependency order
- For parallel execution, run independent steps concurrently
- Track step status (pending, running, completed, failed)
- Log execution progress and results

### 4. Handle Errors
- On step failure, determine which dependent steps should be skipped
- Support retry logic for failed steps
- Provide detailed error reporting

## Command Implementation

When the DAG command is invoked, the LLM should:

1. **Validate Input**
   - Check if DAG file exists and is readable
   - Validate DAG structure and syntax
   - Verify all referenced dependencies exist

2. **Analyze Dependencies**
   - Build dependency graph
   - Check for circular dependencies
   - Determine execution order using topological sorting

3. **Create Execution Plan**
   - Generate step execution sequence
   - Identify parallelizable steps
   - Estimate execution time

4. **Execute Steps**
   - Run each step according to the plan
   - Monitor execution status
   - Handle failures according to error policy
   - Log progress and results

5. **Report Results**
   - Provide execution summary
   - Report any failures or warnings
   - Show execution time and statistics

## Example Usage

```bash
# Execute a DAG file
/dag ./build_pipeline.json

# Dry run to see execution plan
/dag ./deploy.yaml --dry-run

# Execute only a specific step and its dependencies
/dag ./test_suite.json --step integration_tests

# Run with parallel execution enabled
/dag ./data_pipeline.yaml --parallel --verbose

# Continue execution even on failures
/dag ./cleanup.json --continue-on-error
```

## Error Handling
- **File Not Found**: Report missing DAG file with clear error message
- **Invalid Format**: Show syntax errors with line numbers
- **Circular Dependencies**: Identify and report dependency cycles
- **Missing Dependencies**: List undefined step dependencies
- **Execution Failures**: Report failed steps with error details and suggested fixes

## Integration with Other Commands
The DAG command should integrate well with other commands in the system:
- Use existing logging and reporting mechanisms
- Support standard output formats
- Respect global configuration settings
- Allow embedding of other commands as DAG steps