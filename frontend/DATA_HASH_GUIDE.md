# Data Hash Guide for Task Publisher Dashboard

## What is a Data Hash?

The **Data Hash** field in the Task Publisher Dashboard accepts a **string identifier** that represents the task data. This is a flexible field that can store various types of identifiers.

## Accepted Formats

### 1. **IPFS Hash** (Recommended)
IPFS (InterPlanetary File System) hashes are commonly used for decentralized storage:
```
QmHash123
QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG
QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco
```

### 2. **Dataset Hash**
A hash identifier for your dataset:
```
dataset_chest_xray_v1
hash_abc123def456
```

### 3. **Model Hash**
A hash identifier for a machine learning model:
```
model_resnet50_v2
hash_model_xyz789
```

### 4. **Custom Identifier**
Any string identifier up to 256 characters:
```
task_001
my_custom_task_identifier
```

## Technical Specifications

- **Type:** String
- **Maximum Length:** 256 characters
- **Format:** Any alphanumeric string
- **Required:** Yes (cannot be empty)

## Use Cases in HealChain

In the context of HealChain's federated learning system, the data hash typically represents:

1. **Dataset Identifier**: Hash of the training dataset
2. **Model Identifier**: Hash of the model architecture or weights
3. **Task Metadata**: Hash of task configuration or parameters
4. **IPFS Content Hash**: Hash of data stored on IPFS

## Example Values

### For Testing:
```
test_hash_001
QmHash123
dataset_v1
```

### For Production:
```
QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG
ipfs://QmHash...
0x1234567890abcdef...
```

## Integration with Event Listener

When you publish a task, the Python event listener (`listener.py`) will:
1. Detect the `TaskPublished` event
2. Extract the `dataHash` from the event
3. Use it to trigger your HealChain processing algorithms

The data hash you provide will be:
- Stored on-chain in the TaskManager contract
- Emitted in the `TaskPublished` event
- Available for your backend systems to process

## Best Practices

1. **Use IPFS hashes** for decentralized storage
2. **Keep it descriptive** but concise
3. **Use consistent format** across your tasks
4. **Document your hash format** for your team

## Notes

- The hash is stored as a **string** on-chain (not a bytes32)
- It's primarily for **identification and reference**
- The actual data processing happens **off-chain** in your Python backend
- The event listener will receive this hash and can use it to fetch/process the actual data

