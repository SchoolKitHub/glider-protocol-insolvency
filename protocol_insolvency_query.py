"""
Protocol Insolvency Detection Query for DeFi Contracts.

This module implements a Glider query to detect protocol insolvency
vulnerabilities in smart contracts, particularly in DeFi protocols like
ERC4626 vaults and lending pools.

@title: Protocol Insolvency via Unchecked Withdrawals/Mints (ERC4626 & Lending Pools)
@description: Detects DeFi functions allowing over-withdrawal or under-backed
    minting, leading to insolvency. Filters for public/external functions
    without reserve checks. Identifies unchecked transfer/burn calls in
    withdrawal/deposit/mint patterns that could drain protocol reserves
    without verifying sufficient assets back the liabilities.
@author: Hackerdemy Team
@tags: insolvency, DeFi, ERC4626, access-control, missing-checks, vault, lending
@references:
    - https://eips.ethereum.org/EIPS/eip-4626 (ERC4626)
    - https://swcregistry.io/docs/SWC-128/ (DoS with Failed Call)
    - OWASP Smart Contract Top 10: SC05 - Known Vulnerabilities
    - https://github.com/yearn/yearn-vaults
"""

from glider import *


def query():
    """
    Main query function to detect protocol insolvency vulnerabilities.

    This function orchestrates the vulnerability detection process through
    four main steps:
    1. Identifies candidate withdrawal/mint/redeem functions
    2. Finds transfer/burn instructions (vulnerable outflows)
    3. Filters for missing reserve checks
    4. Eliminates false positives

    Returns:
        APIList: List of vulnerable Instructions representing potential
            protocol insolvency issues in smart contracts.

    Note:
        The query uses backward dataflow analysis to identify missing
        reserve checks and applies multiple filters to ensure high
        precision with minimal false positives.
    """
    # Step 1: Identify candidate withdrawal/mint/redeem functions
    # ============================================================
    # Target public/external functions with common DeFi withdrawal/deposit
    # names that could lead to protocol insolvency.
    candidate_functions = (
        Functions()
        .with_one_property([MethodProp.PUBLIC, MethodProp.EXTERNAL])
        .without_properties([MethodProp.IS_PURE, MethodProp.IS_VIEW])
        .without_modifier_names(
            ['onlyOwner', 'nonReentrant', 'whenNotPaused', 'lock']
        )
        .with_one_of_the_names([
            'withdraw', 'redeem', 'burn', 'transferFrom', 'safeWithdraw',
            'exitMarket', 'borrow', 'redeemShares', 'unstake', 'claim',
            'liquidate', 'seize', 'exit', 'removeLiquidity'
        ])
        .with_arg_type('uint256')
        .exec(500)
    )

    # Step 2: Level down to instructions and identify vulnerable outflows
    # ===================================================================
    # Extract all instructions and filter for transfer/burn calls that
    # represent asset outflows from the protocol.
    transfer_and_burn_instructions = (
        candidate_functions
        .instructions()
        .exec(1000)
        .filter(lambda ins: any(
            callee in ins.callee_names()
            for callee in [
                'transfer', 'burn', 'transferFrom', 'safeTransferFrom',
                '_burn'
            ]
        ))
    )

    # Step 3: Core vulnerability detection - missing reserve checks
    # =============================================================
    # Filter for instructions that lack reserve validation and have
    # user-controlled amount parameters.
    vulnerable_instructions = transfer_and_burn_instructions.filter(
        lambda ins: (
            lacks_reserve_check(ins) and
            has_global_df_in_amount(ins)
        )
    )

    # Step 4: Eliminate false positives through secondary filters
    # ===========================================================
    # Apply additional checks to reduce false positives:
    # - Exclude safe wrapper functions
    # - Exclude transfers with return value guards
    # - Exclude trivial zero-amount transfers
    results = vulnerable_instructions.filter(lambda ins: (
        not is_protected_by_safe_wrapper(ins) and
        not has_post_transfer_revert_guard(ins) and
        not is_amount_constant_zero(ins)
    ))

    return results


def lacks_reserve_check(instruction):
    """
    Check if transfer/burn instruction lacks prior reserve validation.

    Analyzes backward dataflow to determine if the amount being transferred
    is validated against available reserves before the transfer occurs.
    Specifically looks for balanceOf(address(this)) patterns.

    Args:
        instruction: A Glider Instruction object representing a transfer/burn
            operation.

    Returns:
        bool: True if the instruction lacks a reserve check (vulnerable),
            False if evidence of reserve checking is found.

    Note:
        Defaults to True (vulnerable) if dataflow analysis cannot be
        performed, following the principle of caution.
    """
    try:
        # Extract the transfer call arguments to identify the amount parameter.
        transfer_args = instruction.get_args()

        # No arguments means trivial transfer - return safe.
        if len(transfer_args) == 0:
            return False

        # The amount parameter is typically the last argument in transfer calls.
        amount_arg = transfer_args[-1]

        # Perform backward dataflow analysis to trace the origin of the amount.
        # This helps identify if the amount is validated against reserves.
        backward_flow = amount_arg.backward_df()

        # Define reserve-checking patterns that indicate safe operations.
        # These patterns indicate the contract is validating available balance.
        reserve_check_patterns = [
            'balanceOf',        # ERC20 balance check
            'getBalance',       # Custom balance getter
            'available',        # Available funds check
            'liquidity',        # Available liquidity check
            'reserves',         # Protocol reserves check
            'totalAssets',      # ERC4626 vault assets check
            'getReserves'       # Reserve getter function
        ]

        # Iterate through dataflow points to identify reserve checks.
        for df_point in backward_flow:
            try:
                # Get the source code representation in lowercase for pattern
                # matching.
                source = df_point.source_code().lower()

                # Check if any reserve pattern appears in the dataflow source.
                if any(
                    pattern.lower() in source
                    for pattern in reserve_check_patterns
                ):
                    # Found a reserve pattern - verify it checks the
                    # contract's own balance (address(this)).
                    if (
                        'address(this)' in df_point.source_code() or
                        'this' in df_point.source_code()
                    ):
                        # Reserve check for contract's balance found -
                        # function is safe.
                        return False

            except Exception:
                # Skip individual dataflow points that cause errors.
                pass

        # No reserve check found in dataflow - vulnerable.
        return True

    except Exception:
        # If dataflow analysis fails, err on the side of caution.
        # Mark as vulnerable to avoid missing real issues.
        return True


def has_global_df_in_amount(instruction):
    """
    Verify that amount is influenced by user-controlled inputs.

    This filter ensures we only flag real vulnerabilities where the amount
    is user-controlled. Constant amounts that an attacker cannot influence
    are not exploitable.

    Args:
        instruction: A Glider Instruction object representing a transfer/burn
            operation.

    Returns:
        bool: True if the amount has global dataflow (user-controlled),
            False if the amount is derived solely from constants.

    Note:
        Defaults to True if dataflow cannot be determined, following the
        principle of caution.
    """
    try:
        # Extract transfer call arguments to identify the amount.
        transfer_args = instruction.get_args()

        # Empty arguments list means safe - no amount to control.
        if len(transfer_args) == 0:
            return False

        # Get the last argument, which is typically the transfer amount.
        amount_arg = transfer_args[-1]

        # Check if the amount argument has global dataflow (receives input
        # from external sources/user input). If it does, the amount is
        # user-controlled and exploitable.
        if hasattr(amount_arg, 'has_global_df'):
            # The instruction object has the dataflow analysis method.
            return amount_arg.has_global_df()
        else:
            # If we cannot determine, assume user-controlled for safety.
            return True

    except Exception:
        # If analysis fails, assume user-controlled for safety.
        return True


def is_protected_by_safe_wrapper(instruction):
    """
    Identify if instruction is in a safe wrapper function.

    Safe wrapper functions (safeTransfer, safeWithdraw, etc.) are designed
    with built-in safety checks and do not represent real vulnerabilities.

    Args:
        instruction: A Glider Instruction object.

    Returns:
        bool: True if the instruction is within a safe wrapper function,
            False otherwise.

    Note:
        Reduces false positives by excluding functions that implement
        safety patterns in their names.
    """
    try:
        # Get the parent function containing this instruction.
        parent_function = instruction.get_parent()

        # No parent means instruction is at module level (shouldn't happen).
        if parent_function is None:
            return False

        # Extract function name and convert to lowercase for case-insensitive
        # matching.
        func_name = parent_function.name.lower()

        # Patterns that indicate a function is a safe wrapper.
        # Functions with these patterns in their names implement safety
        # checks internally.
        safe_patterns = [
            'safetransfer',     # Safe transfer wrapper
            'safewithdraw',     # Safe withdrawal wrapper
            'safemint',         # Safe minting wrapper
            'safeburn'          # Safe burning wrapper
        ]

        # Check if any safe pattern appears in the function name.
        return any(pattern in func_name for pattern in safe_patterns)

    except Exception:
        # If we cannot determine the function name, don't exclude it.
        return False


def has_post_transfer_revert_guard(instruction):
    """
    Check if transfer has subsequent return value validation.

    Transfers protected by return value checks (require(success)) are
    safe because they revert on failure, preventing silent failures.

    Args:
        instruction: A Glider Instruction object representing a transfer.

    Returns:
        bool: True if the transfer is protected by a revert guard,
            False otherwise.

    Note:
        Returns true only if a require/assert statement in the next
        instruction checks the 'success' or 'ok' return value.
    """
    try:
        # Retrieve the instructions that follow this one in execution order.
        next_instructions = instruction.next_instructions()

        # Iterate through subsequent instructions to find guards.
        for next_instr in next_instructions:
            # Check if the next instruction is a require or assert call.
            instr_callees = next_instr.callee_names()
            if (
                'require' in instr_callees or
                'assert' in instr_callees
            ):
                # Found a potential guard - verify it checks return value.
                try:
                    # Get the source code of the guard statement.
                    source = next_instr.source_code()

                    # Check if the guard validates the success/ok flag,
                    # which would be the return value from the transfer.
                    if (
                        'success' in source.lower() or
                        'ok' in source.lower()
                    ):
                        # Guard found that checks return value - transfer
                        # is protected.
                        return True

                except Exception:
                    # Skip if we cannot analyze this instruction.
                    pass

        # No return value guard found - transfer is unprotected.
        return False

    except Exception:
        # If we cannot retrieve next instructions, assume unprotected.
        return False


def is_amount_constant_zero(instruction):
    """
    Exclude transfers of constant zero amount.

    Transfers of zero amount are not real vulnerabilities since they
    cannot drain the protocol.

    Args:
        instruction: A Glider Instruction object representing a transfer.

    Returns:
        bool: True if the transfer amount is constant zero (or type max),
            False otherwise.

    Note:
        Also excludes type(uint256).max transfers which are special cases.
    """
    try:
        # Extract transfer call arguments to identify the amount.
        transfer_args = instruction.get_args()

        # No arguments means no amount to validate - mark as not-zero.
        if len(transfer_args) == 0:
            return False

        # Get the last argument, typically the transfer amount.
        amount_arg = transfer_args[-1]

        # Retrieve the source code representation of the amount.
        source = amount_arg.source_code()

        # Check if the amount is the literal constant zero.
        # Also exclude type(uint256).max which is a special pattern.
        if source.strip() == '0' or 'uint256).max' in source:
            # Amount is constant - not a real vulnerability.
            return True

        # Amount is not a constant - may be vulnerable.
        return False

    except Exception:
        # If we cannot determine the amount value, don't exclude it.
        return False
