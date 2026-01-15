# Alchemist Engine and Reactor Vessel

## Overview

The **Alchemist Engine** and **Reactor Vessel** extend the Neural Nestor Gauge Logic framework with a powerful tensor transformation pipeline inspired by alchemical transmutation. These components provide:

- **Safe, monitored tensor transformations** with validation and constraints
- **Step-by-step execution tracking** with intermediate results
- **Real-time monitoring** with event-driven updates
- **Resource tracking** and performance metrics
- **Transformation history** for analysis and debugging

## Conceptual Framework

### Alchemical Metaphor

The system uses alchemical concepts to make tensor transformations intuitive:

| Alchemical Term | Technical Meaning |
|----------------|-------------------|
| **Transmutation** | Tensor transformation through operations |
| **Elixir** | A recipe of transformation steps |
| **Catalyst** | Activation functions and non-linearities |
| **Crucible** | The computational context |
| **Vessel** | Isolated execution environment |
| **Philosopher's Stone** | Optimal transformation pipeline |

### Architecture

```
┌─────────────────────────────────────────────┐
│           Reactor Vessel                    │
│  ┌───────────────────────────────────────┐  │
│  │     Alchemist Engine                  │  │
│  │  ┌─────────────────────────────────┐  │  │
│  │  │   Elixir (Transformation Recipe)│  │  │
│  │  │                                 │  │  │
│  │  │  Step 1: Custom Function        │  │  │
│  │  │  Step 2: Activation (ReLU)      │  │  │
│  │  │  Step 3: Threshold              │  │  │
│  │  └─────────────────────────────────┘  │  │
│  │                                       │  │
│  │  History │ Validation │ Monitoring   │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  Safety │ Resources │ Events │ Constraints │
└─────────────────────────────────────────────┘
```

## Core Components

### 1. Alchemist Engine

The engine manages tensor transformations through registered elixirs (transformation recipes).

#### Key Features

- **Elixir Registration**: Register reusable transformation pipelines
- **Transformation Execution**: Apply elixirs to transform tensors
- **History Tracking**: Maintain a log of all transformations
- **Intermediate Results**: Capture output at each step
- **Validation**: Verify shapes and data integrity

#### Basic Usage

```typescript
import { AlchemistEngine, createTensor } from './tensor-logic';

// Create engine
const engine = new AlchemistEngine();

// Define an elixir (transformation recipe)
const elixir = {
  id: 'normalize_and_activate',
  name: 'Normalize and Activate',
  description: 'Normalize input then apply sigmoid activation',
  steps: [
    {
      id: 'normalize',
      name: 'Normalize',
      type: 'custom',
      customFn: (tensor) => {
        const max = Math.max(...tensor.data);
        return createTensor(
          'normalized',
          tensor.indices,
          tensor.shape,
          new Float64Array(tensor.data.map(x => x / max))
        );
      },
    },
    {
      id: 'activate',
      name: 'Sigmoid Activation',
      type: 'activation',
      activation: 'sigmoid',
    },
  ],
};

// Register the elixir
engine.registerElixir(elixir);

// Create input tensor
const input = createTensor('input', ['i'], [4], new Float64Array([1, 2, 3, 4]));

// Apply transformation
const result = engine.transmute('normalize_and_activate', { input });

console.log('Output:', result.output.data);
console.log('Steps:', result.intermediates.map(i => i.stepName));
console.log('Execution time:', result.executionTimeMs, 'ms');
```

### 2. Reactor Vessel

The vessel provides a safe, monitored execution environment with resource tracking and safety constraints.

#### Key Features

- **Safety Constraints**: Enforce limits on tensor size, memory, execution time
- **Real-time Monitoring**: Subscribe to events for progress tracking
- **Resource Tracking**: Monitor memory, operations, and performance
- **State Management**: Track execution through well-defined states
- **Error Handling**: Graceful error handling with emergency stop

#### Reactor States

```
IDLE → PREPARING → TRANSMUTING → STABILIZING → COMPLETE
                                              ↓
                                            ERROR
                                              ↓
                                       EMERGENCY_STOP
```

#### Basic Usage

```typescript
import { AlchemistEngine, ReactorVessel } from './tensor-logic';

const engine = new AlchemistEngine();
// ... register elixirs ...

// Create vessel with safety constraints
const vessel = new ReactorVessel(engine, {
  maxTensorSize: 1_000_000,        // Max elements per tensor
  maxExecutionTimeMs: 30_000,      // 30 second timeout
  maxMemoryBytes: 100_000_000,     // 100 MB memory limit
  maxSteps: 50,                    // Max transformation steps
});

// Subscribe to events
vessel.on((event) => {
  if (event.type === 'progress') {
    console.log('Progress:', event.data.progress * 100, '%');
  }
  if (event.type === 'warning') {
    console.warn('Warning:', event.data.message);
  }
});

// Execute transformation
const result = await vessel.execute('my_elixir_id', { input: myTensor });

// Get summary
console.log(vessel.getSummaryReport());
```

## Transformation Steps

### Step Types

#### 1. Custom Functions

Execute arbitrary transformations:

```typescript
{
  id: 'scale',
  name: 'Scale by Factor',
  type: 'custom',
  customFn: (tensor) => {
    return createTensor(
      'scaled',
      tensor.indices,
      tensor.shape,
      new Float64Array(tensor.data.map(x => x * 2))
    );
  },
}
```

#### 2. Activation Functions

Apply standard activation functions:

```typescript
{
  id: 'activate',
  name: 'ReLU Activation',
  type: 'activation',
  activation: 'relu',  // 'sigmoid', 'relu', 'softmax', 'threshold'
}
```

#### 3. Threshold Operations

Apply boolean thresholding:

```typescript
{
  id: 'classify',
  name: 'Binary Classification',
  type: 'threshold',
  thresholdValue: 0.5,
}
```

## Event System

### Event Types

| Event | Data | Description |
|-------|------|-------------|
| `state_change` | `{ state: ReactorState }` | Reactor state changed |
| `progress` | `{ progress: number, currentStep?: string }` | Execution progress (0-1) |
| `warning` | `{ message: string }` | Warning message |
| `step_complete` | `{ step: string, shape: number[] }` | Step completed |
| `complete` | `{ result: TransmutationResult, resources: ResourceMetrics }` | Execution complete |
| `error` | `{ message: string, error: Error }` | Error occurred |

### Subscribing to Events

```typescript
const unsubscribe = vessel.on((event) => {
  switch (event.type) {
    case 'state_change':
      updateUI(event.data.state);
      break;
    case 'progress':
      progressBar.value = event.data.progress;
      break;
    case 'warning':
      showWarning(event.data.message);
      break;
    case 'complete':
      displayResult(event.data.result);
      break;
  }
});

// Later: unsubscribe when no longer needed
unsubscribe();
```

## Pre-built Elixirs

### Logic Programming Elixir

```typescript
const rules = createTensor('rules', ['x', 'y'], [3, 3], myData);
const logicElixir = AlchemistEngine.createLogicElixir(rules);
engine.registerElixir(logicElixir);

const result = engine.transmute('logic_elixir', { rules });
```

### Multi-Layer Perceptron Elixir

```typescript
const mlpElixir = AlchemistEngine.createMLPElixir(
  weights1,  // First layer weights
  weights2,  // Second layer weights
  bias1,     // Optional biases
  bias2
);
engine.registerElixir(mlpElixir);
```

## Advanced Usage

### Complex Pipeline Example

```typescript
const complexPipeline = {
  id: 'ml_pipeline',
  name: 'Complete ML Pipeline',
  description: 'Full preprocessing and inference pipeline',
  steps: [
    {
      id: 'normalize',
      name: 'Normalize Inputs',
      type: 'custom',
      customFn: (tensor) => {
        // Min-max normalization
        const min = Math.min(...tensor.data);
        const max = Math.max(...tensor.data);
        const range = max - min;
        return createTensor(
          'normalized',
          tensor.indices,
          tensor.shape,
          new Float64Array(tensor.data.map(x => (x - min) / range))
        );
      },
      outputShape: [1, 4],
    },
    {
      id: 'hidden',
      name: 'Hidden Layer',
      type: 'activation',
      activation: 'relu',
    },
    {
      id: 'classify',
      name: 'Classification',
      type: 'activation',
      activation: 'softmax',
    },
    {
      id: 'threshold',
      name: 'Argmax',
      type: 'custom',
      customFn: (tensor) => {
        const maxIdx = tensor.data.indexOf(Math.max(...tensor.data));
        const result = new Float64Array(tensor.data.length).fill(0);
        result[maxIdx] = 1;
        return createTensor(
          'classified',
          tensor.indices,
          tensor.shape,
          result
        );
      },
    },
  ],
};
```

### Monitoring with UI Integration

```typescript
// Create a real-time dashboard
const dashboard = {
  state: document.getElementById('reactor-state'),
  progress: document.getElementById('progress-bar'),
  logs: document.getElementById('log-output'),
};

vessel.on((event) => {
  dashboard.logs.innerHTML += `[${event.timestamp}] ${event.type}: ${JSON.stringify(event.data)}\n`;
  
  if (event.type === 'state_change') {
    dashboard.state.textContent = event.data.state;
    dashboard.state.className = `state-${event.data.state.toLowerCase()}`;
  }
  
  if (event.type === 'progress') {
    dashboard.progress.value = event.data.progress;
  }
});
```

## Safety and Best Practices

### 1. Set Appropriate Constraints

```typescript
const vessel = new ReactorVessel(engine, {
  maxTensorSize: 1_000_000,      // Prevent memory exhaustion
  maxExecutionTimeMs: 30_000,    // Timeout protection
  maxMemoryBytes: 100_000_000,   // Memory limit
  maxSteps: 100,                 // Prevent infinite loops
});
```

### 2. Validate Inputs

```typescript
// Use expected shapes in step definitions
{
  id: 'layer1',
  name: 'First Layer',
  type: 'custom',
  inputShape: [1, 784],   // Expected input shape
  outputShape: [1, 128],  // Expected output shape
  customFn: transformFunction,
}
```

### 3. Handle Errors Gracefully

```typescript
try {
  const result = await vessel.execute('my_elixir', inputs);
  processResult(result);
} catch (error) {
  console.error('Transformation failed:', error);
  vessel.reset();  // Reset to clean state
}
```

### 4. Monitor Resource Usage

```typescript
const result = await vessel.execute('heavy_computation', inputs);
const status = vessel.getStatus();

if (status.resources.peakMemoryBytes > threshold) {
  console.warn('High memory usage detected');
}

console.log(vessel.getSummaryReport());
```

## Testing

Run the comprehensive test suite:

```bash
npm run test:alchemist
```

The test suite validates:
- ✅ Engine registration and retrieval
- ✅ Transformation pipelines
- ✅ Activation functions
- ✅ Vessel execution states
- ✅ Safety constraints enforcement
- ✅ Real-time monitoring
- ✅ History tracking
- ✅ Resource metrics

## Integration with Neural Nestor Framework

The Alchemist Engine and Reactor Vessel integrate seamlessly with the existing Neural Nestor Gauge Logic framework:

```typescript
import {
  AlchemistEngine,
  ReactorVessel,
  createNestor,
  NeuralNestorMorph,
} from './tensor-logic';

// Create nested tensor transformation
const nestedElixir = {
  id: 'nested_transform',
  name: 'Nested Tensor Transform',
  steps: [
    {
      id: 'transform_nestor',
      name: 'Transform Nestor',
      type: 'custom',
      customFn: (tensor) => {
        // Apply transformation to nested structure
        const nestor = createNestor(/* ... */);
        // Transform nestor...
        return nestor.tensor;
      },
    },
  ],
};
```

## Performance Considerations

1. **Lazy Evaluation**: Steps are executed sequentially; consider parallelization for independent operations
2. **Memory Management**: Large tensors are cloned for history; use `clearHistory()` periodically
3. **Event Overhead**: Too many event subscribers can impact performance
4. **Shape Validation**: Pre-validate shapes before execution to avoid runtime errors

## Future Enhancements

- 🔄 Parallel step execution for independent operations
- 🎯 GPU acceleration support via WebGPU
- 📊 Advanced metrics and profiling
- 🔍 Visualization tools for transformation pipelines
- 🧪 A/B testing of different elixirs
- 💾 Serialization and deserialization of elixirs
- 🌐 Distributed execution across workers

## References

- [Neural Nestor Gauge Logic](./Neural-Nestor-Gauge-Logic.md)
- [Tensor Logic Paper](./2510.12269v3.pdf)
- [RAPTL Module](../src/tensor-logic/raptl.ts)
- [Test Suite](../scripts/test-alchemist.ts)
