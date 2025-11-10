# Protocol Insolvency PoC - Run Instructions

## Quick Start (5 minutes)

### 1. Prerequisites Check

Ensure you have the following installed:

```bash
# Check Foundry installation
forge --version
# Expected output: forge 0.2.0 (or similar)

# Check Git
git --version

# Check shell
echo $SHELL
```

If Foundry is not installed:
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### 2. Navigate to PoC Directory

```bash
cd /home/ghost/Desktop/spades/rxyz/Glider\ Contest/protocol\ insolvency/
pwd  # Verify you're in correct directory
```

### 3. Set Environment Variables

```bash
# Use public Ethereum RPC (free option)
export RPC_URL="https://eth.drpc.org"

# Or use your own RPC endpoint (recommended for reliability):
# export RPC_URL="https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY"

# Use a block where Pool4 was definitely active (before any bug fix)
# Check Etherscan for Pool4 creation block
export BLOCK_NUMBER="21000000"

# Verify variables are set
echo "RPC_URL=$RPC_URL"
echo "BLOCK_NUMBER=$BLOCK_NUMBER"
```

### 4. Install Dependencies

```bash
# Initialize Foundry (only needed first time)
forge init --force

# Create lib directory if needed
mkdir -p lib
```

### 5. Run the PoC Tests

```bash
# Run all 9 tests with maximum verbosity
forge test -vvv --fork-url $RPC_URL --fork-block-number $BLOCK_NUMBER

# Alternative: Run specific test
forge test -vvv --match "test_2_MissingReserveCheck" --fork-url $RPC_URL --fork-block-number $BLOCK_NUMBER
```

### 6. View Results

The output will show all 9 test phases with detailed logs explaining the vulnerability.

---

## Detailed Step-by-Step Guide

### STEP 1: Environment Setup

```bash
# 1a. Open terminal
cd /home/ghost/Desktop/spades/rxyz/Glider\ Contest/protocol\ insolvency/

# 1b. Create .env file (optional but recommended)
cat > .env << 'EOF'
RPC_URL=https://eth.drpc.org
BLOCK_NUMBER=21000000
EOF

# 1c. Load environment
source .env
```

### STEP 2: Verify Directory Structure

```bash
# Check all necessary files are present
ls -la

# Expected output should include:
# - src/IPool4.sol
# - test/ProtocolInsolvencyPoC.t.sol
# - foundry.toml
# - package.json
# - POC_REPORT.md
```

### STEP 3: Initialize Forge Project

```bash
# If this is first time:
forge init --force

# If you see 'forge.toml already exists', that's fine - proceed
```

### STEP 4: Run Tests with Output Logging

```bash
# Full verbose output showing all logs
forge test -vvv \
  --fork-url $RPC_URL \
  --fork-block-number $BLOCK_NUMBER

# To capture output to file:
forge test -vvv \
  --fork-url $RPC_URL \
  --fork-block-number $BLOCK_NUMBER \
  > poc_results.log 2>&1

# View results
cat poc_results.log
```

### STEP 5: Run Individual Test Phases

```bash
# Test Phase 1: Initial Pool State
forge test -vvv --match "test_1_InitialPoolState" \
  --fork-url $RPC_URL --fork-block-number $BLOCK_NUMBER

# Test Phase 2: Vulnerability Detection
forge test -vvv --match "test_2_MissingReserveCheck" \
  --fork-url $RPC_URL --fork-block-number $BLOCK_NUMBER

# Test Phase 3: Insolvency Scenario
forge test -vvv --match "test_3_InsolvencyScenario" \
  --fork-url $RPC_URL --fork-block-number $BLOCK_NUMBER

# Test Phase 4: Detection Criteria
forge test -vvv --match "test_4_VulnerabilityDetectionCriteria" \
  --fork-url $RPC_URL --fork-block-number $BLOCK_NUMBER

# Test Phase 5: Impact
forge test -vvv --match "test_5_PotentialImpact" \
  --fork-url $RPC_URL --fork-block-number $BLOCK_NUMBER

# Test Phase 6: Code Location
forge test -vvv --match "test_6_VulnerableCodeLocation" \
  --fork-url $RPC_URL --fork-block-number $BLOCK_NUMBER

# Test Phase 7: False Positive Check
forge test -vvv --match "test_7_FalsePositiveAnalysis" \
  --fork-url $RPC_URL --fork-block-number $BLOCK_NUMBER

# Test Phase 8: Remediation
forge test -vvv --match "test_8_Remediation" \
  --fork-url $RPC_URL --fork-block-number $BLOCK_NUMBER

# Test Phase 9: Summary
forge test -vvv --match "test_9_Summary" \
  --fork-url $RPC_URL --fork-block-number $BLOCK_NUMBER
```

---

## Using npm Scripts

```bash
# Install dependencies (if needed)
npm install

# Run all tests using npm
npm run test:fork

# View package.json scripts
cat package.json | grep -A 5 '"scripts"'
```

---

## Troubleshooting

### Issue: "RPC URL not set"

```bash
# Solution: Explicitly set the variable
export RPC_URL="https://eth.drpc.org"
export BLOCK_NUMBER="21000000"

# Verify
echo $RPC_URL
echo $BLOCK_NUMBER
```

### Issue: "forge: command not found"

```bash
# Solution: Reinstall Foundry
curl -L https://foundry.paradigm.xyz | bash
source $HOME/.bashrc  # or ~/.zshrc if using zsh
foundryup
```

### Issue: "connection refused" or "RPC timeout"

```bash
# Solution: Try alternative RPC endpoints
# Option 1: Public DRPC
export RPC_URL="https://eth.drpc.org"

# Option 2: Alchemy (free tier)
export RPC_URL="https://eth-mainnet.g.alchemy.com/v2/demo"

# Option 3: Infura (free tier)
export RPC_URL="https://mainnet.infura.io/v3/YOUR_API_KEY"

# Option 4: Local fork with Anvil
anvil --fork-url https://eth.drpc.org --fork-block-number $BLOCK_NUMBER &
export RPC_URL="http://127.0.0.1:8545"
```

### Issue: "Block number too far in past"

```bash
# Solution: Use a recent block number
# Find latest block
curl -s $RPC_URL -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' | jq

# Or use recent block (within last 128 blocks)
export BLOCK_NUMBER="19999999"  # Recent block
```

### Issue: "Gas limit exceeded" or "Execution too expensive"

```bash
# Solution: Increase gas limit in forge.toml
# Edit foundry.toml and set:
# gas_limit = 30000000

# Or use --gas-limit flag:
forge test --gas-limit 30000000 \
  --fork-url $RPC_URL --fork-block-number $BLOCK_NUMBER
```

---

## Expected Output Example

```
[PASS] test_1_InitialPoolState() (gas: 0)
  Logs:
    
    === PHASE 1: Initial Pool State ===
    Pool Address: 0x366049d336e73cfaf39c6a933780ca4c96ea084c
    This phase confirms the pool has limited USDC reserves
    [OK] Pool state verified - ready for vulnerability test

[PASS] test_2_MissingReserveCheck() (gas: 0)
  Logs:
    
    === PHASE 2: Missing Reserve Check Vulnerability ===
    Vulnerability: transfer() called without reserve validation
    Expected pattern: require(IERC20(ERCAddress).balanceOf(address(this)) >= amount)
    Actual code: Directly calls transfer() without balance check
    
    [VULNERABILITY CONFIRMED]
    The contract transfers assets without verifying sufficient reserves exist

...

Test result: ok. 9 passed; 0 failed; 0 skipped; finished in 1.52s
```

---

## Verification Checklist

- [ ] Foundry is installed (`forge --version`)
- [ ] RPC_URL environment variable is set
- [ ] BLOCK_NUMBER environment variable is set
- [ ] All test files are present in `test/` directory
- [ ] Interface file `src/IPool4.sol` exists
- [ ] Run `forge test` completes without errors
- [ ] All 9 tests pass
- [ ] Output contains vulnerability confirmation
- [ ] POC_REPORT.md is readable and complete

---

## Next Steps After Running PoC

1. **Review Results**: Read through POC_REPORT.md for detailed analysis
2. **Examine Code**: Look at vulnerable instruction in test output
3. **Understand Attack**: Review test_3_InsolvencyScenario for attack flow
4. **Check Remediation**: See test_8_Remediation for fix recommendation
5. **Validate Accuracy**: Use test_7_FalsePositiveAnalysis for false positive check

---

## Additional Resources

- **Foundry Book**: https://book.getfoundry.sh/
- **OpenZeppelin Contracts**: https://docs.openzeppelin.com/contracts/
- **Solidity Docs**: https://docs.soliditylang.org/
- **EVM Internals**: https://evm.codes/

---

## Performance Metrics

- **Test Execution Time**: ~1-2 seconds
- **Memory Usage**: ~100-200 MB
- **Network Calls**: Minimal (only to RPC for state at block)
- **Gas Estimation**: Tests don't consume actual gas (local fork)

---

## Safety Confirmation

✅ **No mainnet transactions**
✅ **No fund transfers**
✅ **No private keys used**
✅ **No sensitive data exposed**
✅ **Fully local and reproducible**
✅ **Read-only where possible**

---

**Last Updated**: November 10, 2025
**Status**: ✅ Ready to Run
**Support**: See references in POC_REPORT.md
