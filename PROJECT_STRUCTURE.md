# Azure VM Deployment Project Structure

```
azure-vm-find/
│
├── README.md                          # Main project documentation
│
├── scripts/                           # All executable scripts
│   ├── builddb.py                     # VM pricing database builder
│   ├── searchvm.sh                    # VM search tool
│   ├── findvm.sh                      # VM finder utility
│   ├── check_deps.sh                  # Dependency checker
│   │
│   ├── deployment/                    # Deployment scripts
│   │   ├── deploy_sp.py              # Service Principal deployment (RECOMMENDED)
│   │   ├── deploy_arm.py             # ARM template deployment (legacy)
│   │   ├── deploy_vm.sh              # Shell deployment script (legacy)
│   │   └── cloud_deploy.sh           # Azure Cloud Shell script
│   │
│   ├── benchmarks/                    # Model benchmarking
│   │   ├── benchmark_models.sh       # Quick benchmark script
│   │   └── comprehensive_benchmark.sh # Full TPS analysis
│   │
│   └── debug/                         # Debugging utilities
│       ├── check_deployment.py       # Deployment status checker
│       ├── check_ops.py              # Operation details viewer
│       ├── check_nsg.py              # NSG rules validator
│       └── verify_vm.py              # VM existence verifier
│
├── templates/                         # ARM Templates
│   └── deploy.json                   # VM deployment template (corrected)
│
├── keys/                              # SSH Keys (KEEP PRIVATE)
│   ├── ollama_key                    # Private SSH key
│   └── ollama_key.pub                # Public SSH key
│
├── data/                              # Data files
│   └── vms.json                      # VM pricing database (~21 MB)
│
├── docs/                              # Documentation
│   ├── gemini.md                     # Session journey & technical insights
│   ├── BENCHMARK_RESULTS.md          # Initial benchmark results
│   └── COMPREHENSIVE_TPS_BENCHMARK.md # Full TPS analysis & model comparison
│
└── logs/                              # Debug logs (auto-generated)
    ├── deployment_error.log
    ├── deployment_debug.log
    ├── deployment_result.json
    └── vm_create_output.json
```

## 🎯 Quick Start

### 1. Find VM Prices

```bash
# Build database
python3 scripts/builddb.py

# Search for VMs under $0.15/hr
./scripts/searchvm.sh 0.15
```

### 2. Deploy VM

```bash
# Using Service Principal (RECOMMENDED)
python3 scripts/deployment/deploy_sp.py <CLIENT_ID> <CLIENT_SECRET>
```

### 3. Connect to VM

```bash
ssh -i keys/ollama_key azureuser@<YOUR_PUBLIC_IP>
```

## 📁 Directory Purposes

### `/scripts`

All executable scripts organized by function:

- **Root**: Core utilities (builddb, searchvm)
- **deployment/**: VM deployment methods
- **benchmarks/**: Ollama model testing
- **debug/**: Troubleshooting tools

### `/templates`

ARM templates for Azure resources

### `/keys`

**SENSITIVE** - SSH keys for VM access
⚠️ Never commit to Git!

### `/data`

Database files and cached data

### `/docs`

Project documentation and analysis

### `/logs`

Auto-generated debug logs

## 🔐 Security

**Protected Files:**

- `keys/ollama_key` - Private SSH key
- Service Principal credentials (never stored)

**Add to `.gitignore`:**

```
keys/
*.key
*.pem
logs/
*.log
```

## 📊 File Sizes

- `data/vms.json`: ~21 MB (VM pricing database)
- `keys/ollama_key`: 3.4 KB (SSH private key)
- `templates/deploy.json`: 6.6 KB (ARM template)

## 🚀 Deployment Status

**Current VM:**

- IP: `<YOUR_PUBLIC_IP>`
- Size: Standard_D4as_v5 (4 vCPU, 16 GB RAM)
- Region: Central India
- Ollama: Running with llama3.1:8b

**Connect:**

```bash
ssh -i keys/ollama_key azureuser@<YOUR_PUBLIC_IP>
```
