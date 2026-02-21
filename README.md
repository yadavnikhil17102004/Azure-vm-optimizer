# ⚡ AZURE VM OPTIMIZER

> [!IMPORTANT]
> **Tactical Azure VM Deployment.** Bypass portal UI lag and CLI token bloat. Find the coldest prices, deploy with Service Principals, and ship faster.

Built for the **Intel MacBook Pro 15,1** (x86_64) metal, targeting **Azure Central India** and beyond. Secure by penetration testing; efficient by design.

---

## 🛠️ THE ARSENAL

### 1. `builddb.py` - The Intelligence Gatherer

Scrapes the **Azure Retail Prices API** in parallel.

- **Speed**: 100x faster than standard `az` CLI calls.
- **Payload**: Generates `data/vms.json` with real-time pricing and specs.
- **Bypass**: Ignores regional restrictions and unavailable SKUs automatically.

### 2. `searchvm.sh` - The Filter

Local `jq`-powered search. Zero-latency filtering for when you need a node _now_.

```bash
./scripts/searchvm.sh 0.15  # Find everything under $0.15/hr
```

### 3. `deploy_sp.py` - The Payload

ARM template deployment via **Service Principal**.

- **The Problem**: Azure Portal/CLI tokens get "too large" due to group bloat.
- **The Solution**: Clean SP authentication. It just works.
- **Automation**: Polls for public IP and outputs the direct SSH command.

### 4. `resize_disk.py` - System Expansion

Automated deallocation, OS disk resizing (e.g., to 64GB for LLMs), and rebooting.

---

## 🚀 MISSION START

### 1. Scrape the Prices

```bash
python3 scripts/builddb.py
```

### 2. Search for Value

```bash
./scripts/searchvm.sh 0.12
```

### 3. Deploy (Service Principal or User Auth)

Set your environment variables before running deployment scripts:

- `ARM_SUBSCRIPTION_ID`: Your Azure Subscription ID.
- `ARM_TENANT_ID`: Your Azure Tenant ID.
- `ARM_CLIENT_ID`: (SP only) Your App/Client ID.
- `ARM_CLIENT_SECRET`: (SP only) Your Client Secret.

```bash
# Example for deploy_sp.py
export ARM_SUBSCRIPTION_ID="your-sub-id"
export ARM_TENANT_ID="your-tenant-id"
export ARM_CLIENT_ID="your-client-id"
export ARM_CLIENT_SECRET="your-client-secret"
python3 scripts/deployment/deploy_sp.py
```

```bash
# Example for deploy_vm.sh (User Auth)
export ARM_SUBSCRIPTION_ID="your-sub-id"
export ARM_TENANT_ID="your-tenant-id"
./scripts/deployment/deploy_vm.sh
```

---

## 🔐 SECURITY & OPS

- **SSH**: Keys are stored in `keys/` (gitignored). Root-level `ollama_key` is also blocked.
- **Persistence**: `VM_SESSION_MEMORY.md` tracks our mission log locally.
- **Cleanliness**: `.gitignore` is hardened for security pros. No leaks.

## 📊 BENCHMARKS

Check `docs/COMPREHENSIVE_TPS_BENCHMARK.md` for raw Ollama performance metrics on the **D4as_v5** architecture.

---

**Status:** `MISSION_READY`  
**Identity:** Nikhil Yadav (Cybersecurity & Full-Stack)  
**License:** MIT
