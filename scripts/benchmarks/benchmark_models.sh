#!/bin/bash
# Ollama Model Benchmark Script
# Tests different models to find optimal performance on VM

echo "==================================================="
echo "Ollama Model Benchmark - Standard_D4as_v5"
echo "Hardware: 4 vCPU, 16 GB RAM (CPU-only mode)"
echo "==================================================="
echo ""

# Test prompt (consistent across models)
PROMPT="Explain quantum computing in one sentence."

# Models to test (ordered by size)
MODELS=(
    "llama3.2:3b"
    "qwen2.5:7b"
    "llama3.1:8b"
    "gemma2:9b"
    "llama3.1:13b"
    "mistral:7b"
)

echo "Available models to test:"
for model in "${MODELS[@]}"; do
    echo "  - $model"
done
echo ""

# Function to benchmark a model
benchmark_model() {
    local model=$1
    echo "=========================================="
    echo "Testing: $model"
    echo "=========================================="
    
    # Pull the model if not present
    echo "Pulling $model..."
    if ollama pull "$model" 2>&1 | grep -q "Error"; then
        echo "❌ Failed to pull $model"
        return 1
    fi
    
    # Get model info
    echo ""
    echo "Model Info:"
    ollama show "$model" 2>/dev/null | head -20
    
    echo ""
    echo "Running inference test..."
    echo "Prompt: '$PROMPT'"
    echo ""
    
    # Run inference and capture output
    start_time=$(date +%s.%N)
    response=$(echo "$PROMPT" | ollama run "$model" 2>&1)
    end_time=$(date +%s.%N)
    
    # Calculate time
    duration=$(echo "$end_time - $start_time" | bc)
    
    echo "Response: $response"
    echo ""
    echo "⏱️  Time taken: ${duration}s"
    
    # Check memory usage
    echo ""
    echo "Memory usage after inference:"
    free -h | grep Mem
    
    echo ""
    echo "=========================================="
    echo ""
}

# Test each model
for model in "${MODELS[@]}"; do
    benchmark_model "$model"
    
    # Wait between tests to let memory clear
    sleep 3
done

echo "==================================================="
echo "Benchmark Complete!"
echo "==================================================="
