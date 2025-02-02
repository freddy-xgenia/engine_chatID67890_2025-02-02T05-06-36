import copy


def check_and_round_number(number):
    """
    Check if the input is an integer. If it's a float, round it to the nearest integer.
    Args:
        number: The input number (int or float)
    Returns:
        int: The integer result after rounding
    """
    if isinstance(number, float):
        rounded_number = round(number)
        return rounded_number
    return number


def check_results(result: dict):
    """
    Validates and rounds total_winnings, payouts in the winning lines, and total_payout using check_and_round_number.

    Args:
        result (dict): The result dictionary containing total_winnings and spin_results.

    Returns:
        dict: The updated result dictionary with validated and rounded values.
    """
    # Create a deep copy of the result to avoid modifying the original
    updated_result = copy.deepcopy(result)

    # Check and round total_winnings
    if "total_winnings" in updated_result:
        total_winnings = updated_result["total_winnings"]
        updated_result["total_winnings"] = check_and_round_number(total_winnings)

    # Check and round total_payout
    if "spin_results" in updated_result and "total_payout" in updated_result["spin_results"]:
        total_payout = updated_result["spin_results"]["total_payout"]
        updated_result["spin_results"]["total_payout"] = check_and_round_number(total_payout)

    # Check and round payouts in winning_lines
    if "spin_results" in updated_result and "winning_lines" in updated_result["spin_results"]:
        winning_lines = updated_result["spin_results"]["winning_lines"]
        for line in winning_lines:
            if "payout" in line:
                line["payout"] = check_and_round_number(line["payout"])

    return updated_result

