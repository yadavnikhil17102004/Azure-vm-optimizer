#!/bin/bash
# Comprehensive Ollama Benchmark with TPS Measurement
# Tests models mentioned in the comparison guide

echo "==========================================================="
echo "Ollama Model Benchmark - Comprehensive TPS Analysis"
echo "Hardware: Standard_D4as_v5 (4 vCPU, 16 GB RAM, CPU-only)"
echo "==========================================================="
echo ""

# Test prompt (standardized for fair comparison)
PROMPT="Write a detailed explanation of how neural networks learn through backpropagation. Include the key concepts and mathematical intuition."

# Models to test (available in Ollama, ~7B range for 16GB RAM)
MODELS=(
    "llama2:7b"           # LLaMA 2 (older, from the list)
    "llama3.1:8b"         # LLaMA 3.1 (current best)
    "mistral:7b"          # Mistral (from the list)
    "phi3:3.8b"           # Microsoft Phi-3 (efficient)
    "gemma2:9b"           # Google Gemma 2 (latest)
    "qwen2.5:7b"          # Qwen 2.5 (Chinese tech, strong)
)

echo "Models to benchmark:"
for model in "${MODELS[@]}"; do
    echo "  - $model"
done
echo ""
echo "Test prompt ($(echo "$PROMPT" | wc -w) words):"
echo "\"$PROMPT\""
echo ""

# Function to count tokens (approximate: words * 1.3)
count_tokens() {
    local text="$1"
    local words=$(echo "$text" | wc -w)
    echo $(echo "$words * 1.3" | bc | cut -d. -f1)
}

# Function to benchmark a model
benchmark_model() {
    local model=$1
    echo "==========================================================="
    echo "📊 TESTING: $model"
    echo "==========================================================="
    
    # Pull the model
    echo "⬇️  Pulling $model..."
    if ! ollama pull "$model" 2>&1 | tail -5; then
        echo "❌ Failed to pull $model"
        echo ""
        return 1
    fi
    
    echo ""
    echo "📝 Model Information:"
    ollama show "$model" 2>/dev/null | head -15
    
    echo ""
    echo "🧠 Memory BEFORE inference:"
    free -h | grep "Mem:"
    
    echo ""
    echo "🚀 Running inference..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Run inference and capture output
    start_time=$(date +%s.%N)
    response=$(echo "$PROMPT" | ollama run "$model" 2>&1)
    end_time=$(date +%s.%N)
    
    # Calculate metrics
    duration=$(echo "$end_time - $start_time" | bc)
    response_length=$(echo "$response" | wc -w)
    response_tokens=$(count_tokens "$response")
    tokens_per_sec=$(echo "scale=2; $response_tokens / $duration" | bc)
    
    echo "$response"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo ""
    echo "📈 PERFORMANCE METRICS:"
    echo "  ⏱️  Time:           ${duration}s"
    echo "  📝 Words:           $response_length"
    echo "  🎯 Tokens (est):    $response_tokens"
    echo "  ⚡ Tokens/sec:      $tokens_per_sec"
    
    echo ""
    echo "🧠 Memory AFTER inference:"
    free -h | grep "Mem:"
    
    echo ""
    echo "💾 Disk usage:"
    ollama list | grep "$model"
    
    echo ""
    echo "==========================================================="
    echo ""
    
    # Save results to CSV
    echo "$model,$duration,$response_length,$response_tokens,$tokens_per_sec" >> benchmark_results.csv
    
    # Wait between tests
    sleep 5
}

# Initialize results file
echo "model,time_sec,words,tokens,tokens_per_sec" > benchmark_results.csv

# Run benchmarks
for model in "${MODELS[@]}"; do
    benchmark_model "$model"
done

echo ""
echo "==========================================================="
echo "✅ BENCHMARK COMPLETE!"
echo "==========================================================="
echo ""
echo "📊 Results Summary:"
echo ""
cat benchmark_results.csv | column -t -s,
echo ""
echo "Full results saved to: benchmark_results.csv"
